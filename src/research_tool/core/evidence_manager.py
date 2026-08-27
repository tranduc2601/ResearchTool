"""Evidence collection and tracking manager."""
import structlog
import ulid
from datetime import datetime, timezone
from research_tool.domain import Evidence, EvidenceType, EvidenceTheme
from research_tool.infrastructure.db.repositories.evidence_repo import EvidenceRepo
from research_tool.infrastructure.db.repositories.entity_repo import EntityRepo
from research_tool.infrastructure.file_storage import FileStorage
from research_tool.core.provenance import build_evidence_provenance
from research_tool.core.yield_tracker import YieldTracker

logger = structlog.get_logger()

class EvidenceManager:
    """
    Manages evidence discovery, persistence, and thematic aggregation.
    """

    def __init__(
        self,
        run_id: str,
        evidence_repo: EvidenceRepo,
        entity_repo: EntityRepo,
        file_storage: FileStorage,
        yield_tracker: YieldTracker,
    ):
        self.run_id = run_id
        self._repo = evidence_repo
        self._entity_repo = entity_repo
        self._storage = file_storage
        self._yield_tracker = yield_tracker

    async def add_evidence(
        self,
        entity_id: str | None,
        evidence_type: EvidenceType,
        raw_text: str | None,
        source_platform: str,
        source_url: str | None,
        root_seed_id: str,
        parent_seed_id: str | None = None,
        direct_url: str | None = None,
        parent_url: str | None = None,
        screenshot_bytes: bytes | None = None,
        confidence: float = 1.0,
        discovery_chain: list[dict] | None = None,
    ) -> Evidence:
        """Create and persist a new evidence record."""
        evidence_id = ulid.new().str
        
        screenshot_path = None
        if screenshot_bytes:
            filename = f"evidence_{evidence_id}"
            screenshot_path_obj = await self._storage.save_screenshot(screenshot_bytes, filename)
            screenshot_path = str(screenshot_path_obj)

        provenance = build_evidence_provenance(
            run_id=self.run_id,
            root_seed_id=root_seed_id,
            source_entity_id=entity_id,
            parent_seed_id=parent_seed_id,
            discovery_chain=discovery_chain,
        )

        evidence = Evidence(
            evidence_id=evidence_id,
            run_id=self.run_id,
            entity_id=entity_id,
            evidence_type=evidence_type,
            raw_text=raw_text,
            source_platform=source_platform,
            source_url=source_url,
            direct_url=direct_url,
            parent_url=parent_url,
            screenshot_path=screenshot_path,
            confidence=confidence,
            provenance=provenance,
            captured_at=datetime.now(timezone.utc),
        )

        created = await self._repo.create(evidence)
        self._yield_tracker.record_evidence()
        
        # Export as JSON for later LLM analysis
        try:
            from research_tool.infrastructure.serialization import to_json
            import json
            data = json.loads(to_json(created))
            await self._storage.save_evidence_json(evidence_id, data)
        except Exception as e:
            logger.warning("evidence_export_failed", evidence_id=evidence_id, error=str(e))

        logger.info("evidence_added", evidence_id=evidence_id, type=evidence_type.value)
        return created

    async def add_theme(
        self,
        entity_id: str,
        theme_label: str,
        sample_ids: list[str] | None = None,
    ) -> EvidenceTheme:
        """Record or update a recurring theme (e.g., 'Pin yếu')."""
        theme_id = ulid.new().str
        theme = EvidenceTheme(
            theme_id=theme_id,
            entity_id=entity_id,
            theme_label=theme_label,
            frequency=1,
            sample_evidence_ids=sample_ids or [],
            updated_at=datetime.now(timezone.utc),
        )
        return await self._repo.upsert_theme(theme)

    async def list_for_entity(self, entity_id: str) -> list[Evidence]:
        """List all evidence for an entity."""
        return await self._repo.list_by_entity(entity_id)
