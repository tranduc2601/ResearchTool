"""Central orchestrator for the autonomous visual agent."""
import structlog
import asyncio
from datetime import datetime, timezone

from research_tool.domain import (
    RunSession, SeedSource, EventType,
    WorldState, PageType, CheckpointTrigger,
    RunStatus
)
from research_tool.interfaces import ComputerController, VisionProvider, OCRProvider
from research_tool.config.settings import AppSettings
from research_tool.core.event_logger import EventLogger
from research_tool.core.yield_tracker import YieldTracker
from research_tool.core.seed_manager import SeedManager
from research_tool.core.visit_manager import VisitManager
from research_tool.core.frontier_manager import FrontierManager
from research_tool.core.exploration_graph import ExplorationGraph
from research_tool.core.evidence_manager import EvidenceManager
from research_tool.core.recovery_manager import RecoveryManager
from research_tool.infrastructure.db.repositories.run_repo import RunRepo

logger = structlog.get_logger()

class HumanInterventionRequired(Exception):
    pass

class Orchestrator:
    """Main control loop."""

    def __init__(
        self,
        settings: AppSettings,
        run_repo: RunRepo,
        controller: ComputerController,
        vision_provider: VisionProvider,
        ocr_provider: OCRProvider,
        event_logger: EventLogger,
        yield_tracker: YieldTracker,
        seed_manager: SeedManager,
        visit_manager: VisitManager,
        frontier_manager: FrontierManager,
        exploration_graph: ExplorationGraph,
        evidence_manager: EvidenceManager,
        recovery_manager: RecoveryManager,
    ):
        self.settings = settings
        self.run_repo = run_repo
        self.controller = controller
        self.vision = vision_provider
        self.ocr = ocr_provider
        self.events = event_logger
        self.yield_tracker = yield_tracker
        self.seeds = seed_manager
        self.visits = visit_manager
        self.frontier = frontier_manager
        self.graph = exploration_graph
        self.evidence = evidence_manager
        self.recovery = recovery_manager

        self.current_run: RunSession | None = None
        self.world_state: WorldState | None = None

    async def start_session(self, initial_query: str, run_id: str) -> None:
        """Initialize a run and start the loop."""
        self.world_state = WorldState(run_id=run_id, platform="windows", app="browser")
        self.current_run = RunSession(
            run_id=run_id,
            goal_text=initial_query,
            status=RunStatus.RUNNING
        )
        await self.run_repo.create(self.current_run)
        
        await self.events.log(EventType.RUN_START, {"initial_query": initial_query})
        
        # Inject the first seed
        seed, _ = await self.seeds.create_seed(
            text=initial_query,
            source=SeedSource.USER
        )
        await self.frontier.add_seed(
            seed_id=seed.seed_id,
            mention_confidence=1.0,
            seed_similarity=1.0,
            source_diversity=1.0,
            novelty=1.0,
            unexplored_bonus=1.0,
            depth_penalty=0.0
        )
        await self.events.log(EventType.SEED_DISCOVERED, {"seed_id": seed.seed_id, "text": initial_query})
        
        # Start the loop
        try:
            await self._run_loop()
            self.current_run.status = RunStatus.DONE
        except HumanInterventionRequired as e:
            logger.warning("orchestrator_paused_for_human", reason=str(e))
            self.current_run.status = RunStatus.PAUSED
            await self.events.log(EventType.RUN_END, {"reason": "human_required"})
            raise
        except asyncio.CancelledError:
            logger.info("orchestrator_cancelled")
            self.current_run.status = RunStatus.PAUSED
            await self.events.log(EventType.RUN_END, {"reason": "cancelled"})
            raise
        except Exception as e:
            logger.exception("orchestrator_crashed", error=str(e))
            self.current_run.status = RunStatus.FAILED
            await self.events.log(EventType.RUN_END, {"error": str(e)})
            raise
        finally:
            self.current_run.time_end = datetime.now(timezone.utc)
            await self.run_repo.update_status(run_id, self.current_run.status)
            if self.current_run.status == RunStatus.DONE:
                await self.events.log(EventType.RUN_END)

    async def _run_loop(self) -> None:
        """The core outer exploration loop."""
        max_goals = 5  # Limit for testing
        goals_processed = 0
        
        while goals_processed < max_goals:
            goals_processed += 1
            
            # Check yield status
            if self.yield_tracker.current_status() == "SATURATION":
                logger.info("stopping_due_to_saturation")
                break
                
            # Pop frontier
            item = await self.frontier.pop_next()
            if not item:
                logger.info("frontier_exhausted")
                break
                
            # Execute inner loop to achieve goal
            success = await self._achieve_goal(item)
            
            if success:
                await self.frontier.mark_completed(item.frontier_id)
            else:
                await self.frontier.mark_failed(item.frontier_id)
                
            # Checkpoint periodically
            if goals_processed % 3 == 0:
                await self.recovery.create_checkpoint(
                    world_state=self.world_state,
                    trigger=CheckpointTrigger.PERIODIC
                )
                
    async def _achieve_goal(self, frontier_item) -> bool:
        """The inner SEE -> THINK -> ACT loop for a specific goal."""
        from research_tool.domain.action import ActionType, ActionStatus
        from research_tool.core.action_validator import ActionValidator
        
        max_actions = 10
        actions_taken = 0
        validator = ActionValidator(screen_width=1920, screen_height=1080)  # Standard bounds
        
        query = "Evaluate current screen."
        if frontier_item.seed_id:
            query = f"Search for seed: {frontier_item.seed_id}"
            
        while actions_taken < max_actions:
            actions_taken += 1
            
            # 1. SEE
            screenshot_bytes = await self.controller.screenshot()
            self.world_state.active_url = await self.controller.get_active_url()
            self.world_state.active_window_title = await self.controller.get_window_title()
            
            # 2. THINK
            vision_result = await self.vision.analyze_screen(screenshot_bytes, self.world_state, query)
            await self.events.log(EventType.SCREENSHOT, {"page_type": vision_result.page_type.value})
            
            # Record visit based on visual context
            await self.visits.record_visit(
                platform="unknown",
                url=self.world_state.active_url,
                screen_fingerprint="dummy_fp"
            )
            
            action = vision_result.next_action
            
            # 3. VALIDATE
            validation_result = validator.validate(action)
            if validation_result.status != ActionStatus.SUCCESS:
                logger.warning("invalid_action_proposed", action=action.action_type, error=validation_result.error)
                # In real scenario: feed error back to VLM in next iter
                continue
                
            # 4. EVALUATE TERMINAL STATES
            if action.action_type == ActionType.GOAL_MET:
                logger.info("goal_met", frontier_item=frontier_item.frontier_id)
                return True
            elif action.action_type == ActionType.GOAL_FAILED:
                logger.warning("goal_failed_by_vision", frontier_item=frontier_item.frontier_id)
                return False
            elif action.action_type == ActionType.HUMAN_REQUIRED:
                logger.warning("human_intervention_required")
                self.current_run.status = RunStatus.PAUSED
                raise HumanInterventionRequired("Human required")
                
            # 5. ACT
            logger.info("executing_action", type=action.action_type)
            result = None
            if action.action_type == ActionType.CLICK and action.x is not None and action.y is not None:
                result = await self.controller.click(action.x, action.y)
            elif action.action_type == ActionType.TYPE_TEXT and action.text:
                result = await self.controller.type_text(action.text)
            elif action.action_type == ActionType.SCROLL and action.x is not None and action.y is not None:
                result = await self.controller.scroll(action.x, action.y, dy=10) # Stub dy
            elif action.action_type == ActionType.PRESS_KEY and action.key:
                result = await self.controller.press_key(action.key)
            elif action.action_type == ActionType.BACK:
                result = await self.controller.back()
            elif action.action_type == ActionType.WAIT:
                await asyncio.sleep(1.0)
                continue
            
            if result and result.status == ActionStatus.FAILURE:
                logger.warning("action_failed", type=action.action_type, error=result.error)
                # In real scenario: backoff or feed error to VLM
                
        logger.warning("inner_loop_timeout", max_actions=max_actions)
        return False
