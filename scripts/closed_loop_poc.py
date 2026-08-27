"""
Closed-Loop PoC for Wave 7C.

This script wires together the REAL WindowsController and REAL VisionProvider (Moondream2 / Qwen2-VL)
and executes a strictly controlled, single-page workflow to measure latency and state logs.

Usage:
    python scripts/closed_loop_poc.py
"""
import asyncio
import structlog
from pathlib import Path
from research_tool.domain.action import ActionType, ActionStatus
from research_tool.core.action_validator import ActionValidator
from research_tool.core.scaling_mapper import ScalingCoordinateMapper
from research_tool.implementations.controller.windows_controller import WindowsController

# For this PoC, we will create a lightweight RealVisionProvider wrapper
# Note: You must have transformers, torch, etc. installed (see benchmark_vlm.py).
from research_tool.interfaces.vision_provider import VisionProvider, VisionResult
from research_tool.domain.action import ActionCommand
from research_tool.domain import PageType, Confidence, WorldState

logger = structlog.get_logger()

class RealVisionProvider(VisionProvider):
    """A minimal wrapper around the VLM benchmark code for the orchestrator interface."""
    def __init__(self, model_name: str = "moondream2"):
        # Inline import to avoid breaking if not installed
        from benchmark_vlm import VLMBenchmark
        self.benchmark = VLMBenchmark(model_name)
        self.benchmark.load_model()
        # Save temp screenshots to pass to the benchmark
        self.tmp_path = Path("tmp_closed_loop.png")

    async def analyze_screen(self, screenshot_bytes: bytes, current_state: WorldState, goal_query: str) -> VisionResult:
        with open(self.tmp_path, "wb") as f:
            f.write(screenshot_bytes)
            
        # The prompt forces the VLM to return structured text.
        # Qwen2-VL is better at JSON, but for this PoC we'll use a very simple string parser.
        prompt = f"""
        You are an autonomous web agent.
        Goal: {goal_query}
        
        Analyze the image and reply ONLY with the next action in this format:
        ACTION: <type>
        X: <x> (if click/scroll)
        Y: <y> (if click/scroll)
        TEXT: <text> (if type)
        
        Valid types: CLICK, TYPE_TEXT, SCROLL, GOAL_MET
        """
        
        # This is a blocking call, but it's a PoC script
        import asyncio
        result_text = await asyncio.to_thread(self.benchmark.run_inference, str(self.tmp_path), prompt)
        
        return self._parse_vlm_output(result_text)
        
    def _parse_vlm_output(self, text: str) -> VisionResult:
        """Extremely naive parser for the PoC."""
        lines = text.strip().split('\n')
        action_type = ActionType.WAIT
        x, y = None, None
        out_text = ""
        
        for line in lines:
            line = line.strip().upper()
            if line.startswith("ACTION:"):
                action_str = line.replace("ACTION:", "").strip()
                try:
                    action_type = ActionType(action_str)
                except ValueError:
                    action_type = ActionType.WAIT
            elif line.startswith("X:"):
                try:
                    x = int(line.replace("X:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("Y:"):
                try:
                    y = int(line.replace("Y:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("TEXT:"):
                out_text = line.replace("TEXT:", "").strip()
                
        command = ActionCommand(action_type=action_type, x=x, y=y, text=out_text)
        logger.info("vlm_parsed_command", command=str(command))
        
        return VisionResult(
            page_type=PageType.UNKNOWN,
            detected_elements=[],
            current_entity_name=None,
            confidence=Confidence.UNCERTAIN,
            next_action=command
        )


async def run_closed_loop():
    logger.info("Initializing Closed-Loop PoC...")
    
    # 1. Setup Controller
    # Assuming the Vision model uses a 1000x1000 grid for coords, mapping to 1920x1080 screen
    mapper = ScalingCoordinateMapper(1000, 1000, 1920, 1080)
    controller = WindowsController(mapper=mapper)
    validator = ActionValidator(1000, 1000) # Validating model coords, not screen coords
    
    # 2. Setup Vision
    try:
        vision = RealVisionProvider(model_name="moondream2") # or qwen2-vl
    except ImportError:
        logger.error("Missing ML dependencies. See scripts/benchmark_vlm.py")
        return

    # 3. Dummy State
    world_state = WorldState(run_id="poc_run_1", platform="windows", app="desktop")
    goal = "Find the search bar and click it."
    
    max_steps = 3
    for step in range(max_steps):
        logger.info(f"--- Step {step + 1} ---")
        
        # SEE
        logger.info("Capturing screenshot...")
        screenshot = await controller.screenshot()
        
        # THINK
        logger.info("Requesting VLM analysis...")
        import time
        start = time.time()
        vision_result = await vision.analyze_screen(screenshot, world_state, goal)
        logger.info(f"VLM latency: {time.time() - start:.2f}s")
        
        action = vision_result.next_action
        
        if action.action_type == ActionType.GOAL_MET:
            logger.info("VLM reported GOAL MET. Terminating.")
            break
            
        # VALIDATE
        val_res = validator.validate(action)
        if val_res.status != ActionStatus.SUCCESS:
            logger.warning("Invalid action proposed", error=val_res.error)
            continue
            
        # ACT
        logger.info("Executing action via PyAutoGUI...", action=action.action_type)
        if action.action_type == ActionType.CLICK and action.x is not None and action.y is not None:
            await controller.click(action.x, action.y)
        elif action.action_type == ActionType.TYPE_TEXT and action.text:
            await controller.type_text(action.text)
            
        await asyncio.sleep(2.0) # Wait for UI to settle

    logger.info("Closed-Loop PoC Complete.")

if __name__ == "__main__":
    asyncio.run(run_closed_loop())
