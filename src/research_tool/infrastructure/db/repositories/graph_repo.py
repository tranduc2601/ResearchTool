"""Repository for GraphNode and GraphEdge persistence."""

import json
from pathlib import Path

from research_tool.domain.graph import GraphEdge, GraphNode, NodeType, RelationType
from research_tool.infrastructure.db.connection import get_connection


class GraphRepo:
    """SQLite-backed repository for GraphNode and GraphEdge."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _node_to_row(node: GraphNode) -> tuple:
        return (
            node.node_id,
            node.run_id,
            node.node_type.value,
            node.label,
            json.dumps(node.metadata) if node.metadata is not None else None,
            node.created_at.isoformat(),
        )

    @staticmethod
    def _node_from_row(row) -> GraphNode:
        from datetime import datetime

        meta_raw = row["metadata"]
        return GraphNode(
            node_id=row["node_id"],
            run_id=row["run_id"],
            node_type=NodeType(row["node_type"]),
            label=row["label"],
            metadata=json.loads(meta_raw) if meta_raw else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _edge_to_row(edge: GraphEdge) -> tuple:
        return (
            edge.edge_id,
            edge.run_id,
            edge.from_node_id,
            edge.to_node_id,
            edge.relation.value,
            json.dumps(edge.evidence) if edge.evidence is not None else None,
            edge.created_at.isoformat(),
        )

    @staticmethod
    def _edge_from_row(row) -> GraphEdge:
        from datetime import datetime

        evidence_raw = row["evidence"]
        return GraphEdge(
            edge_id=row["edge_id"],
            run_id=row["run_id"],
            from_node_id=row["from_node"],
            to_node_id=row["to_node"],
            relation=RelationType(row["relation"]),
            evidence=json.loads(evidence_raw) if evidence_raw else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_node(self, node: GraphNode) -> GraphNode:
        """Insert a GraphNode row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO graph_nodes (node_id, run_id, node_type, label, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                self._node_to_row(node),
            )
            await conn.commit()
        return node

    async def create_edge(self, edge: GraphEdge) -> GraphEdge:
        """Insert a GraphEdge row and return it."""
        async with get_connection(self.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO graph_edges
                    (edge_id, run_id, from_node, to_node, relation, evidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._edge_to_row(edge),
            )
            await conn.commit()
        return edge

    async def get_node(self, node_id: str) -> GraphNode | None:
        """Fetch a GraphNode by ID, or None if not found."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM graph_nodes WHERE node_id = ?", (node_id,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return self._node_from_row(row)

    async def get_edges_from(self, node_id: str) -> list[GraphEdge]:
        """Return all outgoing edges from a node."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM graph_edges WHERE from_node = ?", (node_id,)
            )
            rows = await cursor.fetchall()
        return [self._edge_from_row(r) for r in rows]

    async def get_edges_to(self, node_id: str) -> list[GraphEdge]:
        """Return all incoming edges to a node."""
        async with get_connection(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM graph_edges WHERE to_node = ?", (node_id,)
            )
            rows = await cursor.fetchall()
        return [self._edge_from_row(r) for r in rows]

    async def get_ancestry(self, node_id: str, max_depth: int = 10) -> list[GraphEdge]:
        """Walk edges backwards (to_node → from_node) up to max_depth hops.

        Returns edges in BFS order from the given node upward.
        """
        visited_nodes: set[str] = {node_id}
        result: list[GraphEdge] = []
        frontier: list[str] = [node_id]

        for _ in range(max_depth):
            if not frontier:
                break
            next_frontier: list[str] = []
            async with get_connection(self.db_path) as conn:
                placeholders = ",".join("?" * len(frontier))
                cursor = await conn.execute(
                    f"SELECT * FROM graph_edges WHERE to_node IN ({placeholders})",
                    tuple(frontier),
                )
                rows = await cursor.fetchall()
            for row in rows:
                edge = self._edge_from_row(row)
                result.append(edge)
                if edge.from_node_id not in visited_nodes:
                    visited_nodes.add(edge.from_node_id)
                    next_frontier.append(edge.from_node_id)
            frontier = next_frontier

        return result
