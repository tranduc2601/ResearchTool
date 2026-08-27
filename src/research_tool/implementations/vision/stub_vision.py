"""Stub VisionProvider — returns fixed deterministic results for testing."""

from __future__ import annotations

import structlog

from research_tool.domain import Confidence, PageType, WorldState, ActionCommand, ActionType
from research_tool.interfaces import (
    BoundingBox,
    ElementLocation,
    UIElement,
    VisionProvider,
    VisionResult,
)

logger = structlog.get_logger()


class StubVisionProvider(VisionProvider):
    """
    Returns a fixed VisionResult for every screenshot.
    Useful for wiring the pipeline without a real VLM.

    Configurable via constructor:
        default_page_type: PageType to return (default SEARCH_RESULT)
        default_confidence: Confidence to return (default KNOWN)
        elements: list of UIElement to return
    """

    def __init__(
        self,
        default_page_type: PageType = PageType.SEARCH_RESULT,
        default_confidence: Confidence = Confidence.KNOWN,
        elements: list[UIElement] | None = None,
        default_next_action: ActionCommand | None = None,
    ):
        self.default_page_type = default_page_type
        self.default_confidence = default_confidence
        self.elements = elements or []
        self.default_next_action = default_next_action or ActionCommand(action_type=ActionType.GOAL_MET)

    async def analyze_screen(
        self, screenshot: bytes, context: WorldState, query: str = ""
    ) -> VisionResult:
        logger.debug(
            "StubVisionProvider.analyze_screen",
            query=query,
            screenshot_bytes=len(screenshot),
        )
        return VisionResult(
            page_type=self.default_page_type,
            detected_elements=self.elements,
            current_entity_name=None,
            confidence=self.default_confidence,
            next_action=self.default_next_action,
            raw_output={"stub": True},
        )

    async def locate_element(
        self, screenshot: bytes, description: str
    ) -> ElementLocation | None:
        logger.debug("StubVisionProvider.locate_element", description=description)
        # Return a fixed center location for testing
        return ElementLocation(
            bounding_box=BoundingBox(x=100, y=100, width=200, height=50),
            confidence=0.9,
            element_type="stub_element",
            label=description,
        )
