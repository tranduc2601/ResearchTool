# ResearchTool

ResearchTool is a local-first autonomous visual information explorer and computer-use agent designed for deep information discovery across desktop and mobile user interfaces (not a product recommender). Operating directly through visual perception and device interaction, it navigates complex UI workflows, extracts structured information, and organizes findings locally without cloud lock-in.

## Quick Start

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Run the CLI:
   ```bash
   research-tool start --goal "Find information about topic X"
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

Run linter:
```bash
ruff check .
```

## Architecture Overview

For comprehensive documentation on system architecture, domain models, interface definitions, database schemas, and implementation roadmap, refer to [MASTER_SPEC.md](MASTER_SPEC.md).
