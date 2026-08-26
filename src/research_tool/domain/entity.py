"""Entity domain models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class EntityType(StrEnum):
    PRODUCT = "PRODUCT"
    POST = "POST"
    CATEGORY = "CATEGORY"
    KEYWORD = "KEYWORD"
    VIDEO = "VIDEO"
    CHANNEL = "CHANNEL"
    PAGE = "PAGE"


class IdentityConfidence(StrEnum):
    SAME = "SAME"
    PROBABLY_SAME = "PROBABLY_SAME"
    UNKNOWN = "UNKNOWN"
    DIFFERENT = "DIFFERENT"


@dataclass
class EntityListing:
    listing_id: str
    entity_id: str
    platform: str
    url: str | None = None
    title: str | None = None
    price: float | None = None
    currency: str | None = None
    metadata: dict | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EntityRelation:
    relation_id: str
    entity_id_a: str
    entity_id_b: str
    relation_type: IdentityConfidence
    confidence: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Entity:
    entity_id: str
    run_id: str
    entity_type: EntityType
    canonical_name: str
    brand: str | None = None
    model: str | None = None
    identity_confidence: IdentityConfidence = IdentityConfidence.UNKNOWN
    user_profile_match: dict | None = None
    provenance: dict | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
