"""Repository for CheckpointData persistence."""

import dataclasses
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from research_tool.domain.checkpoint import CheckpointData, CheckpointTrigger
from research_tool.domain.world_state import AgentStatus, Confidence, PageType, WorldState
from research_tool.infrastructure.db.connection import get_connection


def _world_state_to_dict(ws: WorldState) -> dict:
    """Serialize WorldState to a JSON-safe dict."""
    d = dataclasses.asdict(ws)
    # Convert datetime -> isoformat string
    if isinstance(d.get("updated_at"), datetime):
        d["updated_at"] = d["updated_at"].isoformat()
    return d


def _dict_to_world_state(d: dict) -> WorldState:
    """Reconstruct WorldState from a deserialized dict."""
    return WorldState(
        run_id=d["run_id"],
        platform=d["platform"],
        app=d["app"],
        page_type=PageType(d["page_type"]),
        current_entity_id=d.get("current_entity_id"),
        current_seed_id=d.get("current_seed_id"),
        root_seed_id=d.get("root_seed_id"),
        current_branch_id=d.get("current_branch_id"),
        scroll_position=d.get("scroll_position"),
        last_action_event_id=d.get("last_action_event_id"),
        current_objective=d.get("current_objective", ""),
        navigation_history=d.get("navigation_history", []),
        confidence=Confidence(d["confidence"]),
        agent_status=AgentStatus(d["agent_status"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
    )


class CheckpointRepo:
    """SQLite-backed repository for CheckpointData."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_row(checkpoint: CheckpointData) -> tuple:
        world_state_json = json.dumps(_world_state_to_dict(checkpoint.world_state))
        frontier_snapshot_json = (
            json.dumps(checkpoint.frontier_snapshot)
            if checkpoint.frontier_snapshot
            else None
        )
        yield_snapshot_json = (
            json.dumps(checkpoint.yield_snapshot)
            if checkpoint.yield_snapshot is not None
            else None
        )
        return (
            checkpoint.checkpoint_id,
            checkpoint.run_id,
            world_state_json,
            frontier_snapshot_json,
            yield_snapshot_json,
            checkpoint.trigger.value,
            checkpoint.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row) -> CheckpointData:
        world_state_dict = json.loads(row["world_state"])
        world_state = _dict_to_world_state(world_state_dict)

        frontier_snapshot_raw = row["frontier_snapshot"]
        frontier_snapshot = json.loads(frontier_snapshot_raw) if frontier_snapshot_raw else []

        yield_snapshot_raw = row["yield_snapshot"]
        yield_snapshot = json.loads(yield_snapshot_raw) if yield_snapshot_raw else None

        return CheckpointData(
            checkpoint_id=row["checkpoint_id"],
            run_id=row["run_id"],
            world_state=world_state,
            frontier_snapshot=frontier_snapshot,
            yield_snapshot=yield_snapshot,
            trigger=CheckpointTrigger(row["trigger"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def save(self, checkpoint: CheckpointData) -> CheckpointData:
        """Insert a CheckpointData row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO checkpoints
                    (checkpoint_id, run_id, world_state, frontier_snapshot, yield_snapshot,
                     trigger, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(checkpoint),
            )
            await conn.commit()
        return checkpoint

    async def get(self, checkpoint_id: str) -> CheckpointData | None:
        """Fetch a CheckpointData by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def get_latest(self, run_id: str) -> CheckpointData | None:
        """Return most recent checkpoint for a run, or None."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE run_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (run_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._from_row(row)

    async def list_by_run(self, run_id: str, limit: int = 10) -> list[CheckpointData]:
        """Return checkpoints for a run, most recent first, up to limit."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE run_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (run_id, limit),
            )
            rows = await cursor.fetchall()
        return [self._from_row(r) for r in rows]
