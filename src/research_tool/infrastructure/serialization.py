"""JSON serialization helpers and content fingerprinting utilities."""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import imagehash
from PIL import Image


class DomainJSONEncoder(json.JSONEncoder):
    """
    Extends json.JSONEncoder to handle:
    - datetime -> ISO-8601 string
    - Enum -> .value
    - dataclass -> dict (via dataclasses.asdict)
    - Path -> str
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        return super().default(obj)


def to_json(obj: Any, indent: int | None = None) -> str:
    """Serialize obj to JSON string using DomainJSONEncoder."""
    return json.dumps(obj, cls=DomainJSONEncoder, indent=indent)


def from_json(s: str) -> Any:
    """Parse a JSON string to dict or list."""
    return json.loads(s)


def fingerprint_text(text: str) -> str:
    """
    Fast stable fingerprint for text content (e.g. product title + price).
    Normalizes whitespace, lowercases, strips, then SHA-256 first 16 bytes -> hex.
    Returns a 32-char hex string.
    """
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def fingerprint_image(image_bytes: bytes) -> str | None:
    """
    Perceptual hash for screenshot deduplication.
    Uses imagehash.phash on the PIL image.
    Returns the hash as a hex string, or None if image cannot be parsed.
    """
    if not image_bytes:
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
        phash = imagehash.phash(img)
        return str(phash)
    except Exception:
        return None


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """
    Compute bit-level hamming distance between two hex-encoded hashes.
    Used to compare perceptual image hashes.
    Returns int distance (0 = identical, higher = more different).
    """
    try:
        a = int(hash_a, 16)
        b = int(hash_b, 16)
        return bin(a ^ b).count("1")
    except (ValueError, TypeError):
        raise ValueError(f"Invalid hex string for hamming distance: '{hash_a}', '{hash_b}'")


def normalize_title(title: str) -> str:
    """
    Normalize a product/entity title for dedup comparison:
    - lowercase
    - strip leading/trailing whitespace
    - collapse multiple spaces
    - remove common noise characters: ™ ® © _ -
    Returns the normalized string.
    """
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r"[™®©]", "", t)
    t = re.sub(r"[-_]", " ", t)
    return " ".join(t.split())
