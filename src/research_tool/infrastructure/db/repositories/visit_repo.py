"""Repository for VisitRecord persistence."""

from pathlib import Path

from research_tool.domain.visit import VisitRecord
from research_tool.infrastructure.db.connection import get_connection


class VisitRepo:
    """SQLite-backed repository for VisitRecord."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(visit: VisitRecord) -> tuple:
        return (
            visit.visit_id,
            visit.run_id,
            visit.url,
            visit.entity_id,
            visit.platform,
            visit.content_fingerprint,
            visit.screen_fingerprint,
            visit.visited_at.isoformat(),
            visit.revisit_count,
            visit.last_revisit_reason,
            visit.last_revisit_sought,
        )

    @staticmethod
    def _from_row(row) -> VisitRecord:
        from datetime import datetime

        return VisitRecord(
            visit_id=row["visit_id"],
            run_id=row["run_id"],
            platform=row["platform"],
            url=row["url"],
            entity_id=row["entity_id"],
            content_fingerprint=row["content_fingerprint"],
            screen_fingerprint=row["screen_fingerprint"],
            visited_at=datetime.fromisoformat(row["visited_at"]),
            revisit_count=row["revisit_count"],
            last_revisit_reason=row["last_revisit_reason"],
            last_revisit_sought=row["last_revisit_sought"],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create(self, visit: VisitRecord) -> VisitRecord:
        """Insert a VisitRecord row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO visits
                    (visit_id, run_id, url, entity_id, platform,
                     content_fingerprint, screen_fingerprint,
                     visited_at, revisit_count, last_revisit_reason, last_revisit_sought)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(visit),
            )
            await conn.commit()
        return visit

    async def get_by_url(self, url: str, run_id: str) -> VisitRecord | None:
        """Fetch a VisitRecord by URL within a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM visits WHERE url = ? AND run_id = ? LIMIT 1",
                (url, run_id),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def get_by_fingerprint(
        self, fingerprint: str, run_id: str
    ) -> VisitRecord | None:
        """Fetch a VisitRecord by content fingerprint within a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM visits WHERE content_fingerprint = ? AND run_id = ? LIMIT 1",
                (fingerprint, run_id),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def get_by_entity(self, entity_id: str, run_id: str) -> VisitRecord | None:
        """Fetch a VisitRecord by entity_id within a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM visits WHERE entity_id = ? AND run_id = ? LIMIT 1",
                (entity_id, run_id),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def increment_revisit(
        self, visit_id: str, reason: str, sought: str
    ) -> None:
        """Increment the revisit count and record the reason and sought text."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                UPDATE visits
                SET revisit_count = revisit_count + 1,
                    last_revisit_reason = ?,
                    last_revisit_sought = ?
                WHERE visit_id = ?
                """,
                (reason, sought, visit_id),
            )
            await conn.commit()

    async def is_visited(
        self, url: str | None, fingerprint: str | None, run_id: str
    ) -> bool:
        """Return True if url OR content_fingerprint matches an existing visit for this run."""
        async with get_connection(self.db_path) as conn:
            if url is not None and fingerprint is not None:
                cursor = await conn.execute(
                    """
                    SELECT 1 FROM visits
                    WHERE run_id = ? AND (url = ? OR content_fingerprint = ?)
                    LIMIT 1
                    """,
                    (run_id, url, fingerprint),
                )
            elif url is not None:
                cursor = await conn.execute(
                    "SELECT 1 FROM visits WHERE run_id = ? AND url = ? LIMIT 1",
                    (run_id, url),
                )
            elif fingerprint is not None:
                cursor = await conn.execute(
                    "SELECT 1 FROM visits WHERE run_id = ? AND content_fingerprint = ? LIMIT 1",
                    (run_id, fingerprint),
                )
            else:
                return False
            row = await cursor.fetchone()
        return row is not None
