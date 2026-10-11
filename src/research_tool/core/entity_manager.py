"""Entity creation, deduplication, and tracking manager."""
import structlog
import ulid
from datetime import datetime, timezone
from research_tool.domain import Entity, EntityType, IdentityConfidence
from research_tool.infrastructure.db.repositories.entity_repo import EntityRepo
from research_tool.core.dedup_engine import DedupEngine, DedupProfile, DedupResult
from research_tool.core.yield_tracker import YieldTracker
from research_tool.core.frontier_manager import FrontierManager

logger = structlog.get_logger()

class EntityManager:
    """Manages entities, deduping them against known entities in the DB."""
    
    def __init__(self, run_id: str, repo: EntityRepo, frontier: FrontierManager, yield_tracker: YieldTracker):
        self.run_id = run_id
        self._repo = repo
        self._frontier = frontier
        self._yield_tracker = yield_tracker

    async def discover_entity(
        self,
        name: str,
        brand: str | None = None,
        model_sku: str | None = None,
        image_hash: str | None = None,
        source_url: str | None = None
    ) -> Entity:
        """Process a newly discovered entity, dedup it, and add to frontier if new."""
        profile = DedupProfile(
            normalized_title=name.strip().lower(),
            text_content=name,
            brand=brand,
            model_sku=model_sku,
            image_hash=image_hash
        )
        
        # 1. Fetch all entities (or a subset) for dedup. 
        # In V1 we fetch all for this run.
        existing_entities = await self._repo.list_by_run(self.run_id)
        
        best_match = None
        best_result = DedupResult.DIFFERENT
        
        for e in existing_entities:
            e_profile = DedupProfile(
                normalized_title=e.name.strip().lower(),
                text_content=e.name,
                brand=e.brand,
                model_sku=e.model_sku,
                image_hash=None # we'd need to store image hash on Entity, but for V1 we skip or use text
            )
            res = DedupEngine.compare(profile, e_profile)
            if res == DedupResult.SAME:
                best_match = e
                best_result = res
                break
            elif res == DedupResult.PROBABLY_SAME:
                best_match = e
                best_result = res
                
        if best_match:
            logger.info("entity_deduped", result=best_result.value, existing=best_match.entity_id)
            return best_match
            
        # 2. If DIFFERENT or UNKNOWN, create a new Entity
        entity = Entity(
            entity_id=ulid.new().str,
            run_id=self.run_id,
            entity_type=EntityType.PRODUCT, # default
            name=name,
            brand=brand,
            model_sku=model_sku,
            identity_confidence=IdentityConfidence.HIGH,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await self._repo.create(entity)
        self._yield_tracker.record_candidate()
        
        # 3. Add to Frontier
        await self._frontier.add_entity(
            entity_id=entity.entity_id,
            novelty=1.0,
            unexplored_bonus=1.0
        )
        logger.info("new_entity_discovered", entity_id=entity.entity_id, name=name)
        return entity
