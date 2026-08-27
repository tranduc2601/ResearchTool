"""Exploration knowledge graph manager."""
import structlog
import ulid
from datetime import datetime, timezone
from research_tool.domain import GraphNode, GraphEdge, NodeType, RelationType
from research_tool.infrastructure.db.repositories.graph_repo import GraphRepo

logger = structlog.get_logger()

class ExplorationGraph:
    """
    Manages the logical discovery graph.
    
    Nodes represent domains objects (seeds, entities, visits).
    Edges represent discovery paths (e.g., SEED -> GENERATED -> ENTITY).
    Used for provenance and avoiding endless loops.
    """

    def __init__(self, run_id: str, graph_repo: GraphRepo):
        self.run_id = run_id
        self._repo = graph_repo

    async def get_or_create_node(
        self,
        node_id: str,
        node_type: NodeType,
        label: str,
        metadata: dict | None = None
    ) -> GraphNode:
        """Get existing node or create a new one."""
        node = await self._repo.get_node(node_id)
        if node:
            return node
            
        node = GraphNode(
            node_id=node_id,
            run_id=self.run_id,
            node_type=node_type,
            label=label,
            metadata=metadata,
            created_at=datetime.now(timezone.utc),
        )
        created = await self._repo.create_node(node)
        logger.debug("graph_node_created", node_id=node_id, node_type=node_type.value)
        return created

    async def add_edge(
        self,
        from_node_id: str,
        to_node_id: str,
        relation: RelationType,
        evidence: str | None = None,
    ) -> GraphEdge:
        """Create an edge between two existing nodes."""
        edge = GraphEdge(
            edge_id=ulid.new().str,
            run_id=self.run_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            relation=relation,
            evidence=evidence,
            created_at=datetime.now(timezone.utc),
        )
        created = await self._repo.create_edge(edge)
        logger.debug("graph_edge_created", from_node=from_node_id, to_node=to_node_id, relation=relation.value)
        return created

    async def get_ancestry(self, node_id: str, max_depth: int = 10) -> list[GraphEdge]:
        """Return the backward path of discovery for a node."""
        return await self._repo.get_ancestry(node_id, max_depth)
