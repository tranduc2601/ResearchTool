import asyncio
import os
from pathlib import Path

# Setup paths
import sys
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from research_tool.config.settings import load_settings
from research_tool.implementations.controller.windows_controller import WindowsController
from research_tool.implementations.vision.local_vlm import LocalVisionProvider
from research_tool.core.orchestrator import Orchestrator

def main():
    settings = load_settings()
    # Provide dummy dependencies just to verify init
    # Wait, Orchestrator expects full Managers/Repositories. 
    # It's easier to use the ApplicationService.
    from research_tool.gui.service import ApplicationService
    
    app_svc = ApplicationService()
    # start_run does not block, it spins up a thread
    app_svc.start_run(
        query="test query", 
        platform="windows", 
        model="moondream2",  # use a lightweight or mock model string
        time_end_mins=0, 
        out_dir=str(settings.data_dir), 
        adb_device=None, 
        use_scrcpy=False
    )
    
    import time
    time.sleep(2)  # give it time to init and fail if it will fail
    
    # Check queue for errors
    errors = []
    while not app_svc.state_queue.empty():
        msg = app_svc.state_queue.get_nowait()
        if "error" in msg:
            errors.append(msg["error"])
        if "log" in msg:
            print("LOG:", msg["log"])
            
    if errors:
        print("ERRORS ENCOUNTERED:")
        for e in errors:
            print(e)
        sys.exit(1)
        
    state = app_svc.get_latest_state()
    print("Final Status:", state.get("status"))
    app_svc.stop_run()

if __name__ == "__main__":
    main()
