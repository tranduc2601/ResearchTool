"""Abstract interface for the Vision/VLM provider.

The VisionProvider is responsible for:
- Analyzing screenshots to understand the current UI state
- Locating specific UI elements by natural-language description
- Supporting grounding (screenshot → coordinate) for computer control

The core never imports a concrete implementation.
Implementations live in research_tool.implementations.vision.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from research_tool.domain import Confidence, PageType, WorldState


@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


@dataclass
class UIElement:
    element_type: str  # "search_box" | "product_card" | "button" | "review_item" | ...
    bounding_box: BoundingBox
    label: str | None = None
    confidence: float = 1.0


@dataclass
class VisionResult:
    page_type: PageType
    detected_elements: list[UIElement]
    current_entity_name: str | None
    confidence: Confidence
    suggested_action: str | None  # natural-language suggestion
    raw_output: dict | None = None  # model's raw JSON output (for audit)
    screenshot_used: bytes | None = None


@dataclass
class ElementLocation:
    bounding_box: BoundingBox
    confidence: float
    element_type: str
    label: str | None = None


class VisionProvider(ABC):
    @abstractmethod
    async def analyze_screen(
        self,
        screenshot: bytes,
        context: WorldState,
        query: str = "",
    ) -> VisionResult:
        """Analyze a screenshot in context and return UI understanding."""
        ...

    @abstractmethod
    async def locate_element(
        self,
        screenshot: bytes,
        description: str,
    ) -> ElementLocation | None:
        """Find a UI element by natural-language description. Returns None if not found."""
        ...
