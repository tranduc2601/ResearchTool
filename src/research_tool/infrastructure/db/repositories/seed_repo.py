"""Repository for Seed persistence."""

import json
from pathlib import Path

from research_tool.domain.seed import Seed, SeedSource, SeedStatus
from research_tool.infrastructure.db.connection import get_connection


class SeedRepo:
    """SQLite-backed repository for Seed."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(seed: Seed) -> tuple:
        return (
            seed.seed_id,
            seed.run_id,
            seed.text,
            seed.source.value,
            seed.parent_seed_id,
            seed.parent_entity_id,
            seed.parent_evidence_id,
            seed.expansion_reason,
            seed.expansion_depth,
            seed.status.value,
            json.dumps(seed.provenance) if seed.provenance is not None else None,
            seed.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row) -> Seed:
        from datetime import datetime

        provenance_raw = row["provenance"]
        return Seed(
            seed_id=row["seed_id"],
            run_id=row["run_id"],
            text=row["text"],
            source=SeedSource(row["source"]),
            status=SeedStatus(row["status"]),
            parent_seed_id=row["parent_seed_id"],
            parent_entity_id=row["parent_entity_id"],
            parent_evidence_id=row["parent_evidence_id"],
            expansion_reason=row["expansion_reason"],
            expansion_depth=row["expansion_depth"],
            provenance=json.loads(provenance_raw) if provenance_raw else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create(self, seed: Seed) -> Seed:
        """Insert a Seed row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO seeds
                    (seed_id, run_id, text, source, parent_seed_id, parent_entity_id,
                     parent_evidence_id, expansion_reason, expansion_depth, status,
                     provenance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(seed),
            )
            await conn.commit()
        return seed

    async def get(self, seed_id: str) -> Seed | None:
        """Fetch a Seed by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM seeds WHERE seed_id = ?", (seed_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def list_by_run(
        self, run_id: str, status: SeedStatus | None = None
    ) -> list[Seed]:
        """Return all seeds for a run, optionally filtered by status."""
        async with get_connection(self.db_path) as conn:
            if status is None:
                cursor = await conn.execute(
                    "SELECT * FROM seeds WHERE run_id = ? ORDER BY created_at",
                    (run_id,),
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM seeds WHERE run_id = ? AND status = ? ORDER BY created_at",
                    (run_id, status.value),
                )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]

    async def update_status(self, seed_id: str, status: SeedStatus) -> None:
        """Update the status of a Seed."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                "UPDATE seeds SET status = ? WHERE seed_id = ?",
                (status.value, seed_id),
            )
            await conn.commit()

    async def get_by_text_and_run(self, text: str, run_id: str) -> Seed | None:
        """Find a seed by its text within a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM seeds WHERE text = ? AND run_id = ? LIMIT 1",
                (text, run_id),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)
