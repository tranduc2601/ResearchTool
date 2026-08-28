# Pre-Real-World Validation Checklist

All backend implementation, architecture, and code-only testing phases are officially **complete**. 
The system is now fully prepared for physical, real-world deployment.

Below is the definitive list of physical environment setup tasks and validation tests you must perform.

## 1. Physical Environment Setup
Before running tests, ensure your physical setup is properly configured:
*   [ ] **Connect Android Device**: Plug in your device (e.g., iQOO Z10 Turbo+) via USB.
*   [ ] **Enable USB Debugging**: Ensure `adb devices` lists your device as authorized.
*   [ ] **Scrcpy Dependency**: Ensure the `scrcpy` binary is installed and accessible in your system `PATH`.
*   [ ] **Tesseract Dependency**: Ensure `tesseract` is installed and accessible in your `PATH` (if you plan to benchmark the CPU OCR fallback).
*   [ ] **Primary Display Setup**: For the Windows controller tests, ensure your primary monitor is unobstructed and the scaling settings map to standard coordinates (100% or 150% scaling, adjust mapper if needed).

## 2. Hardware Validation Tests

### A. Android `scrcpy` / ADB Closed Loop Test
**Goal**: Prove the new Android integration works without blocking or crashing the loop.
1. Run `python src/research_tool/cli/main.py run "Find best running shoes" --platform android`
2. **Observe**: Ensure the system successfully starts the `scrcpy` subprocess, grabs screenshots via `adb exec-out screencap`, and translates semantic coordinates into physical taps on your device screen.

### B. OCR Engine Benchmarking (Tesseract vs PaddleOCR)
**Goal**: Determine which OCR backend is more performant on your Ryzen 5 5600H CPU to save GPU VRAM for the main vision model.
1. Run `python scripts/validation/benchmark_ocr.py`
2. **Observe**: Review latency numbers (Average and P90) and extraction quality.
3. Update `config/defaults.yaml` to set your preferred `ocr_backend`.

### C. Full Windows Closed Loop Exploration (Acceptance Test)
**Goal**: Validate the orchestrator's semantic loop on a live desktop without human intervention.
1. Clear your screen to a simple web browser (e.g., an Amazon or Shopee page).
2. Run `python scripts/run_acceptance.py`
3. **Observe**: Do not touch the mouse. Watch as the agent issues `CLICK`, `TYPE_TEXT`, and `SCROLL` commands. Confirm it identifies entities, halts infinite scrolling after 3 empty scrolls, and successfully reaches a `GOAL_MET` or `HUMAN_REQUIRED` state.

### D. System Long-Running Execution (Stress Test)
**Goal**: Verify that the Orchestrator's internal checkpointing, graph memory, and VRAM management remain stable over an extended period.
1. Launch an open-ended goal (e.g., `python src/research_tool/cli/main.py run "Map out current prices for all RTX 4070 laptops on this site"`).
2. **Observe**: Leave the system unattended for 1-2 hours. Monitor Task Manager to ensure Python RAM stays below 3GB and GPU VRAM remains rock solid around 1.55GB.

### E. Data Export Validation
**Goal**: Prove the data gathered during real exploration translates perfectly to external analytics.
1. After the long-running test, note the `RUN_ID`.
2. Run `python src/research_tool/cli/main.py export <RUN_ID> --format csv`
3. **Observe**: Open the generated CSV files in Excel or Pandas. Confirm that `entities`, `evidence`, `visits`, and `frontier` graphs are correctly structured and readable.

---
**Status**: AWAITING USER VALIDATION
**Next Action**: Perform the checklist above.
