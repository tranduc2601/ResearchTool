"""Concrete implementations of core interfaces.

Real VLM, OCR, and controller implementations are added here as the
Vision PoC (Gate #1) progresses. Stubs are always available for testing.
"""

from research_tool.implementations.controller.stub_controller import (
    CallRecord,
    StubController,
)
from research_tool.implementations.ocr.stub_ocr import StubOCRProvider
from research_tool.implementations.platform.generic_browser import GenericBrowserAdapter
from research_tool.implementations.vision.stub_vision import StubVisionProvider

__all__ = [
    "CallRecord",
    "GenericBrowserAdapter",
    "StubController",
    "StubOCRProvider",
    "StubVisionProvider",
]
