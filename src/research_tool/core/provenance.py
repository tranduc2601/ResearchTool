"""Provenance chain helpers — pure functions, no I/O."""

from research_tool.domain import Seed, Evidence, Entity

def build_seed_provenance(
    run_id: str,
    root_seed_id: str,
    parent_seed_id: str | None = None,
    parent_entity_id: str | None = None,
    parent_evidence_id: str | None = None,
    expansion_reason: str | None = None,
) -> dict:
    """Build a provenance dict for a new seed. Returns JSON-serializable dict."""
    return {
        "run_id": run_id,
        "root_seed_id": root_seed_id,
        "parent_seed_id": parent_seed_id,
        "parent_entity_id": parent_entity_id,
        "parent_evidence_id": parent_evidence_id,
        "expansion_reason": expansion_reason,
    }

def build_evidence_provenance(
    run_id: str,
    root_seed_id: str,
    source_entity_id: str | None = None,
    parent_seed_id: str | None = None,
    discovery_chain: list[dict] | None = None,
) -> dict:
    """Build a provenance dict for an evidence record."""
    return {
        "run_id": run_id,
        "root_seed_id": root_seed_id,
        "source_entity_id": source_entity_id,
        "parent_seed_id": parent_seed_id,
        "discovery_chain": discovery_chain or [],
    }

def describe_chain(provenance: dict) -> str:
    """
    Return a human-readable description of the provenance chain.
    Example: "User seed 'bàn làm việc' → Product A → Comment #184 → Seed 'T10 Pro'"
    Used for logging and audit.
    """
    # Simply joining parts or creating a descriptive text based on what is not None
    # For now, just a generic string representation based on keys
    parts = []
    
    if "root_seed_id" in provenance:
        parts.append(f"Root Seed: {provenance['root_seed_id']}")
    
    if provenance.get("parent_seed_id"):
        parts.append(f"Parent Seed: {provenance['parent_seed_id']}")
        
    if provenance.get("parent_entity_id"):
        parts.append(f"Entity: {provenance['parent_entity_id']}")
        
    if provenance.get("source_entity_id"):
        parts.append(f"Entity: {provenance['source_entity_id']}")
        
    if provenance.get("parent_evidence_id"):
        parts.append(f"Evidence: {provenance['parent_evidence_id']}")
        
    if provenance.get("expansion_reason"):
        parts.append(f"Reason: {provenance['expansion_reason']}")
        
    if provenance.get("discovery_chain"):
        chain = provenance["discovery_chain"]
        parts.append(f"Chain ({len(chain)} steps)")

    if not parts:
        return "Unknown chain"
        
    return " → ".join(parts)
