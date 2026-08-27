"""Unit tests for abstract interface contracts and supporting dataclasses."""

import pytest

from research_tool.domain import ActionCommand, ActionType, Confidence, PageType, WorldState
from research_tool.interfaces import (
    BoundingBox,
    ComputerController,
    ElementLocation,
    OCRProvider,
    OCRResult,
    OCRWord,
    PlatformAdapter,
    UIElement,
    VisionProvider,
    VisionResult,
)

# =============================================================================
# BoundingBox & Supporting Dataclass Tests
# =============================================================================


def test_bounding_box_center_calculation():
    bbox = BoundingBox(x=10, y=20, width=100, height=80)
    assert bbox.center == (60, 60)


def test_bounding_box_center_odd_dimensions():
    bbox = BoundingBox(x=0, y=0, width=15, height=25)
    # 0 + 15 // 2 = 7, 0 + 25 // 2 = 12
    assert bbox.center == (7, 12)


def test_ui_element_instantiation_and_defaults():
    bbox = BoundingBox(x=10, y=20, width=100, height=50)
    element = UIElement(element_type="search_box", bounding_box=bbox)
    assert element.element_type == "search_box"
    assert element.bounding_box == bbox
    assert element.label is None
    assert element.confidence == 1.0

    element_with_label = UIElement(
        element_type="button",
        bounding_box=bbox,
        label="Submit",
        confidence=0.95,
    )
    assert element_with_label.label == "Submit"
    assert element_with_label.confidence == 0.95


def test_element_location_instantiation_and_defaults():
    bbox = BoundingBox(x=5, y=10, width=50, height=30)
    location = ElementLocation(
        bounding_box=bbox,
        confidence=0.9,
        element_type="button",
    )
    assert location.bounding_box == bbox
    assert location.confidence == 0.9
    assert location.element_type == "button"
    assert location.label is None

    location_with_label = ElementLocation(
        bounding_box=bbox,
        confidence=0.85,
        element_type="product_card",
        label="Shopee Item",
    )
    assert location_with_label.label == "Shopee Item"


def test_vision_result_minimal_and_full_instantiation():
    bbox = BoundingBox(x=0, y=0, width=100, height=100)
    element = UIElement(element_type="product_card", bounding_box=bbox)

    # Minimal required fields
    result = VisionResult(
        page_type=PageType.PRODUCT_PAGE,
        detected_elements=[element],
        current_entity_name="Product ABC",
        confidence=Confidence.KNOWN,
        next_action=ActionCommand(ActionType.SCROLL),
    )
    assert result.page_type == PageType.PRODUCT_PAGE
    assert len(result.detected_elements) == 1
    assert result.current_entity_name == "Product ABC"
    assert result.confidence == Confidence.KNOWN
    assert result.next_action.action_type == ActionType.SCROLL
    assert result.raw_output is None
    assert result.screenshot_used is None

    # Full fields
    full_result = VisionResult(
        page_type=PageType.SEARCH_RESULT,
        detected_elements=[],
        current_entity_name=None,
        confidence=Confidence.UNCERTAIN,
        next_action=ActionCommand(ActionType.WAIT),
        raw_output={"model": "test-vlm", "tokens": 120},
        screenshot_used=b"fake-png-bytes",
    )
    assert full_result.next_action.action_type == ActionType.WAIT
    assert full_result.raw_output == {"model": "test-vlm", "tokens": 120}
    assert full_result.screenshot_used == b"fake-png-bytes"


def test_ocr_word_and_ocr_result_instantiation():
    bbox = BoundingBox(x=10, y=20, width=50, height=15)
    word = OCRWord(text="Hello", bounding_box=bbox)
    assert word.text == "Hello"
    assert word.bounding_box == bbox
    assert word.confidence == 1.0

    result = OCRResult(full_text="Hello World", words=[word])
    assert result.full_text == "Hello World"
    assert len(result.words) == 1
    assert result.language is None
    assert result.raw_output is None

    result_full = OCRResult(
        full_text="Xin chao",
        words=[word],
        language="vi",
        raw_output={"engine": "tesseract"},
    )
    assert result_full.language == "vi"
    assert result_full.raw_output == {"engine": "tesseract"}


# =============================================================================
# VisionProvider ABC Tests
# =============================================================================


def test_vision_provider_is_abstract():
    with pytest.raises(TypeError) as exc_info:
        VisionProvider()  # type: ignore[abstract]
    assert "Can't instantiate abstract class" in str(exc_info.value)


