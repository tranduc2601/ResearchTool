import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from research_tool.domain import (
    RunSession, SeedSource, EventType, ActionEvent,
    WorldState, PageType, AgentStatus, CheckpointTrigger, Seed
)
from research_tool.core.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_start_session():
    # Mocks
    settings = MagicMock()
    run_repo = AsyncMock()
    controller = AsyncMock()
    vision_provider = AsyncMock()
    ocr_provider = AsyncMock()
    event_logger = AsyncMock()
    yield_tracker = MagicMock()
    seed_manager = AsyncMock()
    visit_manager = AsyncMock()
    frontier_manager = AsyncMock()
    exploration_graph = AsyncMock()
    evidence_manager = AsyncMock()
    recovery_manager = AsyncMock()

    # Setup specific mocks
    yield_tracker.current_status.return_value = "EXPLORATION"
    
    # Return a dummy seed from create_seed
    dummy_seed = Seed(
        seed_id="seed-123",
        run_id="run-1",
        text="test query",
        source=SeedSource.USER,
        status="ACTIVE"
    )
    seed_manager.create_seed.return_value = (dummy_seed, "new")
    
    # Return some items from frontier to run loop a few times
    item1 = MagicMock()
    item1.seed_id = "seed-123"
    item1.frontier_id = "front-1"
    
    item2 = MagicMock()
    item2.seed_id = "seed-456"
    item2.frontier_id = "front-2"
    
    # Third pop returns None to break the loop normally if max_iters wasn't hit
    frontier_manager.pop_next.side_effect = [item1, item2, None]
    
    controller.screenshot.return_value = b"fake_screenshot"
    controller.get_active_url.return_value = "https://example.com"
    controller.get_window_title.return_value = "Example Title"
    
    vision_result = MagicMock()
    vision_result.page_type = PageType.SEARCH_RESULT
    vision_provider.analyze_screen.return_value = vision_result

    # Create orchestrator
    orchestrator = Orchestrator(
        settings=settings,
        run_repo=run_repo,
        controller=controller,
        vision_provider=vision_provider,
        ocr_provider=ocr_provider,
        event_logger=event_logger,
        yield_tracker=yield_tracker,
        seed_manager=seed_manager,
        visit_manager=visit_manager,
        frontier_manager=frontier_manager,
        exploration_graph=exploration_graph,
        evidence_manager=evidence_manager,
        recovery_manager=recovery_manager
    )
    
    # Run
    await orchestrator.start_session("test query", "run-1")
    
    # Assertions
    
    # 1. verify run repo create
    run_repo.create.assert_awaited_once()
    created_run = run_repo.create.await_args[0][0]
    assert created_run.run_id == "run-1"
    assert created_run.goal_text == "test query"
    
    # 2. verify event log for run started
    event_logger.log.assert_any_await(EventType.RUN_START, {"initial_query": "test query"})
    
    # 3. verify seed creation
    seed_manager.create_seed.assert_awaited_once_with(text="test query", source=SeedSource.USER)
    frontier_manager.add_seed.assert_awaited_once()
    
    # 4. verify loop calls (2 items before exhausted)
    assert controller.screenshot.await_count == 2
    assert vision_provider.analyze_screen.await_count == 2
    assert visit_manager.record_visit.await_count == 2
    
    # 5. verify completion
    assert orchestrator.current_run.status.name == "DONE"
    run_repo.update_status.assert_awaited_once_with("run-1", orchestrator.current_run.status)
    event_logger.log.assert_any_await(EventType.RUN_END)

@pytest.mark.asyncio
async def test_orchestrator_cancellation():
    settings = MagicMock()
    run_repo = AsyncMock()
    event_logger = AsyncMock()
    seed_manager = AsyncMock()
    frontier_manager = AsyncMock()
    
    # Minimum required for start_session before loop
    dummy_seed = Seed(
        seed_id="seed-123",
        run_id="run-1",
        text="test query",
        source=SeedSource.USER,
        status="ACTIVE"
    )
    seed_manager.create_seed.return_value = (dummy_seed, "new")
    
    orchestrator = Orchestrator(
        settings=settings,
        run_repo=run_repo,
        controller=AsyncMock(),
        vision_provider=AsyncMock(),
        ocr_provider=AsyncMock(),
        event_logger=event_logger,
        yield_tracker=MagicMock(),
        seed_manager=seed_manager,
        visit_manager=AsyncMock(),
        frontier_manager=frontier_manager,
        exploration_graph=AsyncMock(),
        evidence_manager=AsyncMock(),
        recovery_manager=AsyncMock()
    )
    
    # Force asyncio.CancelledError inside _run_loop
    orchestrator._run_loop = AsyncMock(side_effect=asyncio.CancelledError)
    
    with pytest.raises(asyncio.CancelledError):
        await orchestrator.start_session("test query", "run-1")
        
    # Ensure completion log/status still happens
    assert orchestrator.current_run.status.name == "PAUSED"
    run_repo.update_status.assert_awaited_once_with("run-1", orchestrator.current_run.status)
