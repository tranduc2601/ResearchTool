"""Repository for ActionEvent persistence."""

import json
from datetime import datetime
from pathlib import Path

from research_tool.domain.event import ActionEvent, EventActor, EventType
from research_tool.infrastructure.db.connection import get_connection


class EventRepo:
    """SQLite-backed repository for ActionEvent."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(event: ActionEvent) -> tuple:
        return (
            event.event_id,
            event.run_id,
            event.event_type.value,
            event.actor.value,
            json.dumps(event.detail) if event.detail is not None else None,
            event.parent_event_id,
            event.occurred_at.isoformat(),
        )

    @staticmethod
    def _from_row(row) -> ActionEvent:
        detail_raw = row["detail"]
        return ActionEvent(
            event_id=row["event_id"],
            run_id=row["run_id"],
            event_type=EventType(row["event_type"]),
            actor=EventActor(row["actor"]),
            detail=json.loads(detail_raw) if detail_raw is not None else None,
            parent_event_id=row["parent_event_id"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def append(self, event: ActionEvent) -> ActionEvent:
        """INSERT an ActionEvent row (JSONL-style append, no update)."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO events
                    (event_id, run_id, event_type, actor, detail, parent_event_id, occurred_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(event),
            )
            await conn.commit()
        return event

    async def get(self, event_id: str) -> ActionEvent | None:
        """Fetch an ActionEvent by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM events WHERE event_id = ?", (event_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def list_by_run(
        self, run_id: str, limit: int = 200, offset: int = 0
    ) -> list[ActionEvent]:
        """Return events for a run ordered by occurred_at, with pagination."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM events
                WHERE run_id = ?
                ORDER BY occurred_at
                LIMIT ? OFFSET ?
                """,
                (run_id, limit, offset),
            )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]

    async def list_by_type(self, run_id: str, event_type: EventType) -> list[ActionEvent]:
        """Return events for a run filtered by event_type."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM events
                WHERE run_id = ? AND event_type = ?
                ORDER BY occurred_at
                """,
                (run_id, event_type.value),
            )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]

    async def count_by_run(self, run_id: str) -> int:
        """Return count of events for a run."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM events WHERE run_id = ?", (run_id,)
            )
            row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_recent(self, run_id: str, n: int = 10) -> list[ActionEvent]:
        """Return N most recent events for a run, ordered by occurred_at DESC."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM events
                WHERE run_id = ?
                ORDER BY occurred_at DESC
                LIMIT ?
                """,
                (run_id, n),
            )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]
