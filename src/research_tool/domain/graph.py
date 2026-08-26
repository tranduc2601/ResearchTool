"""GraphNode, GraphEdge, and related discovery graph types."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class NodeType(StrEnum):
    """Type of entity/node in the discovery graph."""

    SEED = "SEED"
    ENTITY = "ENTITY"
    EVIDENCE = "EVIDENCE"
    SEARCH = "SEARCH"
    URL = "URL"


class RelationType(StrEnum):
    """Type of relationship/edge in the discovery graph."""

    DISCOVERED_FROM = "DISCOVERED_FROM"
    MENTIONED_IN = "MENTIONED_IN"
    SAME_AS = "SAME_AS"
    PROBABLY_SAME = "PROBABLY_SAME"
    RELATED_TO = "RELATED_TO"
    OEM_OF = "OEM_OF"
    EXPANDS = "EXPANDS"


@dataclass
class GraphNode:
    """A node in the discovery graph."""

    node_id: str
    run_id: str
    node_type: NodeType
    label: str
    metadata: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class GraphEdge:
    """A directed edge connecting two nodes in the discovery graph."""

    edge_id: str
    run_id: str
    from_node_id: str
    to_node_id: str
    relation: RelationType
    evidence: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
