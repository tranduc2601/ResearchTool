"""Visit tracking and revisit decision logic."""
import structlog
import ulid
from datetime import datetime, timezone

from research_tool.domain import VisitRecord
from research_tool.infrastructure.db.repositories.visit_repo import VisitRepo
from research_tool.infrastructure.serialization import fingerprint_text

logger = structlog.get_logger()

class VisitManager:
    """
    Tracks what the agent has visited and enforces revisit rules.

    Visited = URL match OR content fingerprint match for the same run.
    Revisit is allowed only when: a reason is provided AND revisit_count < max_revisits.
    """

    def __init__(
        self,
        run_id: str,
        visit_repo: VisitRepo,
        max_revisits: int = 3,
    ):
        self.run_id = run_id
        self._repo = visit_repo
        self.max_revisits = max_revisits

    async def is_visited(
        self,
        url: str | None = None,
        content_fingerprint: str | None = None,
    ) -> bool:
        """True if url or content_fingerprint matches an existing visit for this run."""
        return await self._repo.is_visited(url, content_fingerprint, self.run_id)

    async def record_visit(
        self,
        platform: str,
        url: str | None = None,
        entity_id: str | None = None,
        content: str | None = None,      # raw text to fingerprint
        screen_fingerprint: str | None = None,
    ) -> VisitRecord:
        """Record a new visit. Computes content_fingerprint if content is provided."""
        content_fp = fingerprint_text(content) if content else None
        record = VisitRecord(
            visit_id=ulid.new().str,
            run_id=self.run_id,
            platform=platform,
            url=url,
            entity_id=entity_id,
            content_fingerprint=content_fp,
            screen_fingerprint=screen_fingerprint,
            visited_at=datetime.now(timezone.utc),
        )
        created = await self._repo.create(record)
        logger.debug("visit_recorded", url=url, platform=platform)
        return created

    async def should_revisit(
        self,
        url: str | None = None,
        entity_id: str | None = None,
        reason: str | None = None,
    ) -> bool:
        """
        Returns True if revisiting is justified:
        - Must have an explicit reason
        - revisit_count < max_revisits
        - Either url or entity_id must be provided
        """
        if not reason:
            return False
        record = None
        if url:
            record = await self._repo.get_by_url(url, self.run_id)
        if record is None and entity_id:
            record = await self._repo.get_by_entity(entity_id, self.run_id)
        if record is None:
            return True  # Not visited yet — definitely should visit
        return record.revisit_count < self.max_revisits

    async def record_revisit(
        self,
        visit_id: str,
        reason: str,
        sought: str,
    ) -> None:
        """Record that the agent revisited an entity with a specific reason."""
        await self._repo.increment_revisit(visit_id, reason, sought)
        logger.info("revisit_recorded", visit_id=visit_id, reason=reason)
