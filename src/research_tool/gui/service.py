"""Application Service bridging Orchestrator and GUI."""
import asyncio
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Dict, Any
import ulid

from research_tool.config.settings import load_settings, AppSettings
from research_tool.infrastructure.db.connection import apply_schema
from research_tool.infrastructure.db.repositories import (
    RunRepo, SeedRepo, FrontierRepo, GraphRepo, VisitRepo,
    EvidenceRepo, EntityRepo, CheckpointRepo, EventRepo
)
from research_tool.infrastructure.file_storage import FileStorage
from research_tool.implementations.vision.local_vlm import LocalVisionProvider
from research_tool.implementations.ocr.tesseract_ocr import TesseractOCRProvider
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

class ApplicationService:
    def __init__(self):
        self.orchestrator: Optional[Orchestrator] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.state_queue = queue.Queue()
        self.run_id: str = ""
        self.settings: Optional[AppSettings] = None

    def start_run(self, query: str, platform: str, model: str, time_end_mins: float, out_dir: str, adb_device: str = None, use_scrcpy: bool = False):
        """Starts the orchestrator in a background thread."""
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Already running")
            
        self._stop_event.clear()
        self.run_id = ulid.new().str
        
        from research_tool.config.settings import get_app_root
        self.settings = load_settings()
        
        # Override output dir if provided
        if out_dir:
            p = Path(out_dir)
            if not p.is_absolute():
                p = get_app_root() / p
            self.settings.data_dir = p
            
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(query, platform, model, time_end_mins, adb_device, use_scrcpy),
            daemon=True
        )
        self._thread.start()

    def stop_run(self):
        """Requests the orchestrator to stop safely."""
        self._stop_event.set()
        if self.orchestrator and self.orchestrator.current_run:
            from research_tool.domain.run import RunStatus
            self.orchestrator.current_run.status = RunStatus.PAUSED
            
    def emergency_stop(self):
        """Triggers emergency stop (hard fail)."""
        self._stop_event.set()
        if self.orchestrator and self.orchestrator.current_run:
            from research_tool.domain.run import RunStatus
            self.orchestrator.current_run.status = RunStatus.FAILED

    def get_latest_state(self) -> Dict[str, Any]:
        """Returns the current state for the GUI to display."""
        if not self.orchestrator or not self.orchestrator.current_run:
            return {"status": "IDLE"}
            
        seeds = frontier = entities = evidence = 0
        try:
            import sqlite3
            db_path = self.settings.data_dir / "research.db"
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                seeds = c.execute("SELECT COUNT(*) FROM seeds WHERE run_id=?", (self.run_id,)).fetchone()[0]
                frontier = c.execute("SELECT COUNT(*) FROM frontier WHERE run_id=?", (self.run_id,)).fetchone()[0]
                entities = c.execute("SELECT COUNT(*) FROM entities WHERE run_id=?", (self.run_id,)).fetchone()[0]
                evidence = c.execute("SELECT COUNT(*) FROM evidence WHERE run_id=?", (self.run_id,)).fetchone()[0]
        except Exception:
            pass
            
        return {
            "status": self.orchestrator.current_run.status.value,
            "run_id": self.run_id,
            "platform": self.orchestrator.world_state.platform if self.orchestrator.world_state.platform else "Unknown",
            "active_app": self.orchestrator.world_state.app or "Unknown",
            "seeds": seeds,
            "frontier": frontier,
            "entities": entities,
            "evidence": evidence,
        }

    def _run_loop(self, query: str, platform: str, model: str, time_end_mins: float, adb_device: str, use_scrcpy: bool):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._async_start(query, platform, model, time_end_mins, adb_device, use_scrcpy))
        except Exception as e:
            self.state_queue.put({"error": str(e)})
        finally:
            self.loop.close()

    async def _async_start(self, query: str, platform: str, model: str, time_end_mins: float, adb_device: str, use_scrcpy: bool):
        db_path = self.settings.data_dir / "research.db"
        self.settings.data_dir.mkdir(parents=True, exist_ok=True)
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
        
        from research_tool.implementations.ocr.paddle_ocr import PaddleOCRProvider, PADDLE_AVAILABLE
        from research_tool.implementations.ocr.tesseract_ocr import TesseractOCRProvider, TESSERACT_AVAILABLE
        
        file_storage = FileStorage(self.settings.data_dir)
        ocr = None
        
        if self.settings.providers.ocr_backend.lower() == "paddle" and PADDLE_AVAILABLE:
            ocr = PaddleOCRProvider()
        elif self.settings.providers.ocr_backend.lower() == "tesseract" and TESSERACT_AVAILABLE:
            ocr = TesseractOCRProvider()
            
        # Map friendly names to HuggingFace repository paths
        hf_model_path = model
        if model.lower() == "qwen2-vl":
            hf_model_path = self.settings.providers.vision_model_path if getattr(self.settings.providers, 'vision_model_path', None) else "Qwen/Qwen2-VL-2B-Instruct"
        elif model.lower() == "moondream2":
            hf_model_path = "vikhyatk/moondream2"
            
        vision = LocalVisionProvider(model_name=hf_model_path, ocr_provider=ocr)
        
        if platform.lower() == "android":
            # Scale from Qwen's native 1000x1000 grid to Android screen size
            mapper = ScalingCoordinateMapper(1000, 1000, 1080, 2400)
            controller = AndroidController(device_serial=adb_device, mapper=mapper, use_scrcpy=use_scrcpy)
            if use_scrcpy:
                await controller.start_scrcpy()
        else:
            # Scale from Qwen's native 1000x1000 grid to actual screen size
            import pyautogui
            sw, sh = pyautogui.size()
            mapper = ScalingCoordinateMapper(1000, 1000, sw, sh)
            controller = WindowsController(mapper=mapper)
            
        events = EventLogger(self.run_id, event_repo, file_storage)
        yield_tracker = YieldTracker()
        seeds = SeedManager(self.run_id, seed_repo)
        visits = VisitManager(self.run_id, visit_repo)
        frontier = FrontierManager(self.run_id, frontier_repo)
        graph = ExplorationGraph(self.run_id, graph_repo)
        entities = EntityManager(self.run_id, entity_repo, frontier, yield_tracker)
        evidence = EvidenceManager(self.run_id, evidence_repo, entity_repo, file_storage, yield_tracker)
        recovery = RecoveryManager(self.run_id, checkpoint_repo, yield_tracker)
        
        self.orchestrator = Orchestrator(
            settings=self.settings,
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
        
        # Override action timeout/limits if time_end_mins is set
        if time_end_mins > 0:
            # Simplistic approach: we just let orchestrator run but have a background task watch time
            pass
            
        start_time = time.time()
        
        # Create a watchdog task to monitor for stop event or timeout
        async def watchdog():
            while not self._stop_event.is_set():
                if time_end_mins > 0 and (time.time() - start_time) > (time_end_mins * 60):
                    self.stop_run()
                    self.state_queue.put({"log": f"Time limit of {time_end_mins} mins reached."})
                    break
                await asyncio.sleep(1)
                
        watchdog_task = asyncio.create_task(watchdog())
        
        try:
            self.state_queue.put({"log": f"Session started: {self.run_id}"})
            await self.orchestrator.start_session(query, run_id=self.run_id)
        except Exception as e:
            self.state_queue.put({"log": f"Error in orchestrator: {str(e)}"})
        finally:
            self._stop_event.set()
            await watchdog_task
            self.state_queue.put({"log": "Session ended."})
