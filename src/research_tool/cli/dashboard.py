"""Terminal UI Dashboard for the Research Tool."""
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
import asyncio

from research_tool.domain import RunStatus
from research_tool.core.orchestrator import Orchestrator

class Dashboard:
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self.console = Console()
        self.layout = Layout()
        self._setup_layout()
        
    def _setup_layout(self):
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="logs", ratio=2)
        )

    def _generate_header(self) -> Panel:
        run = self.orchestrator.current_run
        goal = run.goal_text if run else "Initializing..."
        status = run.status.value if run else "STARTING"
        return Panel(f"[bold blue]Autonomous Explorer[/bold blue] | Goal: [yellow]{goal}[/yellow] | Status: [bold {self._status_color(status)}]{status}[/]", style="white")

    def _status_color(self, status: str) -> str:
        colors = {"RUNNING": "green", "PAUSED": "yellow", "DONE": "blue", "FAILED": "red"}
        return colors.get(status, "white")

    def _generate_stats(self) -> Panel:
        table = Table.grid(padding=1)
        table.add_column(style="cyan", justify="right")
        table.add_column(style="magenta")
        
        # Pull stats from orchestrator (in a real app we'd query the DB or managers, this is simple for V1)
        # We can use the YieldTracker to get some stats
        yt = self.orchestrator.yield_tracker
        table.add_row("Candidates Found:", str(yt.metrics.new_candidates_count))
        table.add_row("Evidence Captured:", str(yt.metrics.new_evidence_count))
        table.add_row("Saturation Level:", str(yt.current_status()))
        
        return Panel(table, title="[bold]Run Metrics[/bold]", border_style="cyan")
        
    def _generate_logs(self) -> Panel:
        # We'd ideally tail the structlog output, but for simple V1 GUI we just show active state
        ws = self.orchestrator.world_state
        app = ws.active_app if ws else "None"
        url = ws.active_url if ws else "None"
        title = ws.active_window_title if ws else "None"
        
        text = Text()
        text.append(f"Current App: {app}\n", style="bold")
        text.append(f"Active URL: {url}\n", style="blue")
        text.append(f"Window: {title}\n", style="italic")
        
        return Panel(text, title="[bold]Current Vision Context[/bold]", border_style="green")
        
    def _generate_footer(self) -> Panel:
        import psutil
        try:
            import torch
            vram = torch.cuda.memory_allocated() / (1024**2) if torch.cuda.is_available() else 0
        except ImportError:
            vram = 0
            
        ram = psutil.Process().memory_info().rss / (1024**2)
        return Panel(f"RAM: {ram:.1f} MB | VRAM: {vram:.1f} MB", style="dim")

    async def run(self):
        """Run the dashboard alongside the orchestrator."""
        with Live(self.layout, refresh_per_second=2, console=self.console) as live:
            while True:
                # Update panels
                self.layout["header"].update(self._generate_header())
                self.layout["stats"].update(self._generate_stats())
                self.layout["logs"].update(self._generate_logs())
                self.layout["footer"].update(self._generate_footer())
                
                if self.orchestrator.current_run and self.orchestrator.current_run.status in [RunStatus.DONE, RunStatus.FAILED]:
                    break
                    
                await asyncio.sleep(0.5)