@pytest.mark.asyncio
async def test_concrete_vision_provider_can_be_instantiated():
    class DummyVisionProvider(VisionProvider):
        async def analyze_screen(
            self,
            screenshot: bytes,
            context: WorldState,
            query: str = "",
        ) -> VisionResult:
            return VisionResult(
                page_type=PageType.SEARCH_RESULT,
                detected_elements=[],
                current_entity_name=None,
                confidence=Confidence.KNOWN,
                next_action=ActionCommand(ActionType.GOAL_MET),
            )

        async def locate_element(
            self,
            screenshot: bytes,
            description: str,
        ) -> ElementLocation | None:
            return None

    provider = DummyVisionProvider()
    assert isinstance(provider, VisionProvider)

    state = WorldState(run_id="run-1", platform="shopee", app="chrome")
    res = await provider.analyze_screen(b"screenshot", state)
    assert res.page_type == PageType.SEARCH_RESULT
    loc = await provider.locate_element(b"screenshot", "search bar")
    assert loc is None


# =============================================================================
# OCRProvider ABC Tests
# =============================================================================


def test_ocr_provider_is_abstract():
    with pytest.raises(TypeError) as exc_info:
        OCRProvider()  # type: ignore[abstract]
    assert "Can't instantiate abstract class" in str(exc_info.value)


@pytest.mark.asyncio
async def test_concrete_ocr_provider_can_be_instantiated():
    class DummyOCRProvider(OCRProvider):
        async def extract_text(
            self,
            image: bytes,
            region: BoundingBox | None = None,
            language_hint: str = "vi",
        ) -> OCRResult:
            return OCRResult(full_text="Test Text", words=[])

    provider = DummyOCRProvider()
    assert isinstance(provider, OCRProvider)

    res = await provider.extract_text(b"image-bytes")
    assert res.full_text == "Test Text"


# =============================================================================
# ComputerController ABC Tests
# =============================================================================


def test_computer_controller_is_abstract():
    with pytest.raises(TypeError) as exc_info:
        ComputerController()  # type: ignore[abstract]
    assert "Can't instantiate abstract class" in str(exc_info.value)


@pytest.mark.asyncio
async def test_concrete_computer_controller_can_be_instantiated():
    class DummyComputerController(ComputerController):
        async def screenshot(self) -> bytes:
            return b"png-bytes"

        async def move(self, x: int, y: int, smooth: bool = True) -> None:
            pass

        async def click(self, x: int, y: int, button: str = "left") -> None:
            pass

        async def double_click(self, x: int, y: int) -> None:
            pass

        async def scroll(self, x: int, y: int, dy: int) -> None:
            pass

        async def type_text(self, text: str, clear_first: bool = False) -> None:
            pass

        async def press_key(self, key: str) -> None:
            pass

        async def back(self) -> None:
            pass

        async def get_window_title(self) -> str:
            return "Test Window"

        async def get_active_url(self) -> str | None:
            return "https://shopee.vn"

    controller = DummyComputerController()
    assert isinstance(controller, ComputerController)

    assert await controller.screenshot() == b"png-bytes"
    assert await controller.get_window_title() == "Test Window"
    assert await controller.get_active_url() == "https://shopee.vn"


# =============================================================================
# PlatformAdapter ABC Tests
# =============================================================================


def test_platform_adapter_is_abstract():
    with pytest.raises(TypeError) as exc_info:
        PlatformAdapter()  # type: ignore[abstract]
    assert "Can't instantiate abstract class" in str(exc_info.value)


def test_concrete_platform_adapter_can_be_instantiated():
    class DummyShopeeAdapter(PlatformAdapter):
        @property
        def platform_name(self) -> str:
            return "shopee"

        def identify_page_type(self, url: str, title: str) -> PageType | None:
            if "shopee.vn/search" in url:
                return PageType.SEARCH_RESULT
            return None

        def extract_entity_id_from_url(self, url: str) -> str | None:
            if "shopee.vn/product/" in url:
                return url.split("/")[-1]
            return None

    adapter = DummyShopeeAdapter()
    assert isinstance(adapter, PlatformAdapter)
    assert adapter.platform_name == "shopee"
    assert adapter.identify_page_type("https://shopee.vn/search?q=phone", "Search") == PageType.SEARCH_RESULT
    assert adapter.identify_page_type("https://other.vn", "Other") is None
    assert adapter.extract_entity_id_from_url("https://shopee.vn/product/12345") == "12345"
    assert adapter.extract_entity_id_from_url("https://shopee.vn/home") is None
