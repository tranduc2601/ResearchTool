"""Unit tests for domain models: RunSession, Seed, FrontierItem, FrontierScore, GraphNode, GraphEdge, and enums."""

from datetime import UTC, datetime

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
)


def test_run_session_defaults():
    session = RunSession(run_id="run-1", goal_text="Find ergonomic chair")

    assert session.run_id == "run-1"
    assert session.goal_text == "Find ergonomic chair"
    assert session.status == RunStatus.RUNNING
    assert session.time_end is None
    assert session.stop_conditions == []
    assert session.user_profile_id is None
    assert isinstance(session.created_at, datetime)
    assert session.created_at.tzinfo == UTC
    assert isinstance(session.updated_at, datetime)
    assert session.updated_at.tzinfo == UTC


def test_run_status_enum_string_serialization():
    assert RunStatus.RUNNING == "RUNNING"
    assert RunStatus.PAUSED == "PAUSED"
    assert RunStatus.DONE == "DONE"
    assert RunStatus.FAILED == "FAILED"
    assert RunStatus.RUNNING.value == "RUNNING"


def test_seed_defaults():
    seed = Seed(
        seed_id="seed-1",
        run_id="run-1",
        text="ergonomic chair",
        source=SeedSource.USER,
    )

    assert seed.seed_id == "seed-1"
    assert seed.run_id == "run-1"
    assert seed.text == "ergonomic chair"
    assert seed.source == SeedSource.USER
    assert seed.status == SeedStatus.PENDING
    assert seed.parent_seed_id is None
    assert seed.parent_entity_id is None
    assert seed.parent_evidence_id is None
    assert seed.expansion_reason is None
    assert seed.expansion_depth == 0
    assert seed.provenance is None
    assert isinstance(seed.created_at, datetime)
    assert seed.created_at.tzinfo == UTC


def test_seed_source_all_cases():
    expected = {
        "USER",
        "COMMENT",
        "REVIEW",
        "RECOMMENDATION",
        "SOCIAL",
        "SEARCH",
        "INFERRED",
    }
    actual = {s.value for s in SeedSource}
    assert actual == expected
    assert len(SeedSource) == 7


def test_frontier_score_compute_typical():
    score = FrontierScore(
        mention_score=0.8,
        seed_similarity=0.6,
        source_diversity=0.5,
        novelty=0.7,
        unexplored_bonus=0.4,
        depth_penalty=0.1,
    )
    computed = score.compute()
    assert 0.0 <= computed <= 1.0
    expected = (
        0.35 * 0.8
        + 0.25 * 0.6
        + 0.20 * 0.5
        + 0.10 * 0.7
        + 0.10 * 0.4
        - 0.20 * 0.1
    )
    assert abs(computed - expected) < 1e-9


def test_frontier_score_compute_all_zero():
    score = FrontierScore()
    assert score.compute() == 0.0


def test_frontier_score_compute_bounds_clamping():
    high_score = FrontierScore(
        mention_score=1.0,
        seed_similarity=1.0,
        source_diversity=1.0,
        novelty=1.0,
        unexplored_bonus=1.0,
        depth_penalty=0.0,
    )
    assert high_score.compute() == 1.0

    penalty_heavy = FrontierScore(
        mention_score=0.0,
        seed_similarity=0.0,
        source_diversity=0.0,
        novelty=0.0,
        unexplored_bonus=0.0,
        depth_penalty=1.0,
    )
    assert penalty_heavy.compute() == 0.0


def test_frontier_item_defaults():
    item = FrontierItem(frontier_id="front-1", run_id="run-1")

    assert item.frontier_id == "front-1"
    assert item.run_id == "run-1"
    assert item.seed_id is None
    assert item.entity_id is None
    assert item.priority_score == 0.0
    assert item.score_components is None
    assert item.status == FrontierStatus.PENDING
    assert isinstance(item.created_at, datetime)
    assert item.created_at.tzinfo == UTC
    assert isinstance(item.updated_at, datetime)
    assert item.updated_at.tzinfo == UTC


def test_graph_node_and_edge_instantiation():
    node = GraphNode(
        node_id="node-1",
        run_id="run-1",
        node_type=NodeType.SEED,
        label="Ergonomic Chair",
        metadata={"category": "furniture"},
    )
    assert node.node_id == "node-1"
    assert node.run_id == "run-1"
    assert node.node_type == NodeType.SEED
    assert node.label == "Ergonomic Chair"
    assert node.metadata == {"category": "furniture"}
    assert isinstance(node.created_at, datetime)
    assert node.created_at.tzinfo == UTC

    edge = GraphEdge(
        edge_id="edge-1",
        run_id="run-1",
        from_node_id="node-1",
        to_node_id="node-2",
        relation=RelationType.DISCOVERED_FROM,
        evidence={"text": "found in review", "url": "https://example.com"},
    )
    assert edge.edge_id == "edge-1"
    assert edge.run_id == "run-1"
    assert edge.from_node_id == "node-1"
    assert edge.to_node_id == "node-2"
    assert edge.relation == RelationType.DISCOVERED_FROM
    assert edge.evidence == {"text": "found in review", "url": "https://example.com"}
    assert isinstance(edge.created_at, datetime)
    assert edge.created_at.tzinfo == UTC


def test_relation_type_probably_same_exists():
    assert RelationType.PROBABLY_SAME == "PROBABLY_SAME"
    assert RelationType.PROBABLY_SAME in RelationType


def test_all_enums_are_str_subclasses():
    enums_to_test = [
        StopCondition,
        RunStatus,
        SeedSource,
        SeedStatus,
        FrontierStatus,
        NodeType,
        RelationType,
    ]
    for enum_cls in enums_to_test:
        for member in enum_cls:
            assert isinstance(member, str), f"{member} in {enum_cls} is not str instance"
            assert isinstance(member.value, str), f"{member.value} in {enum_cls} is not str"
            assert issubclass(enum_cls, str), f"{enum_cls} is not subclass of str"
