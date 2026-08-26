"""Abstract interface for the OCR provider.

OCR complements the VLM for text-heavy regions where reading precise text
is cheaper than a full vision inference pass. It is NOT a replacement for
vision — it cannot understand UI layout or semantic context.

Implementations: research_tool.implementations.ocr
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from research_tool.interfaces.vision_provider import BoundingBox


@dataclass
class OCRWord:
    text: str
    bounding_box: BoundingBox
    confidence: float = 1.0


@dataclass
class OCRResult:
    full_text: str
    words: list[OCRWord]
    language: str | None = None
    raw_output: dict | None = None


class OCRProvider(ABC):
    @abstractmethod
    async def extract_text(
        self,
        image: bytes,
        region: BoundingBox | None = None,
        language_hint: str = "vi",
    ) -> OCRResult:
        """Extract text from an image or image region."""
        ...
