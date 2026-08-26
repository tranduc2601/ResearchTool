"""Event domain models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class EventType(StrEnum):
    SEARCH = "SEARCH"
    NAVIGATE = "NAVIGATE"
    CLICK = "CLICK"
    SCROLL = "SCROLL"
    TYPE = "TYPE"
    BACK = "BACK"
    SCREENSHOT = "SCREENSHOT"
    SEED_DISCOVERED = "SEED_DISCOVERED"
    EVIDENCE_SAVED = "EVIDENCE_SAVED"
    CHECKPOINT = "CHECKPOINT"
    RECOVERY = "RECOVERY"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    YIELD_LOW = "YIELD_LOW"
    SATURATION = "SATURATION"
    RUN_START = "RUN_START"
    RUN_END = "RUN_END"


class EventActor(StrEnum):
    AGENT = "AGENT"
    USER = "USER"


@dataclass
class ActionEvent:
    event_id: str
    run_id: str
    event_type: EventType
    actor: EventActor = EventActor.AGENT
    detail: dict | None = None
    parent_event_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
