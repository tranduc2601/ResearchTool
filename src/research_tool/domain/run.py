"""RunSession and related types."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class StopCondition(StrEnum):
    """Conditions under which a run session stops."""

    TIME_END = "TIME_END"
    FRONTIER_EXHAUSTED = "FRONTIER_EXHAUSTED"
    YIELD_SATURATION = "YIELD_SATURATION"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    MANUAL_STOP = "MANUAL_STOP"


class RunStatus(StrEnum):
    """Lifecycle status of a run session."""

    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class RunSession:
    """Represents a research run session."""

    run_id: str
    goal_text: str
    status: RunStatus = RunStatus.RUNNING
    time_end: datetime | None = None
    stop_conditions: list[StopCondition] = field(default_factory=list)
    user_profile_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
