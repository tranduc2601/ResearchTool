# ResearchTool

ResearchTool is a local-first autonomous visual information explorer and computer-use agent designed for deep information discovery across desktop and mobile user interfaces. Operating directly through visual perception and device interaction, it navigates complex UI workflows, extracts structured information, and organizes findings locally without cloud lock-in.

## Quick Start

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Configure Environment:
   Edit `src/research_tool/config/defaults.yaml` or set environment variables via `.env`.

4. Run the CLI (Terminal Dashboard):
   ```bash
   research-tool run "Find information about topic X" --platform windows --model qwen2-vl
   ```

5. Run the Minimal Desktop GUI:
   ```bash
   python src/research_tool/gui/app.py
   ```

## Features & Usage

### Exporting Data
After a session completes, you can export the SQLite trace graph and discovered entities to JSON or CSV:
```bash
research-tool export <RUN_ID> --format csv --out ./results
```

### Android Integration (Scrcpy / ADB)
The agent can control an Android device directly. Ensure `adb` (and optionally `scrcpy`) are installed and in your PATH. 
```bash
research-tool run "Search Shopee for ergonomic chairs" --platform android
```

### OCR Providers
The tool ships with fallback OCR to assist the VLM with dense text reading.
We support **Tesseract** (CPU) and **PaddleOCR** (CPU/GPU).
You can benchmark them locally using:
```bash
python scripts/validation/benchmark_ocr.py
```

### Packaging
To compile a standalone binary for distribution using PyInstaller:
```bash
python scripts/build_standalone.py
```

## Development Setup

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run test suite:
```bash
pytest
```

## Architecture Overview

For comprehensive documentation on system architecture, refer to `IMPLEMENTATION_STATUS.md` and `PRE-REAL-WORLD-VALIDATION.md`.
