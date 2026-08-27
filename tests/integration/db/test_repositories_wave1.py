"""Integration tests for Wave 1 repositories: Run, Seed, Frontier, Graph, Visit."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import ulid

from research_tool.domain import (
    FrontierItem,
    FrontierScore,
    FrontierStatus,
    GraphEdge,
    GraphNode,
    NodeType,
    RelationType,
    RunSession,
    RunStatus,
    Seed,
    SeedSource,
    SeedStatus,
    StopCondition,
    VisitRecord,
)
from research_tool.infrastructure.db.connection import apply_schema
from research_tool.infrastructure.db.repositories import (
    FrontierRepo,
    GraphRepo,
    RunRepo,
    SeedRepo,
    VisitRepo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def db(tmp_path: Path) -> Path:
    """Create a fresh SQLite DB with schema applied."""
    db_path = tmp_path / "test.sqlite3"
    await apply_schema(db_path)
    return db_path


def make_run(**kwargs) -> RunSession:
    defaults = dict(
        run_id=ulid.new().str,
        goal_text="Find the best mechanical keyboard",
        status=RunStatus.RUNNING,
        stop_conditions=[StopCondition.FRONTIER_EXHAUSTED],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return RunSession(**defaults)


def make_seed(run_id: str, **kwargs) -> Seed:
    defaults = dict(
        seed_id=ulid.new().str,
        run_id=run_id,
        text="mechanical keyboard",
        source=SeedSource.USER,
        status=SeedStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return Seed(**defaults)


def make_frontier(run_id: str, priority: float = 0.5, **kwargs) -> FrontierItem:
    defaults = dict(
        frontier_id=ulid.new().str,
        run_id=run_id,
        priority_score=priority,
        status=FrontierStatus.PENDING,
        score_components=FrontierScore(mention_score=0.8, total=priority),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return FrontierItem(**defaults)


def make_node(run_id: str, label: str = "keyboard", **kwargs) -> GraphNode:
    defaults = dict(
        node_id=ulid.new().str,
        run_id=run_id,
        node_type=NodeType.SEED,
        label=label,
        created_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return GraphNode(**defaults)


def make_edge(run_id: str, from_id: str, to_id: str, **kwargs) -> GraphEdge:
    defaults = dict(
        edge_id=ulid.new().str,
        run_id=run_id,
        from_node_id=from_id,
        to_node_id=to_id,
        relation=RelationType.DISCOVERED_FROM,
        created_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return GraphEdge(**defaults)


def make_visit(run_id: str, url: str = "https://example.com", **kwargs) -> VisitRecord:
    defaults = dict(
        visit_id=ulid.new().str,
        run_id=run_id,
        platform="web",
        url=url,
        visited_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return VisitRecord(**defaults)


# ---------------------------------------------------------------------------
# RunRepo tests
# ---------------------------------------------------------------------------


async def test_run_create_and_get(db: Path) -> None:
    """RunRepo.create then get returns the same run."""
    repo = RunRepo(db)
    run = make_run()
    await repo.create(run)

    fetched = await repo.get(run.run_id)
    assert fetched is not None
    assert fetched.run_id == run.run_id
    assert fetched.goal_text == run.goal_text
    assert fetched.status == RunStatus.RUNNING
    assert StopCondition.FRONTIER_EXHAUSTED in fetched.stop_conditions


async def test_run_get_nonexistent_returns_none(db: Path) -> None:
    repo = RunRepo(db)
    assert await repo.get("nonexistent") is None


async def test_run_update_status(db: Path) -> None:
    """RunRepo.update_status changes the status."""
    repo = RunRepo(db)
    run = make_run()
    await repo.create(run)

    await repo.update_status(run.run_id, RunStatus.DONE)
    fetched = await repo.get(run.run_id)
    assert fetched is not None
    assert fetched.status == RunStatus.DONE


async def test_run_list_recent(db: Path) -> None:
    repo = RunRepo(db)
    for _ in range(3):
        await repo.create(make_run())

    results = await repo.list_recent(limit=2)
    assert len(results) == 2


# ---------------------------------------------------------------------------
# SeedRepo tests
# ---------------------------------------------------------------------------


async def test_seed_create_and_list_by_run(db: Path) -> None:
    """SeedRepo.create then list_by_run returns the seed."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = SeedRepo(db)
    seed = make_seed(run.run_id)
    await repo.create(seed)

    seeds = await repo.list_by_run(run.run_id)
    assert len(seeds) == 1
    assert seeds[0].seed_id == seed.seed_id
    assert seeds[0].text == seed.text


