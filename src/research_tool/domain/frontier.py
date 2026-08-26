"""FrontierItem, FrontierScore, and related types."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class FrontierStatus(StrEnum):
    """Status of a frontier item."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    SKIPPED = "SKIPPED"


@dataclass
class FrontierScore:
    """Component scores contributing to frontier item priority."""

    mention_score: float = 0.0
    seed_similarity: float = 0.0
    source_diversity: float = 0.0
    novelty: float = 0.0
    unexplored_bonus: float = 0.0
    depth_penalty: float = 0.0
    total: float = 0.0

    def compute(self) -> float:
        """Apply V1 weights and return the total priority score."""
        total = (
            0.35 * self.mention_score
            + 0.25 * self.seed_similarity
            + 0.20 * self.source_diversity
            + 0.10 * self.novelty
            + 0.10 * self.unexplored_bonus
            - 0.20 * self.depth_penalty
        )
        return max(0.0, min(1.0, total))


@dataclass
class FrontierItem:
    """An item queued in the exploration frontier."""

    frontier_id: str
    run_id: str
    seed_id: str | None = None
    entity_id: str | None = None
    priority_score: float = 0.0
    score_components: FrontierScore | None = None
    status: FrontierStatus = FrontierStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
