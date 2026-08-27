"""Repository for Evidence and EvidenceTheme persistence."""

import json
from datetime import datetime
from pathlib import Path

from research_tool.domain.evidence import Evidence, EvidenceTheme, EvidenceType
from research_tool.infrastructure.db.connection import get_connection


class EvidenceRepo:
    """SQLite-backed repository for Evidence and EvidenceTheme."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(evidence: Evidence) -> tuple:
        return (
            evidence.evidence_id,
            evidence.run_id,
            evidence.entity_id,
            evidence.evidence_type.value,
            evidence.raw_text,
            evidence.source_platform,
            evidence.source_url,
            evidence.direct_url,
            evidence.parent_url,
            evidence.screenshot_path,
            evidence.confidence,
            json.dumps(evidence.provenance) if evidence.provenance is not None else None,
            evidence.captured_at.isoformat(),
        )

    @staticmethod
    def _from_row(row) -> Evidence:
        provenance_raw = row["provenance"]
        return Evidence(
            evidence_id=row["evidence_id"],
            run_id=row["run_id"],
            entity_id=row["entity_id"],
            evidence_type=EvidenceType(row["evidence_type"]),
            raw_text=row["raw_text"],
            source_platform=row["source_platform"],
            source_url=row["source_url"],
            direct_url=row["direct_url"],
            parent_url=row["parent_url"],
            screenshot_path=row["screenshot_path"],
            confidence=row["confidence"],
            provenance=json.loads(provenance_raw) if provenance_raw is not None else None,
            captured_at=datetime.fromisoformat(row["captured_at"]),
        )

    @staticmethod
    def _theme_to_row(theme: EvidenceTheme) -> tuple:
        return (
            theme.theme_id,
            theme.entity_id,
            theme.theme_label,
            theme.frequency,
            json.dumps(theme.sample_evidence_ids),
            theme.updated_at.isoformat(),
        )

    @staticmethod
    def _theme_from_row(row) -> EvidenceTheme:
        sample_ids_raw = row["sample_ids"]
        return EvidenceTheme(
            theme_id=row["theme_id"],
            entity_id=row["entity_id"],
            theme_label=row["theme_label"],
            frequency=row["frequency"],
            sample_evidence_ids=json.loads(sample_ids_raw) if sample_ids_raw else [],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create(self, evidence: Evidence) -> Evidence:
        """Insert an Evidence row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO evidence
                    (evidence_id, run_id, entity_id, evidence_type, raw_text,
                     source_platform, source_url, direct_url, parent_url,
                     screenshot_path, confidence, provenance, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(evidence),
            )
            await conn.commit()
        return evidence

    async def get(self, evidence_id: str) -> Evidence | None:
        """Fetch an Evidence by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def list_by_entity(
        self, entity_id: str, evidence_type: EvidenceType | None = None
    ) -> list[Evidence]:
        """Return all Evidence for an entity, optionally filtered by type."""
        async with get_connection(self.db_path) as conn:
            if evidence_type is not None:
                cursor = await conn.execute(
                    "SELECT * FROM evidence WHERE entity_id = ? AND evidence_type = ? ORDER BY captured_at",
                    (entity_id, evidence_type.value),
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM evidence WHERE entity_id = ? ORDER BY captured_at",
                    (entity_id,),
                )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]

    async def list_by_run(self, run_id: str, limit: int = 100) -> list[Evidence]:
        """Return Evidence for a run, up to limit."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM evidence WHERE run_id = ? ORDER BY captured_at LIMIT ?",
                (run_id, limit),
            )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]

    async def count_by_run(self, run_id: str) -> int:
        """Return count of Evidence rows for a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM evidence WHERE run_id = ?", (run_id,)
            )
            row = await cursor.fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # Theme aggregation
    # ------------------------------------------------------------------

    async def upsert_theme(self, theme: EvidenceTheme) -> EvidenceTheme:
        """Insert or update an EvidenceTheme. If entity+label exists, increment frequency."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT theme_id, frequency, sample_ids FROM evidence_themes WHERE entity_id = ? AND theme_label = ?",
                (theme.entity_id, theme.theme_label),
            )
            existing = await cursor.fetchone()
            if existing is None:
                await conn.execute(
                    """
                    INSERT INTO evidence_themes
                        (theme_id, entity_id, theme_label, frequency, sample_ids, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    self._theme_to_row(theme),
                )
            else:
                existing_id = existing["theme_id"]
                old_ids = json.loads(existing["sample_ids"]) if existing["sample_ids"] else []
                merged_ids = list(dict.fromkeys(old_ids + theme.sample_evidence_ids))
                new_freq = existing["frequency"] + 1
                await conn.execute(
                    """
                    UPDATE evidence_themes
                    SET frequency = ?, sample_ids = ?, updated_at = ?
                    WHERE theme_id = ?
                    """,
                    (new_freq, json.dumps(merged_ids), theme.updated_at.isoformat(), existing_id),
                )
                theme = EvidenceTheme(
                    theme_id=existing_id,
                    entity_id=theme.entity_id,
                    theme_label=theme.theme_label,
                    frequency=new_freq,
                    sample_evidence_ids=merged_ids,
                    updated_at=theme.updated_at,
                )
            await conn.commit()
        return theme

    async def list_themes_by_entity(self, entity_id: str) -> list[EvidenceTheme]:
        """Return all EvidenceThemes for an entity."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM evidence_themes WHERE entity_id = ? ORDER BY frequency DESC",
                (entity_id,),
            )
            rows = await cursor.fetchall()
        return [self._theme_from_row(r) for r in rows]
