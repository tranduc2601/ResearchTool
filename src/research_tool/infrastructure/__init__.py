"""Infrastructure layer: database, file storage, serialization."""

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

__all__ = [
    "FileStorage",
    "DomainJSONEncoder",
    "to_json",
    "from_json",
    "fingerprint_text",
    "fingerprint_image",
    "hamming_distance",
    "normalize_title",
]
