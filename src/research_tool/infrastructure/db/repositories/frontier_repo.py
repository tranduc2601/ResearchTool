"""Repository for FrontierItem persistence."""

import dataclasses
import json
from pathlib import Path

from research_tool.domain.frontier import FrontierItem, FrontierScore, FrontierStatus
from research_tool.infrastructure.db.connection import get_connection


class FrontierRepo:
    """SQLite-backed repository for FrontierItem."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(item: FrontierItem) -> tuple:
        score_json = (
            json.dumps(dataclasses.asdict(item.score_components))
            if item.score_components is not None
            else None
        )
        return (
            item.frontier_id,
            item.run_id,
            item.seed_id,
            item.entity_id,
            item.priority_score,
            score_json,
            item.status.value,
            item.created_at.isoformat(),
            item.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row) -> FrontierItem:
        from datetime import datetime

        score_raw = row["score_components"]
        score = FrontierScore(**json.loads(score_raw)) if score_raw else None
        return FrontierItem(
            frontier_id=row["frontier_id"],
            run_id=row["run_id"],
            seed_id=row["seed_id"],
            entity_id=row["entity_id"],
            priority_score=row["priority_score"],
            score_components=score,
            status=FrontierStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create(self, item: FrontierItem) -> FrontierItem:
        """Insert a FrontierItem row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO frontier
                    (frontier_id, run_id, seed_id, entity_id, priority_score,
                     score_components, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(item),
            )
            await conn.commit()
        return item

    async def get(self, frontier_id: str) -> FrontierItem | None:
        """Fetch a FrontierItem by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM frontier WHERE frontier_id = ?", (frontier_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def pop_next(self, run_id: str) -> FrontierItem | None:
        """Return highest-priority PENDING item and atomically mark it IN_PROGRESS."""
        from datetime import UTC, datetime

        async with get_connection(self.db_path) as conn:
            # Use BEGIN IMMEDIATE for an exclusive write transaction
            await conn.execute("BEGIN IMMEDIATE")
            cursor = await conn.execute(
                """
                SELECT * FROM frontier
                WHERE run_id = ? AND status = 'PENDING'
                ORDER BY priority_score DESC
                LIMIT 1
                """,
                (run_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                await conn.execute("ROLLBACK")
                return None
            now = datetime.now(UTC).isoformat()
            await conn.execute(
                "UPDATE frontier SET status = 'IN_PROGRESS', updated_at = ? WHERE frontier_id = ?",
                (now, row["frontier_id"]),
            )
            await conn.commit()

        # Re-read to get the updated row
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM frontier WHERE frontier_id = ?", (row["frontier_id"],)
            )
            updated_row = await cursor.fetchone()
        return self._from_row(updated_row)

    async def update_status(self, frontier_id: str, status: FrontierStatus) -> None:
        """Update status of a FrontierItem."""
        from datetime import UTC, datetime

        now = datetime.now(UTC).isoformat()
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                "UPDATE frontier SET status = ?, updated_at = ? WHERE frontier_id = ?",
                (status.value, now, frontier_id),
            )
            await conn.commit()

    async def list_pending(self, run_id: str, limit: int = 20) -> list[FrontierItem]:
        """Return up to `limit` PENDING items for a run, ordered by priority descending."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM frontier
                WHERE run_id = ? AND status = 'PENDING'
                ORDER BY priority_score DESC
                LIMIT ?
                """,
                (run_id, limit),
            )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]

    async def count_by_status(self, run_id: str, status: FrontierStatus) -> int:
        """Count frontier items in a given status for a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM frontier WHERE run_id = ? AND status = ?",
                (run_id, status.value),
            )
            row = await cursor.fetchone()
        return row[0]
