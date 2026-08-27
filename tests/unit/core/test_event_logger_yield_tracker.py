"""Tests for EventLogger and YieldTracker."""

import pytest
import pytest_asyncio
import json
from pathlib import Path

from research_tool.core import EventLogger, YieldTracker
from research_tool.domain import EventType, EventActor
from research_tool.infrastructure.db.repositories.event_repo import EventRepo
from research_tool.infrastructure.file_storage import FileStorage
from research_tool.infrastructure.db.connection import apply_schema


@pytest_asyncio.fixture
async def db_path(tmp_path: Path):
    from research_tool.infrastructure.db.connection import get_connection
    db_file = tmp_path / "test.db"
    await apply_schema(db_file)
    async with get_connection(db_file) as conn:
        await conn.execute(
            "INSERT INTO runs (run_id, goal_text, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("test-run-123", "test goal", "RUNNING", "2026-08-27T00:00:00Z", "2026-08-27T00:00:00Z")
        )
        await conn.commit()
    return db_file


@pytest.fixture
def run_id() -> str:
    return "test-run-123"


@pytest.fixture
def event_repo(db_path: Path) -> EventRepo:
    return EventRepo(db_path)


@pytest.fixture
def file_storage(tmp_path: Path, run_id: str) -> FileStorage:
    return FileStorage(tmp_path / run_id)


@pytest.fixture
def event_logger(run_id: str, event_repo: EventRepo, file_storage: FileStorage) -> EventLogger:
    return EventLogger(run_id=run_id, event_repo=event_repo, file_storage=file_storage)


@pytest.mark.asyncio
async def test_event_logger_log_creates_and_returns_event(event_logger: EventLogger):
    event = await event_logger.log(EventType.SEARCH, detail={"q": "foo"})
    assert event.event_type == EventType.SEARCH
    assert event.detail == {"q": "foo"}
    assert event.actor == EventActor.AGENT


@pytest.mark.asyncio
async def test_event_logger_log_persists_to_db(event_logger: EventLogger):
    event = await event_logger.log(EventType.SEED_DISCOVERED)
    recent = await event_logger.recent(1)
    assert len(recent) == 1
    assert recent[0].event_id == event.event_id
    assert recent[0].event_type == EventType.SEED_DISCOVERED


@pytest.mark.asyncio
async def test_event_logger_writes_to_jsonl(event_logger: EventLogger, file_storage: FileStorage):
    await event_logger.log(EventType.RUN_START)
    
    jsonl_path = file_storage.events_log_path
    assert jsonl_path.exists()
    lines = jsonl_path.read_text().strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event_type"] == EventType.RUN_START.value


@pytest.mark.asyncio
async def test_event_logger_two_calls_two_lines(event_logger: EventLogger, file_storage: FileStorage):
    await event_logger.log(EventType.SEARCH)
    await event_logger.log(EventType.NAVIGATE)
    
    jsonl_path = file_storage.events_log_path
    lines = jsonl_path.read_text().strip().split("\n")
    assert len(lines) == 2


@pytest.mark.asyncio
async def test_event_logger_recent_limits_output(event_logger: EventLogger):
    for _ in range(7):
        await event_logger.log(EventType.SEARCH)
    
    recent = await event_logger.recent(5)
    assert len(recent) == 5


def test_yield_tracker_new_tracker():
    tracker = YieldTracker()
    assert tracker.current_status() == "LOW_YIELD"


def test_yield_tracker_record_candidate():
    tracker = YieldTracker()
    tracker.record_candidate()
    assert tracker._current.new_candidates == 1


def test_yield_tracker_record_evidence():
    tracker = YieldTracker()
    tracker.record_evidence()
    assert tracker._current.new_evidence == 1


def test_yield_tracker_snapshot_contains_status():
    tracker = YieldTracker()
    tracker.record_candidate()
    snap = tracker.snapshot()
    assert "status" in snap
    assert snap["status"] == "LOW_YIELD"
    assert snap["new_candidates"] == 1


def test_yield_tracker_record_candidate_twice():
    tracker = YieldTracker()
    tracker.record_candidate()
    tracker.record_candidate()
    assert tracker._current.new_candidates == 2


def test_yield_tracker_consecutive_low_starts_at_zero():
    tracker = YieldTracker()
    assert tracker._consecutive_low == 0


def test_yield_tracker_low_yield_status():
    tracker = YieldTracker(low_yield_candidates=10)
    assert tracker.current_status() == "LOW_YIELD"


def test_yield_tracker_snapshot_reflects_recorded_count():
    tracker = YieldTracker()
    for _ in range(3):
        tracker.record_candidate()
    assert tracker.snapshot()["new_candidates"] == 3
