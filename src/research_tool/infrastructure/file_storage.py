"""Async file storage manager for screenshots, JSON exports, and run data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import aiofiles

from research_tool.infrastructure.serialization import from_json, to_json


class FileStorage:
    """
    Manages the run data directory layout:

        data/runs/<run_id>/
            screenshots/          # PNG files
            exports/entities/     # per-entity JSON
            exports/evidence/     # per-evidence JSON
            logs/events.jsonl     # JSONL event log

    Directories are created lazily on first use.
    """

    def __init__(self, run_data_dir: Path | str):
        self.root = Path(run_data_dir)

    # Directory accessors (create on demand)
    @property
    def screenshots_dir(self) -> Path:
        p = self.root / "screenshots"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def entity_exports_dir(self) -> Path:
        p = self.root / "exports" / "entities"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def evidence_exports_dir(self) -> Path:
        p = self.root / "exports" / "evidence"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def logs_dir(self) -> Path:
        p = self.root / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def events_log_path(self) -> Path:
        return self.logs_dir / "events.jsonl"

    # Screenshot operations
    async def save_screenshot(self, image_bytes: bytes, name: str) -> Path:
        """Save PNG bytes to screenshots/<name>.png. Returns absolute path."""
        filename = name if name.endswith(".png") else f"{name}.png"
        path = self.screenshots_dir / filename
        async with aiofiles.open(path, "wb") as f:
            await f.write(image_bytes)
        return path.resolve()

    async def load_screenshot(self, name: str) -> bytes | None:
        """Load screenshot by name. Returns None if not found."""
        filename = name if name.endswith(".png") else f"{name}.png"
        path = self.screenshots_dir / filename
        if not path.exists() or not path.is_file():
            return None
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    # JSON export operations
    async def save_entity_json(self, entity_id: str, data: dict[str, Any] | Any) -> Path:
        """Save entity data to exports/entities/<entity_id>.json"""
        filename = entity_id if entity_id.endswith(".json") else f"{entity_id}.json"
        path = self.entity_exports_dir / filename
        content = to_json(data, indent=2)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        return path.resolve()

    async def save_evidence_json(self, evidence_id: str, data: dict[str, Any] | Any) -> Path:
        """Save evidence data to exports/evidence/<evidence_id>.json"""
        filename = evidence_id if evidence_id.endswith(".json") else f"{evidence_id}.json"
        path = self.evidence_exports_dir / filename
        content = to_json(data, indent=2)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        return path.resolve()

    async def load_json(self, path: Path | str) -> Any | None:
        """Load and parse a JSON file. Returns None if not found."""
        p = Path(path)
        if not p.exists() or not p.is_file():
            return None
        async with aiofiles.open(p, encoding="utf-8") as f:
            content = await f.read()
        return from_json(content)

    # JSONL event log
    async def append_event_jsonl(self, event_dict: dict[str, Any] | Any) -> None:
        """Append one JSON object as a line to events.jsonl"""
        line = to_json(event_dict) + "\n"
        async with aiofiles.open(self.events_log_path, "a", encoding="utf-8") as f:
            await f.write(line)

    async def read_events_jsonl(self) -> list[dict[str, Any]]:
        """Read all lines from events.jsonl. Returns [] if file missing."""
        path = self.events_log_path
        if not path.exists() or not path.is_file():
            return []
        async with aiofiles.open(path, encoding="utf-8") as f:
            lines = await f.readlines()
        events: list[dict[str, Any]] = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                events.append(from_json(stripped))
        return events
