"""Visit domain model."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class VisitRecord:
    visit_id: str
    run_id: str
    platform: str
    url: str | None = None
    entity_id: str | None = None
    content_fingerprint: str | None = None
    screen_fingerprint: str | None = None
    visited_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    revisit_count: int = 0
    last_revisit_reason: str | None = None
    last_revisit_sought: str | None = None
