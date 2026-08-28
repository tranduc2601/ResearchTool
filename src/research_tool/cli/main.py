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
from research_tool.implementations.vision.local_vlm import LocalVisionProvider
from research_tool.implementations.controller.windows_controller import WindowsController
from research_tool.implementations.controller.android_controller import AndroidController
from research_tool.core.scaling_mapper import ScalingCoordinateMapper

from research_tool.core.event_logger import EventLogger
from research_tool.core.yield_tracker import YieldTracker
from research_tool.core.seed_manager import SeedManager
from research_tool.core.visit_manager import VisitManager
from research_tool.core.frontier_manager import FrontierManager
from research_tool.core.exploration_graph import ExplorationGraph
from research_tool.core.evidence_manager import EvidenceManager
from research_tool.core.recovery_manager import RecoveryManager
from research_tool.core.entity_manager import EntityManager
from research_tool.core.orchestrator import Orchestrator
from research_tool.cli.dashboard import Dashboard

app = typer.Typer(help="Autonomous Visual Information Explorer")
console = Console()

@app.command()
def run(
    query: str = typer.Argument(..., help="The initial search query or goal"),
    config: Path = typer.Option(None, help="Path to custom config yaml"),
    model: str = typer.Option("qwen2-vl", help="Local VLM model name"),
    platform: str = typer.Option("windows", help="Target platform (windows or android)"),
    resume: str = typer.Option(None, help="Run ID to resume"),
):
    """Start an autonomous research session."""
    console.print(f"[bold green]Starting session with query:[/bold green] {query}")
    asyncio.run(_async_run(query, config, model, platform, resume))

async def _async_run(query: str, config: Path | None, model: str, platform: str, resume: str | None):
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
    
    if settings.providers.ocr_backend.lower() == "paddle":
        from research_tool.implementations.ocr.paddle_ocr import PaddleOCRProvider, PADDLE_AVAILABLE
        ocr = PaddleOCRProvider() if PADDLE_AVAILABLE else None
    else:
        from research_tool.implementations.ocr.tesseract_ocr import TesseractOCRProvider, TESSERACT_AVAILABLE
        ocr = TesseractOCRProvider() if TESSERACT_AVAILABLE else None
        
    vision = LocalVisionProvider(model_name=model, ocr_provider=ocr)
    
    if platform.lower() == "android":
        mapper = ScalingCoordinateMapper(1000, 1000, 1080, 2400)
        controller = AndroidController(mapper=mapper)
    else:
        mapper = ScalingCoordinateMapper(1000, 1000, 1920, 1080)
        controller = WindowsController(mapper=mapper)
    
    import ulid
    run_id = resume if resume else ulid.new().str
    
    # Core Managers
    events = EventLogger(run_id, event_repo, file_storage)
    yield_tracker = YieldTracker()
    seeds = SeedManager(run_id, seed_repo)
    visits = VisitManager(run_id, visit_repo)
    frontier = FrontierManager(run_id, frontier_repo)
    graph = ExplorationGraph(run_id, graph_repo)
    entities = EntityManager(run_id, entity_repo, frontier, yield_tracker)
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
        entity_manager=entities
    )
    
    dashboard = Dashboard(orchestrator)
    
    # Run orchestration and dashboard concurrently
    if resume:
        orch_task = asyncio.create_task(orchestrator.resume_session(resume))
    else:
        orch_task = asyncio.create_task(orchestrator.start_session(query, run_id=run_id))
        
    dash_task = asyncio.create_task(dashboard.run())
    
    await asyncio.gather(orch_task, dash_task)
    console.print("[bold green]Session completed![/bold green]")

@app.command()
def export(
    run_id: str = typer.Argument(..., help="The Run ID to export"),
    format: str = typer.Option("json", help="Export format: json or csv"),
    out: Path = typer.Option(Path("export_out"), help="Output directory"),
    config: Path = typer.Option(None, help="Path to custom config yaml")
):
    """Export run data (entities, evidence, graphs) to a structured format."""
    settings = load_settings(config)
    db_path = settings.data_dir / "research.db"
    
    if not db_path.exists():
        console.print(f"[red]Database not found at {db_path}[/red]")
        raise typer.Exit(1)
        
    out.mkdir(parents=True, exist_ok=True)
    
    # Simple synchronous dump for export
    import sqlite3
    import json
    import csv
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    tables = ["entities", "evidence", "visits", "frontier"]
    
    for table in tables:
        rows = conn.execute(f"SELECT * FROM {table} WHERE run_id = ?", (run_id,)).fetchall()
        data = [dict(r) for r in rows]
        
        if format.lower() == "json":
            out_file = out / f"{run_id}_{table}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            out_file = out / f"{run_id}_{table}.csv"
            if data:
                with open(out_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    
    console.print(f"[bold green]Exported {len(tables)} tables to {out.absolute()}[/bold green]")

if __name__ == "__main__":
    app()
