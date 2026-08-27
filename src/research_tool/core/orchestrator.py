"""Central orchestrator for the autonomous visual agent."""
import structlog
import asyncio
from typing import Any
from datetime import datetime, timezone
import ulid

from research_tool.domain import (
    RunSession, SeedSource, EventType, ActionEvent,
    WorldState, PageType, AgentStatus, CheckpointTrigger,
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
            run_id=run_id,
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
        except asyncio.CancelledError:
            logger.info("orchestrator_cancelled")
            await self.events.log(EventType.RUN_END, {"reason": "cancelled"})
            raise
        except Exception as e:
            logger.exception("orchestrator_crashed", error=str(e))
            await self.events.log(EventType.RUN_END, {"error": str(e)})
            raise
        finally:
            self.current_run.time_end = datetime.now(timezone.utc)
            self.current_run.status = RunStatus.DONE
            await self.run_repo.update_status(run_id, RunStatus.DONE)
            await self.events.log(EventType.RUN_END)

    async def _run_loop(self) -> None:
        """The core execution loop."""
        max_iters = 5  # For V1, we put a hard limit for safety during tests
        iters = 0
        
        while iters < max_iters:
            iters += 1
            
            # Check yield status
            if self.yield_tracker.current_status() == "SATURATION":
                logger.info("stopping_due_to_saturation")
                break
                
            # Pop frontier
            item = await self.frontier.pop_next()
            if not item:
                logger.info("frontier_exhausted")
                break
                
            # Get screen and state
            screenshot_bytes = await self.controller.screenshot()
            self.world_state.active_url = await self.controller.get_active_url()
            self.world_state.active_window_title = await self.controller.get_window_title()
            
            # Analyze
            query = "Evaluate current screen for relevant products or evidence."
            if item.seed_id:
                query = f"Search for seed: {item.seed_id}" # In real app, we fetch seed text
                
            vision_result = await self.vision.analyze_screen(screenshot_bytes, self.world_state, query)
            
            # (In a real implementation, we would now process vision_result.discovered_entities
            # and add them to the frontier/evidence/graph)
            
            await self.events.log(EventType.SCREENSHOT, {"page_type": vision_result.page_type.value})
            
            # Record a generic visit for tracking
            await self.visits.record_visit(
                platform="unknown",
                url=self.world_state.active_url,
                screen_fingerprint="dummy_fp"
            )
            
            # Checkpoint
            if iters % 3 == 0:
                await self.recovery.create_checkpoint(
                    world_state=self.world_state,
                    trigger=CheckpointTrigger.PERIODIC
                )
                
            await self.frontier.mark_completed(item.frontier_id)
