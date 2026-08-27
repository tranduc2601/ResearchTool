"""Full end-to-end integration test of the autonomous agent lifecycle."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import ulid

from research_tool.config.settings import AppSettings
from research_tool.infrastructure.db.connection import get_connection, apply_schema
from research_tool.infrastructure.db.repositories import (
    RunRepo, SeedRepo, FrontierRepo, GraphRepo, VisitRepo,
    EvidenceRepo, EntityRepo, CheckpointRepo, EventRepo
)
from research_tool.infrastructure.file_storage import FileStorage
from research_tool.domain import PageType, Confidence, RunStatus
from research_tool.domain.event import EventType
from research_tool.interfaces import VisionResult, UIElement, BoundingBox
from research_tool.core.event_logger import EventLogger
from research_tool.core.yield_tracker import YieldTracker
from research_tool.core.seed_manager import SeedManager
from research_tool.core.visit_manager import VisitManager
from research_tool.core.frontier_manager import FrontierManager
from research_tool.core.exploration_graph import ExplorationGraph
from research_tool.core.evidence_manager import EvidenceManager
from research_tool.core.recovery_manager import RecoveryManager
from research_tool.core.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_full_autonomous_lifecycle(tmp_path: Path):
    """Test the complete research session loop."""
    # 1. Setup DB in memory (or tmp_path)
    db_path = tmp_path / "test_research.db"
    await apply_schema(db_path)
    
    settings = AppSettings(data_dir=tmp_path)
    
    run_repo = RunRepo(db_path)
    seed_repo = SeedRepo(db_path)
    frontier_repo = FrontierRepo(db_path)
    graph_repo = GraphRepo(db_path)
    visit_repo = VisitRepo(db_path)
    evidence_repo = EvidenceRepo(db_path)
    entity_repo = EntityRepo(db_path)
    checkpoint_repo = CheckpointRepo(db_path)
    event_repo = EventRepo(db_path)
    
    file_storage = FileStorage(tmp_path)
    
    # 2. Setup Stubs/Mocks
    controller = AsyncMock()
    controller.screenshot.return_value = b"fake_png"
    controller.get_active_url.return_value = "https://example.com/test"
    controller.get_window_title.return_value = "Test Page"
    
    vision = AsyncMock()
    # Mock vision returning an entity
    vision.analyze_screen.return_value = VisionResult(
        page_type=PageType.SEARCH_RESULT,
        detected_elements=[
            UIElement(
                element_type="product_card",
                bounding_box=BoundingBox(0, 0, 10, 10),
                label="Test Ergonomic Chair",
                confidence=0.9
            )
        ],
        current_entity_name="Test Ergonomic Chair",
        confidence=Confidence.KNOWN,
        suggested_action="Click on the product card",
        raw_output="{}"
    )
    
    ocr = AsyncMock()
    
    # 3. Setup Managers
    run_id = ulid.new().str
    events = EventLogger(run_id, event_repo, file_storage)
    yield_tracker = YieldTracker()
    seeds = SeedManager(run_id, seed_repo)
    visits = VisitManager(run_id, visit_repo)
    frontier = FrontierManager(run_id, frontier_repo)
    graph = ExplorationGraph(run_id, graph_repo)
    evidence = EvidenceManager(run_id, evidence_repo, entity_repo, file_storage, yield_tracker)
    recovery = RecoveryManager(run_id, checkpoint_repo, yield_tracker)
    
    orchestrator = Orchestrator(
        settings=settings,
        run_repo=run_repo,
        controller=controller,
        vision_provider=vision,
        ocr_provider=ocr,
        event_logger=events,
        yield_tracker=yield_tracker,
        seed_manager=seeds,
        visit_manager=visits,
        frontier_manager=frontier,
        exploration_graph=graph,
        evidence_manager=evidence,
        recovery_manager=recovery,
    )
    
    # 4. Run Session
    initial_query = "Tìm ghế ergonomic"
    await orchestrator.start_session(initial_query, run_id=run_id)
    
    # 5. Assertions
    # Run should be completed
    run = await run_repo.get(run_id)
    assert run is not None
    assert run.status == RunStatus.DONE
    
    # Events should be logged
    recent_events = await event_repo.list_by_run(run_id, limit=50)
    assert len(recent_events) > 0
    event_types = [e.event_type for e in recent_events]
    assert EventType.RUN_START in event_types
    assert EventType.RUN_END in event_types
    assert EventType.SEED_DISCOVERED in event_types
    assert EventType.SCREENSHOT in event_types
    
    # Frontier should have been exhausted
    pending = await frontier_repo.list_pending(run_id)
    assert len(pending) == 0
