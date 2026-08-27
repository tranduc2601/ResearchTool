"""Frontier queue and prioritization manager."""
import structlog
import ulid
from datetime import datetime, timezone
from research_tool.domain import FrontierItem, FrontierScore, FrontierStatus
from research_tool.infrastructure.db.repositories.frontier_repo import FrontierRepo

logger = structlog.get_logger()

class FrontierManager:
    """
    Manages the priority queue for exploration.
    
    When a new candidate is discovered (a seed or an entity), it is scored
    and added to the frontier. The Orchestrator pops the highest-priority
    item for its next cycle.
    """

    def __init__(self, run_id: str, frontier_repo: FrontierRepo):
        self.run_id = run_id
        self._repo = frontier_repo

    async def add_seed(
        self,
        seed_id: str,
        mention_confidence: float = 0.5,
        seed_similarity: float = 0.5,
        source_diversity: float = 0.5,
        novelty: float = 0.5,
        unexplored_bonus: float = 0.5,
        depth_penalty: float = 0.0,
    ) -> FrontierItem:
        """Score and enqueue a seed for exploration."""
        score_components = FrontierScore(
            mention_score=mention_confidence,
            seed_similarity=seed_similarity,
            source_diversity=source_diversity,
            novelty=novelty,
            unexplored_bonus=unexplored_bonus,
            depth_penalty=depth_penalty
        )
        item = FrontierItem(
            frontier_id=ulid.new().str,
            run_id=self.run_id,
            seed_id=seed_id,
            entity_id=None,
            priority_score=score_components.compute(),
            score_components=score_components,
            status=FrontierStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await self._repo.create(item)
        logger.debug("frontier_added", item_id=item.frontier_id, seed_id=seed_id, score=item.priority_score)
        return created

    async def add_entity(
        self,
        entity_id: str,
        mention_confidence: float = 0.5,
        seed_similarity: float = 0.5,
        source_diversity: float = 0.5,
        novelty: float = 0.5,
        unexplored_bonus: float = 0.5,
        depth_penalty: float = 0.0,
    ) -> FrontierItem:
        """Score and enqueue an entity for exploration."""
        score_components = FrontierScore(
            mention_score=mention_confidence,
            seed_similarity=seed_similarity,
            source_diversity=source_diversity,
            novelty=novelty,
            unexplored_bonus=unexplored_bonus,
            depth_penalty=depth_penalty
        )
        item = FrontierItem(
            frontier_id=ulid.new().str,
            run_id=self.run_id,
            seed_id=None,
            entity_id=entity_id,
            priority_score=score_components.compute(),
            score_components=score_components,
            status=FrontierStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        created = await self._repo.create(item)
        logger.debug("frontier_added", item_id=item.frontier_id, entity_id=entity_id, score=item.priority_score)
        return created

    async def pop_next(self) -> FrontierItem | None:
        """Get the highest priority PENDING item and mark it IN_PROGRESS."""
        item = await self._repo.pop_next(self.run_id)
        if item:
            logger.info("frontier_popped", item_id=item.frontier_id, score=item.priority_score)
        return item

    async def mark_completed(self, frontier_id: str) -> None:
        """Mark an item as COMPLETED."""
        await self._repo.update_status(frontier_id, FrontierStatus.DONE)

    async def mark_failed(self, frontier_id: str) -> None:
        """Mark an item as FAILED."""
        await self._repo.update_status(frontier_id, FrontierStatus.SKIPPED)

    async def count_pending(self) -> int:
        """Return the number of pending items."""
        return await self._repo.count_by_status(self.run_id, FrontierStatus.PENDING)
