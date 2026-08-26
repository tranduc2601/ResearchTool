"""SQLite connection manager.

Usage:
    async with get_connection(db_path) as conn:
        await conn.execute(...)
"""

from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


@asynccontextmanager
async def get_connection(db_path: Path | str):
    """Open an aiosqlite connection, set WAL + foreign keys, yield, close."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode = WAL")
        await conn.execute("PRAGMA foreign_keys = ON")
        yield conn


async def apply_schema(db_path: Path | str) -> None:
    """Apply schema.sql to the database. Safe to run on existing databases

    because all statements use CREATE TABLE IF NOT EXISTS.
    """
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    async with get_connection(db_path) as conn:
        await conn.executescript(schema_sql)
        await conn.commit()
