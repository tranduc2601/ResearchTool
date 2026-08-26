"""Abstract interfaces that decouple core logic from implementations."""

from research_tool.interfaces.computer_controller import ComputerController
from research_tool.interfaces.ocr_provider import OCRProvider, OCRResult, OCRWord
from research_tool.interfaces.platform_adapter import PlatformAdapter
from research_tool.interfaces.vision_provider import (
    BoundingBox,
    ElementLocation,
    UIElement,
    VisionProvider,
    VisionResult,
)

__all__ = [
    "BoundingBox",
    "UIElement",
    "VisionResult",
    "ElementLocation",
    "VisionProvider",
    "OCRWord",
    "OCRResult",
    "OCRProvider",
    "ComputerController",
    "PlatformAdapter",
]
