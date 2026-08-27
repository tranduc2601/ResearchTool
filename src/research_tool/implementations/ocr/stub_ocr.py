"""Stub OCRProvider — returns empty OCR result for testing."""

from __future__ import annotations

import structlog

from research_tool.interfaces import BoundingBox, OCRProvider, OCRResult

logger = structlog.get_logger()


class StubOCRProvider(OCRProvider):
    """
    Returns empty OCR results. Useful for pipeline testing without a real OCR engine.
    Configurable: pass `fixed_text` to return a specific string.
    """

    def __init__(self, fixed_text: str = ""):
        self.fixed_text = fixed_text

    async def extract_text(
        self,
        image: bytes,
        region: BoundingBox | None = None,
        language_hint: str = "vi",
    ) -> OCRResult:
        logger.debug(
            "StubOCRProvider.extract_text",
            image_bytes=len(image),
            region=region,
        )
        return OCRResult(
            full_text=self.fixed_text,
            words=[],
            language=language_hint,
            raw_output={"stub": True},
        )
