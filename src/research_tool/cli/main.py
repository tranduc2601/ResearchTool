"""Command-line interface."""
import asyncio
import typer
from rich.console import Console
from pathlib import Path

from research_tool.config.settings import load_settings
from research_tool.infrastructure.db.connection import get_connection, apply_schema
from research_tool.infrastructure.db.repositories import (
    RunRepo, SeedRepo, FrontierRepo, GraphRepo, VisitRepo,
    EvidenceRepo, EntityRepo, CheckpointRepo, EventRepo
)
from research_tool.infrastructure.file_storage import FileStorage
from research_tool.implementations import (
    StubVisionProvider, StubOCRProvider, StubController
)
from research_tool.core.event_logger import EventLogger
from research_tool.core.yield_tracker import YieldTracker
from research_tool.core.seed_manager import SeedManager
from research_tool.core.visit_manager import VisitManager
from research_tool.core.frontier_manager import FrontierManager
from research_tool.core.exploration_graph import ExplorationGraph
from research_tool.core.evidence_manager import EvidenceManager
from research_tool.core.recovery_manager import RecoveryManager
from research_tool.core.orchestrator import Orchestrator

app = typer.Typer(help="Autonomous Visual Information Explorer")
console = Console()

@app.command()
def run(
    query: str = typer.Argument(..., help="The initial search query or goal"),
    config: Path = typer.Option(None, help="Path to custom config yaml")
):
    """Start an autonomous research session."""
    console.print(f"[bold green]Starting session with query:[/bold green] {query}")
    asyncio.run(_async_run(query, config))

async def _async_run(query: str, config: Path | None):
    settings = load_settings(config)
    
    # Initialize DB
    db_path = settings.data_dir / "research.db"
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await apply_schema(db_path)
    
    # Repos
    run_repo = RunRepo(db_path)
    seed_repo = SeedRepo(db_path)
    frontier_repo = FrontierRepo(db_path)
    graph_repo = GraphRepo(db_path)
    visit_repo = VisitRepo(db_path)
    evidence_repo = EvidenceRepo(db_path)
    entity_repo = EntityRepo(db_path)
    checkpoint_repo = CheckpointRepo(db_path)
    event_repo = EventRepo(db_path)
    
    # Infrastructure
    file_storage = FileStorage(settings.data_dir)
    
    # Providers (using stubs for V1)
    vision = StubVisionProvider()
    ocr = StubOCRProvider()
    controller = StubController()
    
    import ulid
    run_id = ulid.new().str
    
    # Core Managers
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
    
    await orchestrator.start_session(query, run_id=run_id)
    console.print("[bold green]Session completed![/bold green]")

if __name__ == "__main__":
    app()
