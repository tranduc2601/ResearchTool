"""Seed and related types."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class SeedSource(StrEnum):
    """Source from which a seed was derived."""

    USER = "USER"
    COMMENT = "COMMENT"
    REVIEW = "REVIEW"
    RECOMMENDATION = "RECOMMENDATION"
    SOCIAL = "SOCIAL"
    SEARCH = "SEARCH"
    INFERRED = "INFERRED"


class SeedStatus(StrEnum):
    """Status of a seed in the exploration pipeline."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXHAUSTED = "EXHAUSTED"


@dataclass
class Seed:
    """A search term, keyword, or concept to be explored."""

    seed_id: str
    run_id: str
    text: str
    source: SeedSource
    status: SeedStatus = SeedStatus.PENDING
    parent_seed_id: str | None = None
    parent_entity_id: str | None = None
    parent_evidence_id: str | None = None
    expansion_reason: str | None = None
    expansion_depth: int = 0
    provenance: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
