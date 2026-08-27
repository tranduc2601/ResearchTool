import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from research_tool.domain import (
    PageType, Confidence, RunStatus, WorldState, 
    ActionCommand, ActionType, ActionStatus, ActionResult
)
from research_tool.interfaces import VisionResult, UIElement, BoundingBox
from research_tool.core.orchestrator import Orchestrator
from research_tool.core.action_validator import ActionValidator

# Import all repos and managers
from research_tool.infrastructure.db.connection import apply_schema
from research_tool.infrastructure.db.repositories.run_repo import RunRepo
from research_tool.infrastructure.db.repositories.seed_repo import SeedRepo
from research_tool.infrastructure.db.repositories.frontier_repo import FrontierRepo
from research_tool.infrastructure.db.repositories.graph_repo import GraphRepo
from research_tool.infrastructure.db.repositories.visit_repo import VisitRepo
from research_tool.infrastructure.db.repositories.evidence_repo import EvidenceRepo
from research_tool.infrastructure.db.repositories.entity_repo import EntityRepo
from research_tool.infrastructure.db.repositories.checkpoint_repo import CheckpointRepo
from research_tool.infrastructure.db.repositories.event_repo import EventRepo

from research_tool.infrastructure.file_storage import FileStorage
from research_tool.core.event_logger import EventLogger
from research_tool.core.yield_tracker import YieldTracker
from research_tool.core.seed_manager import SeedManager
from research_tool.core.visit_manager import VisitManager
from research_tool.core.frontier_manager import FrontierManager
from research_tool.core.exploration_graph import ExplorationGraph
from research_tool.core.evidence_manager import EvidenceManager
from research_tool.core.recovery_manager import RecoveryManager
from research_tool.config.settings import AppSettings

@pytest.fixture
def mock_controller():
    controller = AsyncMock()
    controller.screenshot.return_value = b"fake_png"
    controller.get_active_url.return_value = "https://example.com/test"
    controller.get_window_title.return_value = "Test Page"
    controller.click.return_value = ActionResult(ActionStatus.SUCCESS)
    controller.type_text.return_value = ActionResult(ActionStatus.SUCCESS)
    controller.scroll.return_value = ActionResult(ActionStatus.SUCCESS)
    controller.press_key.return_value = ActionResult(ActionStatus.SUCCESS)
    return controller

@pytest.fixture
def orchestrator_deps(tmp_path):
    db_path = tmp_path / "test_poc.db"
    return db_path

@pytest.mark.asyncio
async def test_static_orchestrator_poc_happy_path(orchestrator_deps, mock_controller):
    """
    Simulate a realistic multi-step workflow:
    Search -> Click -> Type -> Results -> Product -> Scroll -> Read -> Save Evidence -> Goal completion
    """
    db_path = orchestrator_deps
    await apply_schema(db_path)
    
    settings = AppSettings(data_dir=db_path.parent)
    run_repo = RunRepo(db_path)
    seed_repo = SeedRepo(db_path)
    frontier_repo = FrontierRepo(db_path)
    graph_repo = GraphRepo(db_path)
    visit_repo = VisitRepo(db_path)
    evidence_repo = EvidenceRepo(db_path)
    entity_repo = EntityRepo(db_path)
    checkpoint_repo = CheckpointRepo(db_path)
    event_repo = EventRepo(db_path)
    
    file_storage = FileStorage(db_path.parent)
    
    run_id = "run_poc_1"
    events = EventLogger(run_id, event_repo, file_storage)
    yield_tracker = YieldTracker()
    seeds = SeedManager(run_id, seed_repo)
    visits = VisitManager(run_id, visit_repo)
    frontier = FrontierManager(run_id, frontier_repo)
    graph = ExplorationGraph(run_id, graph_repo)
    evidence = EvidenceManager(run_id, evidence_repo, entity_repo, file_storage, yield_tracker)
    recovery = RecoveryManager(run_id, checkpoint_repo, yield_tracker)

    # 1. Setup Vision Mock to return a sequence of actions
    mock_vision = AsyncMock()
    
    # We will simulate the VLM responding sequentially to each screenshot
    mock_vision.analyze_screen.side_effect = [
        # Step 1: Click search bar
        VisionResult(PageType.NAVIGATION, [], None, Confidence.KNOWN, ActionCommand(ActionType.CLICK, x=100, y=100)),
        # Step 2: Type query
        VisionResult(PageType.NAVIGATION, [], None, Confidence.KNOWN, ActionCommand(ActionType.TYPE_TEXT, text="Ergonomic Chair")),
        # Step 3: Press enter
        VisionResult(PageType.NAVIGATION, [], None, Confidence.KNOWN, ActionCommand(ActionType.PRESS_KEY, key="enter")),
        # Step 4: Search results, click product
        VisionResult(PageType.SEARCH_RESULT, [], None, Confidence.KNOWN, ActionCommand(ActionType.CLICK, x=300, y=500)),
        # Step 5: Product page, scroll
        VisionResult(PageType.PRODUCT_PAGE, [], "Ergonomic Chair", Confidence.KNOWN, ActionCommand(ActionType.SCROLL, x=0, y=0)),
        # Step 6: Goal Met
        VisionResult(PageType.PRODUCT_PAGE, [], "Ergonomic Chair", Confidence.KNOWN, ActionCommand(ActionType.GOAL_MET)),
    ]

    mock_ocr = AsyncMock()

    orchestrator = Orchestrator(
        settings=settings, run_repo=run_repo, controller=mock_controller,
        vision_provider=mock_vision, ocr_provider=mock_ocr,
        event_logger=events, yield_tracker=yield_tracker,
        seed_manager=seeds, visit_manager=visits, frontier_manager=frontier,
        exploration_graph=graph, evidence_manager=evidence, recovery_manager=recovery
    )
    
    # Run
    await orchestrator.start_session("Find ergonomic chair", run_id)
    
    # Assertions
    # Inner loop should have completed 6 steps.
    assert mock_vision.analyze_screen.call_count == 6
    assert mock_controller.click.call_count == 2
    assert mock_controller.type_text.call_count == 1
    assert mock_controller.press_key.call_count == 1
    assert mock_controller.scroll.call_count == 1
    
    # The frontier item should be marked as completed
    item = await frontier_repo.pop_next(run_id)
    assert item is None

