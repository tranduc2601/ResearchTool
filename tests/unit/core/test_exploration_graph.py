import pytest
from unittest.mock import AsyncMock
from research_tool.core.exploration_graph import ExplorationGraph
from research_tool.domain import GraphNode, GraphEdge, NodeType, RelationType
from datetime import datetime, timezone

@pytest.fixture
def run_id():
    return "run-123"

@pytest.fixture
def repo():
    return AsyncMock()

@pytest.fixture
def graph(run_id, repo):
    return ExplorationGraph(run_id, repo)

@pytest.mark.asyncio
async def test_get_or_create_node_creates_if_missing(graph, repo, run_id):
    repo.get_node.return_value = None
    created_node = GraphNode(
        node_id="node-1",
        run_id=run_id,
        node_type=NodeType.SEED,
        label="Seed Node",
        created_at=datetime.now(timezone.utc)
    )
    repo.create_node.return_value = created_node

    result = await graph.get_or_create_node("node-1", NodeType.SEED, "Seed Node")

    assert result == created_node
    repo.get_node.assert_called_once_with("node-1")
    repo.create_node.assert_called_once()
    assert repo.create_node.call_args[0][0].node_id == "node-1"
    assert repo.create_node.call_args[0][0].node_type == NodeType.SEED
    assert repo.create_node.call_args[0][0].label == "Seed Node"

@pytest.mark.asyncio
async def test_get_or_create_node_returns_existing(graph, repo):
    existing_node = GraphNode(
        node_id="node-1",
        run_id="run-123",
        node_type=NodeType.SEED,
        label="Seed Node",
        created_at=datetime.now(timezone.utc)
    )
    repo.get_node.return_value = existing_node

    result = await graph.get_or_create_node("node-1", NodeType.SEED, "Seed Node")

    assert result == existing_node
    repo.get_node.assert_called_once_with("node-1")
    repo.create_node.assert_not_called()

@pytest.mark.asyncio
async def test_add_edge(graph, repo, run_id):
    edge = GraphEdge(
        edge_id="edge-1",
        run_id=run_id,
        from_node_id="node-1",
        to_node_id="node-2",
        relation=RelationType.DISCOVERED_FROM,
        created_at=datetime.now(timezone.utc)
    )
    repo.create_edge.return_value = edge

    result = await graph.add_edge("node-1", "node-2", RelationType.DISCOVERED_FROM, "evidence text")

    assert result == edge
    repo.create_edge.assert_called_once()
    called_edge = repo.create_edge.call_args[0][0]
    assert called_edge.from_node_id == "node-1"
    assert called_edge.to_node_id == "node-2"
    assert called_edge.relation == RelationType.DISCOVERED_FROM
    assert called_edge.evidence == "evidence text"

@pytest.mark.asyncio
async def test_get_ancestry(graph, repo):
    edges = [AsyncMock(), AsyncMock()]
    repo.get_ancestry.return_value = edges

    result = await graph.get_ancestry("node-1", 5)

    assert result == edges
    repo.get_ancestry.assert_called_once_with("node-1", 5)
