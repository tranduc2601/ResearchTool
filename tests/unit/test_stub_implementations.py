"""Unit tests for stub implementations of core interfaces."""

import pytest

from research_tool.domain import Confidence, PageType, WorldState
from research_tool.implementations import (
    CallRecord,
    GenericBrowserAdapter,
    StubController,
    StubOCRProvider,
    StubVisionProvider,
)
from research_tool.interfaces import (
    BoundingBox,
    ComputerController,
    ElementLocation,
    OCRProvider,
    OCRResult,
    PlatformAdapter,
    UIElement,
    VisionProvider,
    VisionResult,
)


def _make_dummy_world_state() -> WorldState:
    return WorldState(
        run_id="test-run-1",
        platform="generic_browser",
        app="chrome",
        page_type=PageType.SEARCH_RESULT,
        confidence=Confidence.KNOWN,
    )


# =============================================================================
# StubVisionProvider Tests
# =============================================================================


def test_stub_vision_provider_is_instance_of_vision_provider():
    provider = StubVisionProvider()
    assert isinstance(provider, VisionProvider)


@pytest.mark.asyncio
async def test_stub_vision_provider_analyze_screen_defaults():
    provider = StubVisionProvider()
    dummy_screenshot = b"fake_png_data"
    context = _make_dummy_world_state()

    result = await provider.analyze_screen(
        screenshot=dummy_screenshot,
        context=context,
        query="search something",
    )

    assert isinstance(result, VisionResult)
    assert result.page_type == PageType.SEARCH_RESULT
    assert result.confidence == Confidence.KNOWN
    assert result.detected_elements == []
    assert result.current_entity_name is None
    assert result.suggested_action is None
    assert result.raw_output == {"stub": True}


@pytest.mark.asyncio
async def test_stub_vision_provider_custom_configuration():
    elem = UIElement(
        element_type="button",
        bounding_box=BoundingBox(x=10, y=20, width=50, height=30),
        label="Buy Now",
    )
    provider = StubVisionProvider(
        default_page_type=PageType.PRODUCT_PAGE,
        default_confidence=Confidence.UNCERTAIN,
        elements=[elem],
    )
    result = await provider.analyze_screen(b"bytes", _make_dummy_world_state())

    assert result.page_type == PageType.PRODUCT_PAGE
    assert result.confidence == Confidence.UNCERTAIN
    assert len(result.detected_elements) == 1
    assert result.detected_elements[0].label == "Buy Now"


@pytest.mark.asyncio
async def test_stub_vision_provider_locate_element():
    provider = StubVisionProvider()
    location = await provider.locate_element(b"bytes", "search input field")

    assert location is not None
    assert isinstance(location, ElementLocation)
    assert location.bounding_box == BoundingBox(x=100, y=100, width=200, height=50)
    assert location.confidence == 0.9
    assert location.element_type == "stub_element"
    assert location.label == "search input field"


# =============================================================================
# StubOCRProvider Tests
# =============================================================================


def test_stub_ocr_provider_is_instance_of_ocr_provider():
    provider = StubOCRProvider()
    assert isinstance(provider, OCRProvider)


@pytest.mark.asyncio
async def test_stub_ocr_provider_default_empty_text():
    provider = StubOCRProvider()
    result = await provider.extract_text(b"dummy_image")

    assert isinstance(result, OCRResult)
    assert result.full_text == ""
    assert result.words == []
    assert result.language == "vi"
    assert result.raw_output == {"stub": True}


@pytest.mark.asyncio
async def test_stub_ocr_provider_fixed_text():
    provider = StubOCRProvider(fixed_text="hello")
    region = BoundingBox(x=0, y=0, width=100, height=50)
    result = await provider.extract_text(
        image=b"image_bytes",
        region=region,
        language_hint="en",
    )

    assert result.full_text == "hello"
    assert result.words == []
    assert result.language == "en"
    assert result.raw_output == {"stub": True}


# =============================================================================
# StubController Tests
# =============================================================================


def test_stub_controller_is_instance_of_computer_controller():
    controller = StubController()
    assert isinstance(controller, ComputerController)


@pytest.mark.asyncio
async def test_stub_controller_screenshot_returns_non_empty_bytes():
    controller = StubController()
    screenshot_bytes = await controller.screenshot()

    assert isinstance(screenshot_bytes, bytes)
    assert len(screenshot_bytes) > 0
    assert screenshot_bytes.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.asyncio