async def test_seed_update_status_to_exhausted(db: Path) -> None:
    """SeedRepo.update_status to EXHAUSTED."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = SeedRepo(db)
    seed = make_seed(run.run_id)
    await repo.create(seed)

    await repo.update_status(seed.seed_id, SeedStatus.EXHAUSTED)
    fetched = await repo.get(seed.seed_id)
    assert fetched is not None
    assert fetched.status == SeedStatus.EXHAUSTED


async def test_seed_list_by_run_with_status_filter(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = SeedRepo(db)
    s1 = make_seed(run.run_id, text="alpha")
    s2 = make_seed(run.run_id, text="beta", status=SeedStatus.ACTIVE)
    await repo.create(s1)
    await repo.create(s2)

    pending = await repo.list_by_run(run.run_id, status=SeedStatus.PENDING)
    assert len(pending) == 1
    assert pending[0].seed_id == s1.seed_id


async def test_seed_get_by_text_and_run(db: Path) -> None:
    """SeedRepo.get_by_text_and_run finds by text."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = SeedRepo(db)
    seed = make_seed(run.run_id, text="unique keyboard term")
    await repo.create(seed)

    found = await repo.get_by_text_and_run("unique keyboard term", run.run_id)
    assert found is not None
    assert found.seed_id == seed.seed_id

    not_found = await repo.get_by_text_and_run("nonexistent", run.run_id)
    assert not_found is None


# ---------------------------------------------------------------------------
# FrontierRepo tests
# ---------------------------------------------------------------------------


async def test_frontier_create_and_list_pending(db: Path) -> None:
    """FrontierRepo.create then list_pending returns the item."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = FrontierRepo(db)
    item = make_frontier(run.run_id, priority=0.7)
    await repo.create(item)

    pending = await repo.list_pending(run.run_id)
    assert len(pending) == 1
    assert pending[0].frontier_id == item.frontier_id
    assert pending[0].priority_score == pytest.approx(0.7)


async def test_frontier_pop_next_returns_highest_priority_and_marks_in_progress(
    db: Path,
) -> None:
    """FrontierRepo.pop_next returns highest-priority item and marks it IN_PROGRESS."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = FrontierRepo(db)
    low = make_frontier(run.run_id, priority=0.2)
    high = make_frontier(run.run_id, priority=0.9)
    await repo.create(low)
    await repo.create(high)

    popped = await repo.pop_next(run.run_id)
    assert popped is not None
    assert popped.frontier_id == high.frontier_id
    assert popped.status == FrontierStatus.IN_PROGRESS

    # Verify it's no longer PENDING in DB
    pending = await repo.list_pending(run.run_id)
    assert len(pending) == 1
    assert pending[0].frontier_id == low.frontier_id


