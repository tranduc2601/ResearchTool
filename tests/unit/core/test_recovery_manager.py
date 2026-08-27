"""Tests for RecoveryManager."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone

from research_tool.core.recovery_manager import RecoveryManager
from research_tool.core.yield_tracker import YieldTracker
from research_tool.domain import CheckpointData, CheckpointTrigger, WorldState, PageType, AgentStatus, Confidence

# A simple fake repo for CheckpointRepo instead of needing a DB connection
class FakeCheckpointRepo:
    def __init__(self):
        self.checkpoints = []

    async def save(self, checkpoint: CheckpointData) -> CheckpointData:
        self.checkpoints.append(checkpoint)
        # sort by created_at desc
        self.checkpoints.sort(key=lambda x: x.created_at, reverse=True)
        return checkpoint

    async def get_latest(self, run_id: str) -> CheckpointData | None:
        for cp in self.checkpoints:
            if cp.run_id == run_id:
                return cp
        return None


@pytest.fixture
def fake_repo():
    return FakeCheckpointRepo()


@pytest.fixture
def yield_tracker():
    return YieldTracker()


@pytest.fixture
def run_id():
    return "test-run-123"


@pytest.fixture
def recovery_manager(run_id, fake_repo, yield_tracker):
    return RecoveryManager(
        run_id=run_id,
        checkpoint_repo=fake_repo,
        yield_tracker=yield_tracker,
    )


@pytest.fixture
def dummy_world_state(run_id):
    return WorldState(
        run_id=run_id,
        platform="TEST",
        app="APP",
        page_type=PageType.SEARCH_RESULT,
        confidence=Confidence.KNOWN,
        agent_status=AgentStatus.NORMAL,
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_create_checkpoint_saves_with_yield_snapshot(
    recovery_manager: RecoveryManager, dummy_world_state: WorldState, fake_repo: FakeCheckpointRepo, yield_tracker: YieldTracker
):
    yield_tracker.record_candidate()
    expected_snap = yield_tracker.snapshot()
    
    saved = await recovery_manager.create_checkpoint(
        world_state=dummy_world_state,
        trigger=CheckpointTrigger.SEARCH_DONE,
        frontier_snapshot=["url1", "url2"],
    )
    
    assert saved is not None
    assert saved.checkpoint_id is not None
    assert saved.run_id == "test-run-123"
    assert saved.world_state == dummy_world_state
    assert saved.trigger == CheckpointTrigger.SEARCH_DONE
    assert saved.frontier_snapshot == ["url1", "url2"]
    
    # Check yield snapshot is properly embedded
    assert saved.yield_snapshot == expected_snap
    assert saved.yield_snapshot["new_candidates"] == 1
    
    # Verify it was saved in repo
    assert len(fake_repo.checkpoints) == 1
    assert fake_repo.checkpoints[0].checkpoint_id == saved.checkpoint_id


@pytest.mark.asyncio
async def test_get_latest_checkpoint_returns_most_recent(
    recovery_manager: RecoveryManager, dummy_world_state: WorldState
):
    # Save a first one
    cp1 = await recovery_manager.create_checkpoint(
        world_state=dummy_world_state,
        trigger=CheckpointTrigger.SEARCH_DONE
    )
    
    # Save a second one later
    cp2 = await recovery_manager.create_checkpoint(
        world_state=dummy_world_state,
        trigger=CheckpointTrigger.PRODUCT_OPENED
    )
    
    loaded = await recovery_manager.get_latest_checkpoint()
    assert loaded is not None
    assert loaded.checkpoint_id == cp2.checkpoint_id
    assert loaded.trigger == CheckpointTrigger.PRODUCT_OPENED


@pytest.mark.asyncio
async def test_get_latest_checkpoint_returns_none_if_empty(
    recovery_manager: RecoveryManager
):
    loaded = await recovery_manager.get_latest_checkpoint()
    assert loaded is None
