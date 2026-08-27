"""Structured event logger — dual-writes to SQLite EventRepo and JSONL file."""

import structlog
from datetime import datetime, timezone
from research_tool.domain import ActionEvent, EventType, EventActor
from research_tool.infrastructure.db.repositories.event_repo import EventRepo
from research_tool.infrastructure.file_storage import FileStorage
import ulid

logger = structlog.get_logger()

class EventLogger:
    """
    Dual-write event logger.
    
    Usage:
        event_logger = EventLogger(run_id, event_repo, file_storage)
        await event_logger.log(EventType.SEARCH, detail={"query": "bàn làm việc"})
        await event_logger.log(EventType.SEED_DISCOVERED, detail={"seed_text": "T10 Pro"})
    """

    def __init__(self, run_id: str, event_repo: EventRepo, file_storage: FileStorage):
        self.run_id = run_id
        self._repo = event_repo
        self._storage = file_storage

    async def log(
        self,
        event_type: EventType,
        detail: dict | None = None,
        actor: EventActor = EventActor.AGENT,
        parent_event_id: str | None = None,
    ) -> ActionEvent:
        """Create and persist an ActionEvent. Returns the created event."""
        event = ActionEvent(
            event_id=ulid.new().str,
            run_id=self.run_id,
            event_type=event_type,
            actor=actor,
            detail=detail,
            parent_event_id=parent_event_id,
            occurred_at=datetime.now(timezone.utc),
        )
        # Write to SQLite
        await self._repo.append(event)
        # Write to JSONL (non-blocking best-effort)
        try:
            await self._storage.append_event_jsonl({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "actor": event.actor.value,
                "detail": event.detail,
                "parent_event_id": event.parent_event_id,
                "occurred_at": event.occurred_at.isoformat(),
            })
        except Exception as e:
            logger.warning("EventLogger: JSONL write failed", error=str(e))
        logger.debug("event_logged", event_type=event_type.value, detail=detail)
        return event

    async def recent(self, n: int = 10) -> list[ActionEvent]:
        """Return the N most recent events for this run."""
        return await self._repo.get_recent(self.run_id, n)
