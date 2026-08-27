"""Tests for FileStorage, DomainJSONEncoder, and fingerprinting utilities."""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import pytest
from PIL import Image

from research_tool.infrastructure.file_storage import FileStorage
from research_tool.infrastructure.serialization import (
    DomainJSONEncoder,
    fingerprint_image,
    fingerprint_text,
    from_json,
    hamming_distance,
    normalize_title,
    to_json,
)


class SampleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"


@dataclass
class SampleEntity:
    id: str
    name: str
    status: SampleStatus
    created_at: datetime
    path: Path


def make_sample_png_bytes(color: str = "red", size: tuple[int, int] = (8, 8)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# FileStorage Tests
# ---------------------------------------------------------------------------


def test_file_storage_lazy_directory_creation(tmp_path: Path):
    storage = FileStorage(tmp_path / "run_123")

    # Before accessing properties, subdirectories do not exist
    assert not (tmp_path / "run_123" / "screenshots").exists()
    assert not (tmp_path / "run_123" / "exports" / "entities").exists()
    assert not (tmp_path / "run_123" / "exports" / "evidence").exists()
    assert not (tmp_path / "run_123" / "logs").exists()

    # Accessing properties creates them lazily
    assert storage.screenshots_dir.exists()
    assert storage.entity_exports_dir.exists()
    assert storage.evidence_exports_dir.exists()
    assert storage.logs_dir.exists()
    assert storage.events_log_path == storage.logs_dir / "events.jsonl"


async def test_file_storage_save_and_load_screenshot(tmp_path: Path):
    storage = FileStorage(tmp_path)
    image_data = make_sample_png_bytes("blue")

    # Save screenshot
    saved_path = await storage.save_screenshot(image_data, "screen_01")
    assert saved_path.exists()
    assert saved_path.name == "screen_01.png"

    # Load back
    loaded_data = await storage.load_screenshot("screen_01")
    assert loaded_data == image_data

    # Loading with .png suffix also works
    loaded_data_suffix = await storage.load_screenshot("screen_01.png")
    assert loaded_data_suffix == image_data


async def test_file_storage_load_screenshot_missing(tmp_path: Path):
    storage = FileStorage(tmp_path)
    loaded = await storage.load_screenshot("non_existent")
    assert loaded is None


async def test_file_storage_save_entity_and_load_json(tmp_path: Path):
    storage = FileStorage(tmp_path)
    entity_data = {
        "entity_id": "ent_001",
        "title": "Test Product",
        "price": 199.99,
        "tags": ["electronics", "gadgets"],
    }

    saved_path = await storage.save_entity_json("ent_001", entity_data)
    assert saved_path.exists()
    assert saved_path.name == "ent_001.json"

    loaded = await storage.load_json(saved_path)
    assert loaded == entity_data


async def test_file_storage_save_evidence_and_load_json(tmp_path: Path):
    storage = FileStorage(tmp_path)
    evidence_data = {
        "evidence_id": "evi_001",
        "type": "screenshot",
        "timestamp": "2026-08-27T00:00:00Z",
    }

    saved_path = await storage.save_evidence_json("evi_001", evidence_data)
    assert saved_path.exists()
    assert saved_path.name == "evi_001.json"

    loaded = await storage.load_json(saved_path)
    assert loaded == evidence_data


async def test_file_storage_load_json_missing(tmp_path: Path):
    storage = FileStorage(tmp_path)
    missing_path = tmp_path / "non_existent.json"
    assert await storage.load_json(missing_path) is None


async def test_file_storage_event_jsonl_single(tmp_path: Path):
    storage = FileStorage(tmp_path)
    event = {"event_id": "evt_1", "type": "STEP_START", "step": 1}

    await storage.append_event_jsonl(event)
    events = await storage.read_events_jsonl()

    assert len(events) == 1
    assert events[0] == event


async def test_file_storage_event_jsonl_multiple(tmp_path: Path):
    storage = FileStorage(tmp_path)
    events_to_write = [
        {"event_id": f"evt_{i}", "type": "VISIT_PAGE", "index": i}
        for i in range(3)
    ]

    for ev in events_to_write:
        await storage.append_event_jsonl(ev)

    read_events = await storage.read_events_jsonl()
    assert len(read_events) == 3
    assert read_events == events_to_write


async def test_file_storage_read_events_jsonl_missing(tmp_path: Path):
    storage = FileStorage(tmp_path)
    events = await storage.read_events_jsonl()
    assert events == []


# ---------------------------------------------------------------------------
# DomainJSONEncoder & Serialization Tests
# ---------------------------------------------------------------------------


def test_domain_json_encoder_direct_instance():
    encoder = DomainJSONEncoder()
    dt = datetime(2026, 8, 27, 12, 0, 0, tzinfo=UTC)
    assert encoder.default(dt) == "2026-08-27T12:00:00+00:00"
    assert encoder.default(SampleStatus.ACTIVE) == "ACTIVE"
    assert encoder.default(Path("/tmp")) == str(Path("/tmp"))
    assert encoder.default({1, 2}) == [1, 2] or encoder.default({1, 2}) == [2, 1]


def test_domain_json_encoder_datetime():
    dt = datetime(2026, 8, 27, 12, 30, 45, tzinfo=UTC)
    encoded = to_json({"time": dt})
    parsed = from_json(encoded)
    assert parsed == {"time": "2026-08-27T12:30:45+00:00"}


def test_domain_json_encoder_enum():
    encoded = to_json({"status": SampleStatus.ACTIVE})
    parsed = from_json(encoded)
    assert parsed == {"status": "ACTIVE"}


def test_domain_json_encoder_dataclass():
    dt = datetime(2026, 8, 27, 10, 0, 0, tzinfo=UTC)
    entity = SampleEntity(
        id="ent_123",
        name="Smartphone",
        status=SampleStatus.ACTIVE,
        created_at=dt,
        path=Path("/tmp/sample.png"),
    )

    encoded = to_json(entity)
    parsed = from_json(encoded)

    assert parsed == {
        "id": "ent_123",
        "name": "Smartphone",
        "status": "ACTIVE",
        "created_at": "2026-08-27T10:00:00+00:00",
        "path": str(Path("/tmp/sample.png")),
    }


def test_domain_json_encoder_path_and_set():
    p = Path("/var/log/app.log")
    encoded = to_json({"file": p, "tags": {"a", "b"}})
    parsed = from_json(encoded)
    assert parsed["file"] == str(p)
    assert set(parsed["tags"]) == {"a", "b"}


# ---------------------------------------------------------------------------
# Fingerprinting & Utility Tests
# ---------------------------------------------------------------------------


def test_fingerprint_text_normalization():
    fp1 = fingerprint_text("Hello  World")
    fp2 = fingerprint_text("hello world")
    fp3 = fingerprint_text("  HELLO   WORLD  \n")
    assert fp1 == fp2
    assert fp2 == fp3


def test_fingerprint_text_length_and_hex():
    fp = fingerprint_text("Sample Product Title 100$")
    assert len(fp) == 32
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_image_valid_and_invalid():
    # Valid 1x1 image
    png_bytes = make_sample_png_bytes("green", size=(1, 1))
    fp = fingerprint_image(png_bytes)
    assert fp is not None
    assert isinstance(fp, str)
    assert len(fp) > 0

    # Empty bytes
    assert fingerprint_image(b"") is None

    # Corrupted / invalid bytes
    assert fingerprint_image(b"not_an_image_bytes") is None


def test_hamming_distance_identical():
    assert hamming_distance("ff", "ff") == 0
    assert hamming_distance("1234567890abcdef", "1234567890abcdef") == 0


def test_hamming_distance_different():
    dist = hamming_distance("ff", "00")
    assert dist == 8  # 0xff ^ 0x00 = 0b11111111 (8 bits)

    assert hamming_distance("0", "1") == 1
    assert hamming_distance("0", "3") == 2


def test_hamming_distance_invalid_input():
    with pytest.raises(ValueError):
        hamming_distance("xyz", "00")


def test_normalize_title():
    assert normalize_title("  T10-Pro™  ") == "t10 pro"
    assert normalize_title("Brand™ Widget® ©2026") == "brand widget 2026"
    assert normalize_title("Alpha_Beta-Gamma__Delta") == "alpha beta gamma delta"
    assert normalize_title("   Multiple     Spaces   ") == "multiple spaces"
    assert normalize_title("") == ""
