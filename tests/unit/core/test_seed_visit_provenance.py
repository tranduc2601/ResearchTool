import pytest
import ulid
from datetime import datetime, timezone

from research_tool.domain import SeedSource, SeedStatus
from research_tool.infrastructure.db.connection import apply_schema, get_connection
from research_tool.infrastructure.db.repositories.seed_repo import SeedRepo
from research_tool.infrastructure.db.repositories.visit_repo import VisitRepo

from research_tool.core.provenance import (
    build_seed_provenance,
    build_evidence_provenance,
    describe_chain,
)
from research_tool.core.seed_manager import SeedManager
from research_tool.core.visit_manager import VisitManager

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
async def seed_repo(setup_db):
    return SeedRepo(setup_db)

@pytest.fixture
async def visit_repo(setup_db):
    return VisitRepo(setup_db)

@pytest.mark.asyncio
async def test_provenance_helpers():
    # 1. build_seed_provenance(...) returns dict with run_id, root_seed_id
    seed_prov = build_seed_provenance(
        run_id="run-1",
        root_seed_id="root-1",
        expansion_reason="test",
    )
    assert seed_prov["run_id"] == "run-1"
    assert seed_prov["root_seed_id"] == "root-1"
    assert seed_prov["expansion_reason"] == "test"

    # 2. describe_chain({}) returns a string (non-empty)
    desc = describe_chain(seed_prov)
    assert isinstance(desc, str)
    assert len(desc) > 0
    assert "root-1" in desc

    empty_desc = describe_chain({})
    assert empty_desc == "Unknown chain"

@pytest.mark.asyncio
async def test_seed_manager(seed_repo, run_id):
    manager = SeedManager(run_id=run_id, seed_repo=seed_repo)

    # 3. create_seed("bàn làm việc", SeedSource.USER) -> is_new == True
    seed1, is_new1 = await manager.create_seed("bàn làm việc", SeedSource.USER)
    assert is_new1 is True
    assert seed1.text == "bàn làm việc"
    assert seed1.status == SeedStatus.PENDING

    # 4. Same text again -> is_new == False, same seed_id returned
    seed2, is_new2 = await manager.create_seed("bàn làm việc", SeedSource.USER)
    assert is_new2 is False
    assert seed2.seed_id == seed1.seed_id

    # 5. Text normalization: "  Bàn làm VIỆC  " deduplicates with "bàn làm việc"
    seed3, is_new3 = await manager.create_seed("  Bàn làm VIỆC  ", SeedSource.USER)
    assert is_new3 is False
    assert seed3.seed_id == seed1.seed_id

    # 6. activate(seed_id) -> seed status becomes ACTIVE
    await manager.activate(seed1.seed_id)
    pending = await manager.list_pending()
    assert len(pending) == 0  # no pending seeds left
    db_seed = await seed_repo.get_by_text_and_run("bàn làm việc", run_id)
    assert db_seed.status == SeedStatus.ACTIVE

    # 7. exhaust(seed_id) -> seed status becomes EXHAUSTED
    await manager.exhaust(seed1.seed_id)
    db_seed = await seed_repo.get_by_text_and_run("bàn làm việc", run_id)
    assert db_seed.status == SeedStatus.EXHAUSTED

    # 8. list_pending() returns seeds with PENDING status only
    await manager.create_seed("pending seed", SeedSource.USER)
    pending_list = await manager.list_pending()
    assert len(pending_list) == 1
    assert pending_list[0].text == "pending seed"

@pytest.mark.asyncio
async def test_visit_manager(visit_repo, run_id):
    manager = VisitManager(run_id=run_id, visit_repo=visit_repo, max_revisits=2)

    # 9. record_visit(...) -> record created
    visit1 = await manager.record_visit(platform="shopee", url="https://shopee.vn/p/123")
    assert visit1.url == "https://shopee.vn/p/123"

    # 10. is_visited(url="...") -> True after recording
    assert await manager.is_visited(url="https://shopee.vn/p/123") is True

    # 11. is_visited(url="https://other.com") -> False
    assert await manager.is_visited(url="https://other.com") is False

    # 12. should_revisit(url=..., reason="new seed found") -> True (revisit_count < max)
    should = await manager.should_revisit(url="https://shopee.vn/p/123", reason="new seed found")
    assert should is True

    # 13. record_revisit(visit_id, reason, sought) increments count
    await manager.record_revisit(visit1.visit_id, reason="new seed found", sought="info")
    
    # Still should revisit (count = 1, max = 2)
    assert await manager.should_revisit(url="https://shopee.vn/p/123", reason="another") is True
    await manager.record_revisit(visit1.visit_id, reason="another", sought="more info")

    # 14. After max_revisits (2), should_revisit returns False
    assert await manager.should_revisit(url="https://shopee.vn/p/123", reason="yet another") is False

    # 15. should_revisit(reason=None) returns False immediately
    assert await manager.should_revisit(url="https://shopee.vn/p/123", reason=None) is False