async def test_stub_controller_records_all_calls():
    controller = StubController()
    assert controller.calls == []

    await controller.screenshot()
    await controller.move(100, 200, smooth=False)
    await controller.click(10, 20, button="left")
    await controller.double_click(30, 40)
    await controller.scroll(50, 60, dy=-3)
    await controller.type_text("search query", clear_first=True)
    await controller.press_key("enter")
    await controller.back()
    title = await controller.get_window_title()
    url = await controller.get_active_url()

    assert len(controller.calls) == 10

    # Call 0: screenshot
    assert controller.calls[0] == CallRecord(method="screenshot", args={})

    # Call 1: move
    assert controller.calls[1] == CallRecord(
        method="move", args={"x": 100, "y": 200, "smooth": False}
    )

    # Call 2: click
    assert controller.calls[2].method == "click"
    assert controller.calls[2].args["x"] == 10
    assert controller.calls[2].args["y"] == 20
    assert controller.calls[2].args["button"] == "left"

    # Call 3: double_click
    assert controller.calls[3] == CallRecord(
        method="double_click", args={"x": 30, "y": 40}
    )

    # Call 4: scroll
    assert controller.calls[4] == CallRecord(
        method="scroll", args={"x": 50, "y": 60, "dy": -3}
    )

    # Call 5: type_text
    assert controller.calls[5] == CallRecord(
        method="type_text", args={"text": "search query", "clear_first": True}
    )

    # Call 6: press_key
    assert controller.calls[6] == CallRecord(
        method="press_key", args={"key": "enter"}
    )

    # Call 7: back
    assert controller.calls[7] == CallRecord(method="back", args={})

    # Call 8: get_window_title
    assert controller.calls[8] == CallRecord(method="get_window_title", args={})
    assert title == "Stub"

    # Call 9: get_active_url
    assert controller.calls[9] == CallRecord(method="get_active_url", args={})
    assert url is None


@pytest.mark.asyncio
async def test_stub_controller_click_args():
    controller = StubController()
    await controller.click(10, 20)

    assert len(controller.calls) == 1
    assert controller.calls[-1].method == "click"
    assert controller.calls[-1].args["x"] == 10
    assert controller.calls[-1].args["y"] == 20
    assert controller.calls[-1].args["button"] == "left"


@pytest.mark.asyncio
async def test_stub_controller_get_active_url_default_and_set():
    controller = StubController()
    assert await controller.get_active_url() is None

    controller.current_url = "https://example.com"
    assert await controller.get_active_url() == "https://example.com"


@pytest.mark.asyncio
async def test_stub_controller_window_title_configurable():
    controller = StubController()
    assert await controller.get_window_title() == "Stub"

    controller.current_title = "My Web Browser"
    assert await controller.get_window_title() == "My Web Browser"


# =============================================================================
# GenericBrowserAdapter Tests
# =============================================================================


def test_generic_browser_adapter_is_instance_of_platform_adapter():
    adapter = GenericBrowserAdapter()
    assert isinstance(adapter, PlatformAdapter)


def test_generic_browser_adapter_platform_name():
    adapter = GenericBrowserAdapter()
    assert adapter.platform_name == "generic_browser"


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com/search?q=ban+lam+viec", PageType.SEARCH_RESULT),
        ("https://google.com/search?query=test", PageType.SEARCH_RESULT),
        ("https://shopee.vn/search?keyword=abc", PageType.SEARCH_RESULT),
        ("https://site.org/search/items", PageType.SEARCH_RESULT),
        ("https://shopee.vn/product/123", None),
        ("https://example.com/item/456", None),
        ("", PageType.UNKNOWN),
        ("about:blank", PageType.UNKNOWN),
    ],
)
def test_generic_browser_adapter_identify_page_type(url, expected):
    adapter = GenericBrowserAdapter()
    assert adapter.identify_page_type(url, "") == expected


def test_generic_browser_adapter_extract_entity_id_from_url():
    adapter = GenericBrowserAdapter()
    assert adapter.extract_entity_id_from_url("anything") is None
    assert adapter.extract_entity_id_from_url("https://example.com/123") is None
