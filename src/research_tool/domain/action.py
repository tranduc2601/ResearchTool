"""Action and execution domain models."""

from dataclasses import dataclass
from enum import StrEnum


class ActionType(StrEnum):
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    TYPE_TEXT = "TYPE_TEXT"
    SCROLL = "SCROLL"
    PRESS_KEY = "PRESS_KEY"
    BACK = "BACK"
    WAIT = "WAIT"
    GOAL_MET = "GOAL_MET"
    GOAL_FAILED = "GOAL_FAILED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    # Additional actions can be added here without breaking core logic


class ActionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    BLOCKED = "BLOCKED"
    STATE_CHANGE = "STATE_CHANGE"
    UNKNOWN = "UNKNOWN"


@dataclass
class ActionCommand:
    action_type: ActionType
    x: int | None = None
    y: int | None = None
    text: str | None = None
    key: str | None = None
    reasoning: str = ""


@dataclass
class ActionResult:
    status: ActionStatus
    message: str = ""
    error: str | None = None
