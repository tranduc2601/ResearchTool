import pytest
import ulid
from datetime import datetime, timezone

from research_tool.domain import FrontierStatus
from research_tool.infrastructure.db.connection import apply_schema, get_connection
from research_tool.infrastructure.db.repositories.frontier_repo import FrontierRepo
from research_tool.core.frontier_manager import FrontierManager

@pytest.fixture
def run_id():
    return ulid.new().str

@pytest.fixture
async def setup_db(tmp_path, run_id):
    db_file = tmp_path / "test.db"
    await apply_schema(db_file)
    
    # Insert a fake run to satisfy foreign key constraints
    async with get_connection(db_file) as conn:
        now = datetime.now(timezone.utc).isoformat()
        await conn.execute(
            """
            INSERT INTO runs (run_id, goal_text, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, "test goal", "RUNNING", now, now)
        )
        await conn.commit()
        
    return db_file

@pytest.fixture
async def frontier_repo(setup_db):
    return FrontierRepo(setup_db)

@pytest.mark.asyncio
async def test_add_seed(frontier_repo, run_id):
    manager = FrontierManager(run_id=run_id, frontier_repo=frontier_repo)
    item = await manager.add_seed(
        seed_id="test-seed-1",
        mention_confidence=0.8,
        seed_similarity=0.9
    )
    assert item.seed_id == "test-seed-1"
    assert item.entity_id is None
    assert item.status == FrontierStatus.PENDING
    assert item.priority_score > 0
    assert item.score_components.mention_confidence == 0.8
    assert item.score_components.seed_similarity == 0.9

@pytest.mark.asyncio
async def test_add_entity(frontier_repo, run_id):
    manager = FrontierManager(run_id=run_id, frontier_repo=frontier_repo)
    item = await manager.add_entity(
        entity_id="test-entity-1",
        unexplored_bonus=0.7
    )
    assert item.entity_id == "test-entity-1"
    assert item.seed_id is None
    assert item.status == FrontierStatus.PENDING
    assert item.priority_score > 0
    assert item.score_components.unexplored_bonus == 0.7

@pytest.mark.asyncio
async def test_pop_next(frontier_repo, run_id):
    manager = FrontierManager(run_id=run_id, frontier_repo=frontier_repo)
    
    # Add two items with different scores
    await manager.add_seed(seed_id="seed-low", mention_confidence=0.1, novelty=0.1) # low score
    await manager.add_seed(seed_id="seed-high", mention_confidence=0.9, novelty=0.9) # high score
    
    popped = await manager.pop_next()
    assert popped is not None
    assert popped.seed_id == "seed-high"
    assert popped.status == FrontierStatus.IN_PROGRESS
    
    popped2 = await manager.pop_next()
    assert popped2 is not None
    assert popped2.seed_id == "seed-low"
    assert popped2.status == FrontierStatus.IN_PROGRESS
    
    popped3 = await manager.pop_next()
    assert popped3 is None

@pytest.mark.asyncio
async def test_mark_completed_and_failed(frontier_repo, run_id):
    manager = FrontierManager(run_id=run_id, frontier_repo=frontier_repo)
    item = await manager.add_seed(seed_id="test-status")
    
    await manager.mark_completed(item.frontier_id)
    db_item = await frontier_repo.get_by_id(item.frontier_id)
    assert db_item.status == FrontierStatus.COMPLETED
    
    await manager.mark_failed(item.frontier_id)
    db_item = await frontier_repo.get_by_id(item.frontier_id)
    assert db_item.status == FrontierStatus.FAILED

@pytest.mark.asyncio
async def test_count_pending(frontier_repo, run_id):
    manager = FrontierManager(run_id=run_id, frontier_repo=frontier_repo)
    
    assert await manager.count_pending() == 0
    
    await manager.add_seed(seed_id="seed-1")
    await manager.add_entity(entity_id="ent-1")
    
    assert await manager.count_pending() == 2
    
    # popping one item changes it to IN_PROGRESS
    await manager.pop_next()
    assert await manager.count_pending() == 1
