"""Integration tests for the SQLite schema."""

import sqlite3
from pathlib import Path

import pytest

from research_tool.infrastructure.db.connection import apply_schema, get_connection


@pytest.fixture
async def tmp_db(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    await apply_schema(db_path)
    return db_path


async def test_schema_applies_cleanly(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    # Should not raise
    await apply_schema(db_path)


async def test_schema_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    await apply_schema(db_path)
    # Second apply must not raise or corrupt
    await apply_schema(db_path)


async def test_all_tables_exist(tmp_db: Path):
    expected_tables = {
        "runs",
        "seeds",
        "frontier",
        "graph_nodes",
        "graph_edges",
        "entities",
        "entity_listings",
        "entity_relations",
        "visits",
        "evidence",
        "evidence_themes",
        "checkpoints",
        "events",
    }
    async with get_connection(tmp_db) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = await cursor.fetchall()
        actual_tables = {row[0] for row in rows}
    assert expected_tables.issubset(actual_tables)


async def test_wal_mode_enabled(tmp_db: Path):
    async with get_connection(tmp_db) as conn:
        cursor = await conn.execute("PRAGMA journal_mode")
        row = await cursor.fetchone()
        assert row[0] == "wal"


async def test_foreign_keys_enabled(tmp_db: Path):
    async with get_connection(tmp_db) as conn:
        cursor = await conn.execute("PRAGMA foreign_keys")
        row = await cursor.fetchone()
        assert row[0] == 1


async def test_runs_table_has_expected_columns(tmp_db: Path):
    async with get_connection(tmp_db) as conn:
        cursor = await conn.execute("PRAGMA table_info(runs)")
        rows = await cursor.fetchall()
        columns = {row[1] for row in rows}  # row[1] = column name
    assert {"run_id", "goal_text", "status", "created_at", "updated_at"}.issubset(columns)


async def test_row_factory_enables_name_access(tmp_db: Path):
    async with get_connection(tmp_db) as conn:
        await conn.execute(
            "INSERT INTO runs (run_id, goal_text, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                "run_01",
                "Find mechanical keyboards",
                "RUNNING",
                "2026-08-26T22:00:00Z",
                "2026-08-26T22:00:00Z",
            ),
        )
        await conn.commit()

        cursor = await conn.execute("SELECT * FROM runs WHERE run_id = ?", ("run_01",))
        row = await cursor.fetchone()
        assert row is not None
        assert row["run_id"] == "run_01"
        assert row["goal_text"] == "Find mechanical keyboards"


async def test_foreign_key_violation_raises_error(tmp_db: Path):
    async with get_connection(tmp_db) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            await conn.execute(
                "INSERT INTO seeds (seed_id, run_id, text, source, created_at) VALUES (?, ?, ?, ?, ?)",
                ("seed_01", "nonexistent_run", "test text", "MANUAL", "2026-08-26T22:00:00Z"),
            )
            await conn.commit()


async def test_indexes_exist(tmp_db: Path):
    expected_indexes = {
        "idx_seeds_run",
        "idx_seeds_status",
        "idx_frontier_run_status",
        "idx_graph_nodes_run",
        "idx_graph_edges_from",
        "idx_graph_edges_to",
        "idx_visits_url",
        "idx_visits_entity",
        "idx_visits_fingerprint",
        "idx_evidence_entity",
        "idx_evidence_type",
        "idx_checkpoints_run",
        "idx_events_run",
    }
    async with get_connection(tmp_db) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        rows = await cursor.fetchall()
        actual_indexes = {row[0] for row in rows}
    assert expected_indexes.issubset(actual_indexes)
