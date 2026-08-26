"""UserProfile domain model."""

from dataclasses import dataclass, field


@dataclass
class UserProfile:
    profile_id: str
    budget_anchor: float | None = None
    budget_currency: str = "VND"
    size_constraints: str | None = None
    height_cm: float | None = None
    usage_context: str | None = None
    preferences: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    pp_priorities: list[str] = field(default_factory=list)
