"""Repository for Entity, EntityListing, and EntityRelation persistence."""

import json
from datetime import datetime
from pathlib import Path

from research_tool.domain.entity import (
    Entity,
    EntityListing,
    EntityRelation,
    EntityType,
    IdentityConfidence,
)
from research_tool.infrastructure.db.connection import get_connection


class EntityRepo:
    """SQLite-backed repository for Entity, EntityListing, and EntityRelation."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers -- Entity
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(entity: Entity) -> tuple:
        return (
            entity.entity_id,
            entity.run_id,
            entity.entity_type.value,
            entity.canonical_name,
            entity.brand,
            entity.model,
            entity.identity_confidence.value,
            json.dumps(entity.user_profile_match) if entity.user_profile_match is not None else None,
            json.dumps(entity.provenance) if entity.provenance is not None else None,
            entity.created_at.isoformat(),
            entity.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row) -> Entity:
        user_profile_raw = row["user_profile_match"]
        provenance_raw = row["provenance"]
        return Entity(
            entity_id=row["entity_id"],
            run_id=row["run_id"],
            entity_type=EntityType(row["entity_type"]),
            canonical_name=row["canonical_name"],
            brand=row["brand"],
            model=row["model"],
            identity_confidence=IdentityConfidence(row["identity_confidence"]),
            user_profile_match=json.loads(user_profile_raw) if user_profile_raw is not None else None,
            provenance=json.loads(provenance_raw) if provenance_raw is not None else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ------------------------------------------------------------------
    # Serialization helpers -- EntityListing
    # ------------------------------------------------------------------

    @staticmethod
    def _listing_to_row(listing: EntityListing) -> tuple:
        return (
            listing.listing_id,
            listing.entity_id,
            listing.platform,
            listing.url,
            listing.title,
            listing.price,
            listing.currency,
            json.dumps(listing.metadata) if listing.metadata is not None else None,
            listing.captured_at.isoformat(),
        )

    @staticmethod
    def _listing_from_row(row) -> EntityListing:
        metadata_raw = row["metadata"]
        return EntityListing(
            listing_id=row["listing_id"],
            entity_id=row["entity_id"],
            platform=row["platform"],
            url=row["url"],
            title=row["title"],
            price=row["price"],
            currency=row["currency"],
            metadata=json.loads(metadata_raw) if metadata_raw is not None else None,
            captured_at=datetime.fromisoformat(row["captured_at"]),
        )

    # ------------------------------------------------------------------
    # Serialization helpers -- EntityRelation
    # ------------------------------------------------------------------

    @staticmethod
    def _relation_to_row(relation: EntityRelation) -> tuple:
        return (
            relation.relation_id,
            relation.entity_id_a,
            relation.entity_id_b,
            relation.relation_type.value,
            relation.confidence,
            relation.created_at.isoformat(),
        )

    @staticmethod
    def _relation_from_row(row) -> EntityRelation:
        return EntityRelation(
            relation_id=row["relation_id"],
            entity_id_a=row["entity_id_a"],
            entity_id_b=row["entity_id_b"],
            relation_type=IdentityConfidence(row["relation_type"]),
            confidence=row["confidence"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ------------------------------------------------------------------
    # Public API -- Entity
    # ------------------------------------------------------------------

    async def create(self, entity: Entity) -> Entity:
        """Insert an Entity row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO entities
                    (entity_id, run_id, entity_type, canonical_name, brand, model,
                     identity_confidence, user_profile_match, provenance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(entity),
            )
            await conn.commit()
        return entity

    async def get(self, entity_id: str) -> Entity | None:
        """Fetch an Entity by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM entities WHERE entity_id = ?", (entity_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def find_by_name(self, canonical_name: str, run_id: str) -> Entity | None:
        """Find an Entity by canonical_name within a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM entities WHERE canonical_name = ? AND run_id = ? LIMIT 1",
                (canonical_name, run_id),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def update_identity_confidence(
        self, entity_id: str, confidence: IdentityConfidence
    ) -> None:
        """Update the identity_confidence of an Entity."""
        from datetime import UTC

        now = datetime.now(UTC).isoformat()
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                "UPDATE entities SET identity_confidence = ?, updated_at = ? WHERE entity_id = ?",
                (confidence.value, now, entity_id),
            )
            await conn.commit()

    async def list_by_run(
        self, run_id: str, entity_type: EntityType | None = None
    ) -> list[Entity]:
        """Return all Entities for a run, optionally filtered by type."""
        async with get_connection(self.db_path) as conn:
            if entity_type is not None:
                cursor = await conn.execute(
                    "SELECT * FROM entities WHERE run_id = ? AND entity_type = ? ORDER BY created_at",
                    (run_id, entity_type.value),
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM entities WHERE run_id = ? ORDER BY created_at",
                    (run_id,),
                )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]

    async def count_by_run(self, run_id: str) -> int:
        """Return count of Entity rows for a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM entities WHERE run_id = ?", (run_id,)
            )
            row = await cursor.fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # Public API -- Listings
    # ------------------------------------------------------------------

    async def add_listing(self, listing: EntityListing) -> EntityListing:
        """Insert an EntityListing row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO entity_listings
                    (listing_id, entity_id, platform, url, title, price, currency, metadata, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._listing_to_row(listing),
            )
            await conn.commit()
        return listing

    async def list_listings(self, entity_id: str) -> list[EntityListing]:
        """Return all EntityListings for an entity."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM entity_listings WHERE entity_id = ? ORDER BY captured_at",
                (entity_id,),
            )
            rows = await cursor.fetchall()
        return [self._listing_from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Public API -- Relations
    # ------------------------------------------------------------------

    async def add_relation(self, relation: EntityRelation) -> EntityRelation:
        """Insert an EntityRelation row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO entity_relations
                    (relation_id, entity_id_a, entity_id_b, relation_type, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                self._relation_to_row(relation),
            )
            await conn.commit()
        return relation

    async def list_relations(self, entity_id: str) -> list[EntityRelation]:
        """Return all EntityRelations where entity_id is either side."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM entity_relations
                WHERE entity_id_a = ? OR entity_id_b = ?
                ORDER BY created_at
                """,
                (entity_id, entity_id),
            )
            rows = await cursor.fetchall()
        return [self._relation_from_row(r) for r in rows]
