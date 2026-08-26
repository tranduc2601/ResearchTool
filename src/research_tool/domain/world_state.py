"""WorldState and related domain models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class PageType(StrEnum):
    UNKNOWN = "UNKNOWN"
    SEARCH_RESULT = "SEARCH_RESULT"
    PRODUCT_PAGE = "PRODUCT_PAGE"
    REVIEW_SECTION = "REVIEW_SECTION"
    COMMENT_SECTION = "COMMENT_SECTION"
    SOCIAL_POST = "SOCIAL_POST"
    SOCIAL_FEED = "SOCIAL_FEED"
    VIDEO_PAGE = "VIDEO_PAGE"
    CATEGORY_PAGE = "CATEGORY_PAGE"
    LOGIN_PAGE = "LOGIN_PAGE"
    CAPTCHA = "CAPTCHA"
    ERROR_PAGE = "ERROR_PAGE"
    NAVIGATION = "NAVIGATION"


class Confidence(StrEnum):
    KNOWN = "KNOWN"
    UNCERTAIN = "UNCERTAIN"
    UNKNOWN = "UNKNOWN"


class AgentStatus(StrEnum):
    NORMAL = "NORMAL"
    LOW_YIELD = "LOW_YIELD"
    SOFT_BLOCK_SUSPECTED = "SOFT_BLOCK_SUSPECTED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    HARD_ERROR = "HARD_ERROR"
    PAUSED = "PAUSED"
    DONE = "DONE"


@dataclass
class WorldState:
    run_id: str
    platform: str
    app: str
    page_type: PageType = PageType.UNKNOWN
    current_entity_id: str | None = None
    current_seed_id: str | None = None
    root_seed_id: str | None = None
    current_branch_id: str | None = None
    scroll_position: float | None = None
    last_action_event_id: str | None = None
    current_objective: str = ""
    navigation_history: list[str] = field(default_factory=list)
    confidence: Confidence = Confidence.UNKNOWN
    agent_status: AgentStatus = AgentStatus.NORMAL
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
