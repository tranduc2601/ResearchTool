"""Repository for RunSession persistence."""

import json
from datetime import datetime
from pathlib import Path

from research_tool.domain.run import RunSession, RunStatus, StopCondition
from research_tool.infrastructure.db.connection import get_connection


class RunRepo:
    """SQLite-backed repository for RunSession."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(run: RunSession) -> tuple:
        return (
            run.run_id,
            run.goal_text,
            run.user_profile_id,
            run.time_end.isoformat() if run.time_end else None,
            json.dumps([sc.value for sc in run.stop_conditions]),
            run.status.value,
            run.created_at.isoformat(),
            run.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row) -> RunSession:
        stop_conditions_raw = row["stop_conditions"]
        stop_conditions = (
            [StopCondition(v) for v in json.loads(stop_conditions_raw)]
            if stop_conditions_raw
            else []
        )
        return RunSession(
            run_id=row["run_id"],
            goal_text=row["goal_text"],
            status=RunStatus(row["status"]),
            time_end=datetime.fromisoformat(row["time_end"]) if row["time_end"] else None,
            stop_conditions=stop_conditions,
            user_profile_id=row["user_profile"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create(self, run: RunSession) -> RunSession:
        """Insert a RunSession row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO runs
                    (run_id, goal_text, user_profile, time_end, stop_conditions,
                     status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(run),
            )
            await conn.commit()
        return run

    async def get(self, run_id: str) -> RunSession | None:
        """Fetch a RunSession by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def update_status(self, run_id: str, status: RunStatus) -> None:
        """Update the status (and updated_at) of a RunSession."""
        from datetime import UTC

        now = datetime.now(UTC).isoformat()
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                "UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
                (status.value, now, run_id),
            )
            await conn.commit()

    async def list_recent(self, limit: int = 10) -> list[RunSession]:
        """Return the most recently created RunSessions."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]
