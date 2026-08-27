"""Seed lifecycle manager."""
import structlog
import ulid
from datetime import datetime, timezone

from research_tool.domain import Seed, SeedSource, SeedStatus
from research_tool.infrastructure.db.repositories.seed_repo import SeedRepo
from research_tool.core.provenance import build_seed_provenance

logger = structlog.get_logger()

class SeedManager:
    """
    Manages seed creation, deduplication, and status transitions.
    
    Dedup rule: a seed with the same normalized text already exists for
    the run → return existing seed (do not create duplicate).
    Text normalization: lowercase + strip whitespace.
    """

    def __init__(self, run_id: str, seed_repo: SeedRepo):
        self.run_id = run_id
        self._repo = seed_repo

    async def create_seed(
        self,
        text: str,
        source: SeedSource,
        parent_seed_id: str | None = None,
        parent_entity_id: str | None = None,
        parent_evidence_id: str | None = None,
        expansion_reason: str | None = None,
        expansion_depth: int = 0,
    ) -> tuple[Seed, bool]:
        """
        Create a new seed or return existing if duplicate.
        Returns (seed, is_new: bool).
        """
        normalized = text.strip().lower()
        existing = await self._repo.get_by_text_and_run(normalized, self.run_id)
        if existing:
            logger.debug("seed_already_exists", text=normalized)
            return existing, False

        provenance = build_seed_provenance(
            run_id=self.run_id,
            root_seed_id=parent_seed_id or "self",
            parent_seed_id=parent_seed_id,
            parent_entity_id=parent_entity_id,
            parent_evidence_id=parent_evidence_id,
            expansion_reason=expansion_reason,
        )
        seed = Seed(
            seed_id=ulid.new().str,
            run_id=self.run_id,
            text=normalized,
            source=source,
            status=SeedStatus.PENDING,
            parent_seed_id=parent_seed_id,
            parent_entity_id=parent_entity_id,
            parent_evidence_id=parent_evidence_id,
            expansion_reason=expansion_reason,
            expansion_depth=expansion_depth,
            provenance=provenance,
            created_at=datetime.now(timezone.utc),
        )
        created = await self._repo.create(seed)
        logger.info("seed_created", seed_id=created.seed_id, text=normalized, source=source.value)
        return created, True

    async def activate(self, seed_id: str) -> None:
        await self._repo.update_status(seed_id, SeedStatus.ACTIVE)

    async def exhaust(self, seed_id: str) -> None:
        await self._repo.update_status(seed_id, SeedStatus.EXHAUSTED)

    async def list_pending(self) -> list[Seed]:
        return await self._repo.list_by_run(self.run_id, status=SeedStatus.PENDING)