@pytest.mark.asyncio
async def test_static_orchestrator_poc_captcha_human_required(orchestrator_deps, mock_controller):
    db_path = orchestrator_deps
    await apply_schema(db_path)
    
    # Same setup...
    run_repo = RunRepo(db_path)
    frontier_repo = FrontierRepo(db_path)
    
    # Mocks
    mock_vision = AsyncMock()
    mock_vision.analyze_screen.side_effect = [
        # CAPTCHA detected -> VLM asks for human
        VisionResult(PageType.CAPTCHA, [], None, Confidence.KNOWN, ActionCommand(ActionType.HUMAN_REQUIRED)),
    ]
    
    run_id = "run_poc_2"
    orchestrator = Orchestrator(
        settings=AppSettings(data_dir=db_path.parent), run_repo=run_repo, controller=mock_controller,
        vision_provider=mock_vision, ocr_provider=AsyncMock(),
        event_logger=EventLogger(run_id, EventRepo(db_path), FileStorage(db_path.parent)), 
        yield_tracker=YieldTracker(),
        seed_manager=SeedManager(run_id, SeedRepo(db_path)), 
        visit_manager=VisitManager(run_id, VisitRepo(db_path)), 
        frontier_manager=FrontierManager(run_id, frontier_repo),
        exploration_graph=ExplorationGraph(run_id, GraphRepo(db_path)), 
        evidence_manager=EvidenceManager(run_id, EvidenceRepo(db_path), EntityRepo(db_path), FileStorage(db_path.parent), YieldTracker()), 
        recovery_manager=RecoveryManager(run_id, CheckpointRepo(db_path), YieldTracker())
    )
    
    with pytest.raises(Exception, match="Human required"):
        await orchestrator.start_session("Find ergonomic chair", run_id)
        
    assert orchestrator.current_run.status == RunStatus.PAUSED

@pytest.mark.asyncio
async def test_static_orchestrator_poc_invalid_action(orchestrator_deps, mock_controller):
    db_path = orchestrator_deps
    await apply_schema(db_path)
    
    mock_vision = AsyncMock()
    mock_vision.analyze_screen.side_effect = [
        # Out of bounds click
        VisionResult(PageType.NAVIGATION, [], None, Confidence.KNOWN, ActionCommand(ActionType.CLICK, x=9999, y=9999)),
        # Fallback to goal met
        VisionResult(PageType.NAVIGATION, [], None, Confidence.KNOWN, ActionCommand(ActionType.GOAL_MET)),
    ]
    
    run_id = "run_poc_3"
    orchestrator = Orchestrator(
        settings=AppSettings(data_dir=db_path.parent), run_repo=RunRepo(db_path), controller=mock_controller,
        vision_provider=mock_vision, ocr_provider=AsyncMock(),
        event_logger=EventLogger(run_id, EventRepo(db_path), FileStorage(db_path.parent)), 
        yield_tracker=YieldTracker(), seed_manager=SeedManager(run_id, SeedRepo(db_path)), 
        visit_manager=VisitManager(run_id, VisitRepo(db_path)), frontier_manager=FrontierManager(run_id, FrontierRepo(db_path)),
        exploration_graph=ExplorationGraph(run_id, GraphRepo(db_path)), 
        evidence_manager=EvidenceManager(run_id, EvidenceRepo(db_path), EntityRepo(db_path), FileStorage(db_path.parent), YieldTracker()), 
        recovery_manager=RecoveryManager(run_id, CheckpointRepo(db_path), YieldTracker())
    )
    
    await orchestrator.start_session("Test invalid", run_id)
    
    # 2 calls: one invalid (blocked), one goal met
    assert mock_vision.analyze_screen.call_count == 2
    # Click should NOT have been called because it was out of bounds
    assert mock_controller.click.call_count == 0