async def test_frontier_pop_next_empty_returns_none(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = FrontierRepo(db)
    result = await repo.pop_next(run.run_id)
    assert result is None


async def test_frontier_count_by_status(db: Path) -> None:
    """FrontierRepo.count_by_status returns correct count."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = FrontierRepo(db)
    for _ in range(3):
        await repo.create(make_frontier(run.run_id))
    item_done = make_frontier(run.run_id, status=FrontierStatus.DONE)
    await repo.create(item_done)

    assert await repo.count_by_status(run.run_id, FrontierStatus.PENDING) == 3
    assert await repo.count_by_status(run.run_id, FrontierStatus.DONE) == 1
    assert await repo.count_by_status(run.run_id, FrontierStatus.IN_PROGRESS) == 0


async def test_frontier_update_status(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = FrontierRepo(db)
    item = make_frontier(run.run_id)
    await repo.create(item)

    await repo.update_status(item.frontier_id, FrontierStatus.SKIPPED)
    fetched = await repo.get(item.frontier_id)
    assert fetched is not None
    assert fetched.status == FrontierStatus.SKIPPED


async def test_frontier_score_components_roundtrip(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = FrontierRepo(db)
    score = FrontierScore(mention_score=0.9, seed_similarity=0.5, total=0.75)
    item = make_frontier(run.run_id, score_components=score)
    await repo.create(item)

    fetched = await repo.get(item.frontier_id)
    assert fetched is not None
    assert fetched.score_components is not None
    assert fetched.score_components.mention_score == pytest.approx(0.9)
    assert fetched.score_components.seed_similarity == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# GraphRepo tests
# ---------------------------------------------------------------------------


async def test_graph_create_node_and_get(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = GraphRepo(db)
    node = make_node(run.run_id, label="MX Keys")
    await repo.create_node(node)

    fetched = await repo.get_node(node.node_id)
    assert fetched is not None
    assert fetched.node_id == node.node_id
    assert fetched.label == "MX Keys"


async def test_graph_create_edge_and_get_edges_from(db: Path) -> None:
    """GraphRepo.create_node and create_edge then get_edges_from."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = GraphRepo(db)
    n1 = make_node(run.run_id, label="A")
    n2 = make_node(run.run_id, label="B")
    await repo.create_node(n1)
    await repo.create_node(n2)

    edge = make_edge(run.run_id, n1.node_id, n2.node_id)
    await repo.create_edge(edge)

    edges_from = await repo.get_edges_from(n1.node_id)
    assert len(edges_from) == 1
    assert edges_from[0].edge_id == edge.edge_id
    assert edges_from[0].from_node_id == n1.node_id
    assert edges_from[0].to_node_id == n2.node_id

    edges_to = await repo.get_edges_to(n2.node_id)
    assert len(edges_to) == 1
    assert edges_to[0].edge_id == edge.edge_id


async def test_graph_get_ancestry(db: Path) -> None:
    """GraphRepo.get_ancestry traces back N hops."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = GraphRepo(db)
    # Build chain: root → mid → leaf
    root = make_node(run.run_id, label="root")
    mid = make_node(run.run_id, label="mid")
    leaf = make_node(run.run_id, label="leaf")
    await repo.create_node(root)
    await repo.create_node(mid)
    await repo.create_node(leaf)

    e1 = make_edge(run.run_id, root.node_id, mid.node_id)
    e2 = make_edge(run.run_id, mid.node_id, leaf.node_id)
    await repo.create_edge(e1)
    await repo.create_edge(e2)

    # Ancestry of leaf should traverse back to root
    ancestry = await repo.get_ancestry(leaf.node_id, max_depth=5)
    edge_ids = {e.edge_id for e in ancestry}
    assert e1.edge_id in edge_ids
    assert e2.edge_id in edge_ids


async def test_graph_get_ancestry_respects_max_depth(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = GraphRepo(db)
    # Chain of 4: n0 → n1 → n2 → n3
    nodes = [make_node(run.run_id, label=f"n{i}") for i in range(4)]
    for n in nodes:
        await repo.create_node(n)
    edges = [
        make_edge(run.run_id, nodes[i].node_id, nodes[i + 1].node_id)
        for i in range(3)
    ]
    for e in edges:
        await repo.create_edge(e)

    # Start from n3, max_depth=1 should only find the immediate parent edge (n2→n3)
    ancestry = await repo.get_ancestry(nodes[3].node_id, max_depth=1)
    assert len(ancestry) == 1
    assert ancestry[0].from_node_id == nodes[2].node_id


# ---------------------------------------------------------------------------
# VisitRepo tests
# ---------------------------------------------------------------------------


async def test_visit_create_and_get_by_url(db: Path) -> None:
    """VisitRepo.create then get_by_url retrieves the record."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = VisitRepo(db)
    visit = make_visit(run.run_id, url="https://keyboards.example.com/tkl")
    await repo.create(visit)

    found = await repo.get_by_url("https://keyboards.example.com/tkl", run.run_id)
    assert found is not None
    assert found.visit_id == visit.visit_id
    assert found.platform == "web"


async def test_visit_get_by_url_returns_none_for_unknown(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = VisitRepo(db)
    result = await repo.get_by_url("https://not-visited.example.com", run.run_id)
    assert result is None


async def test_visit_is_visited_returns_true_for_known_url(db: Path) -> None:
    """VisitRepo.is_visited returns True for known URL."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = VisitRepo(db)
    visit = make_visit(run.run_id, url="https://visited.example.com")
    await repo.create(visit)

    assert await repo.is_visited("https://visited.example.com", None, run.run_id) is True
    assert await repo.is_visited("https://not-visited.example.com", None, run.run_id) is False


async def test_visit_is_visited_by_fingerprint(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = VisitRepo(db)
    visit = make_visit(run.run_id, content_fingerprint="fp_abc123")
    await repo.create(visit)

    assert await repo.is_visited(None, "fp_abc123", run.run_id) is True
    assert await repo.is_visited(None, "fp_unknown", run.run_id) is False


async def test_visit_is_visited_both_none_returns_false(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = VisitRepo(db)
    assert await repo.is_visited(None, None, run.run_id) is False


async def test_visit_increment_revisit(db: Path) -> None:
    """VisitRepo.increment_revisit increments count and stores reason."""
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = VisitRepo(db)
    visit = make_visit(run.run_id)
    await repo.create(visit)

    await repo.increment_revisit(visit.visit_id, reason="price check", sought="RGB keyboard")
    await repo.increment_revisit(visit.visit_id, reason="stock check", sought="TKL keyboard")

    found = await repo.get_by_url(visit.url, run.run_id)
    assert found is not None
    assert found.revisit_count == 2
    assert found.last_revisit_reason == "stock check"
    assert found.last_revisit_sought == "TKL keyboard"


async def test_visit_get_by_fingerprint(db: Path) -> None:
    run_repo = RunRepo(db)
    run = make_run()
    await run_repo.create(run)

    repo = VisitRepo(db)
    visit = make_visit(run.run_id, content_fingerprint="deadbeef")
    await repo.create(visit)

    found = await repo.get_by_fingerprint("deadbeef", run.run_id)
    assert found is not None
    assert found.visit_id == visit.visit_id

    not_found = await repo.get_by_fingerprint("unknown", run.run_id)
    assert not_found is None
