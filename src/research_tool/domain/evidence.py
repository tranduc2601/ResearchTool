"""Evidence domain model."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class EvidenceType(StrEnum):
    NEGATIVE_COMMENT = "NEGATIVE_COMMENT"
    POSITIVE_COMMENT = "POSITIVE_COMMENT"
    REVIEW = "REVIEW"
    RECOMMENDATION = "RECOMMENDATION"
    PRODUCT_CLAIM = "PRODUCT_CLAIM"
    SOCIAL_POST = "SOCIAL_POST"
    SPECIFICATION = "SPECIFICATION"
    PRICE_OBSERVATION = "PRICE_OBSERVATION"
    DURABILITY_CLAIM = "DURABILITY_CLAIM"
    PAIN_POINT = "PAIN_POINT"
    RELATED_PRODUCT = "RELATED_PRODUCT"
    RELATED_CATEGORY = "RELATED_CATEGORY"


@dataclass
class Evidence:
    evidence_id: str
    run_id: str
    evidence_type: EvidenceType
    source_platform: str
    raw_text: str | None = None
    source_url: str | None = None
    direct_url: str | None = None
    parent_url: str | None = None
    entity_id: str | None = None
    screenshot_path: str | None = None
    confidence: float | None = None
    provenance: dict | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EvidenceTheme:
    theme_id: str
    entity_id: str
    theme_label: str
    frequency: int = 1
    sample_evidence_ids: list[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
