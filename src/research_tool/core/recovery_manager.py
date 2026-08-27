"""Checkpoint and recovery manager."""
import structlog
import ulid
from datetime import datetime, timezone
from research_tool.domain import CheckpointData, CheckpointTrigger, WorldState
from research_tool.infrastructure.db.repositories.checkpoint_repo import CheckpointRepo
from research_tool.core.yield_tracker import YieldTracker

logger = structlog.get_logger()

class RecoveryManager:
    """
    Handles saving and loading run state for crash recovery or pausing.
    """

    def __init__(
        self,
        run_id: str,
        checkpoint_repo: CheckpointRepo,
        yield_tracker: YieldTracker,
    ):
        self.run_id = run_id
        self._repo = checkpoint_repo
        self._yield_tracker = yield_tracker

    async def create_checkpoint(
        self,
        world_state: WorldState,
        trigger: CheckpointTrigger,
        frontier_snapshot: list[str] | None = None,
    ) -> CheckpointData:
        """Create and save a new checkpoint."""
        yield_snapshot = self._yield_tracker.snapshot()
        
        checkpoint = CheckpointData(
            checkpoint_id=ulid.new().str,
            run_id=self.run_id,
            world_state=world_state,
            frontier_snapshot=frontier_snapshot,
            yield_snapshot=yield_snapshot,
            trigger=trigger,
            created_at=datetime.now(timezone.utc),
        )
        
        saved = await self._repo.save(checkpoint)
        logger.info("checkpoint_created", trigger=trigger.value, checkpoint_id=saved.checkpoint_id)
        return saved

    async def get_latest_checkpoint(self) -> CheckpointData | None:
        """Load the most recent checkpoint for this run."""
        loaded = await self._repo.get_latest(self.run_id)
        if loaded:
            logger.info("checkpoint_loaded", checkpoint_id=loaded.checkpoint_id)
        return loaded
