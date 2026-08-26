"""Checkpoint domain models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from research_tool.domain.world_state import WorldState


class CheckpointTrigger(StrEnum):
    SEARCH_DONE = "SEARCH_DONE"
    PRODUCT_OPENED = "PRODUCT_OPENED"
    REVIEW_SECTION_ENTERED = "REVIEW_SECTION_ENTERED"
    EVIDENCE_SAVED = "EVIDENCE_SAVED"
    SEED_DISCOVERED = "SEED_DISCOVERED"
    FRONTIER_ITEM_SELECTED = "FRONTIER_ITEM_SELECTED"
    NAVIGATION_COMPLETED = "NAVIGATION_COMPLETED"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"


@dataclass
class CheckpointData:
    checkpoint_id: str
    run_id: str
    world_state: WorldState
    frontier_snapshot: list[dict] = field(default_factory=list)
    yield_snapshot: dict | None = None
    trigger: CheckpointTrigger = CheckpointTrigger.EVIDENCE_SAVED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
