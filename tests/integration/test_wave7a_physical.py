"""Physical test harness for Wave 7A."""
import pytest
import asyncio
from pathlib import Path

from research_tool.domain.action import ActionStatus
from research_tool.core.scaling_mapper import ScalingCoordinateMapper
from research_tool.implementations.controller.windows_controller import WindowsController
from research_tool.implementations.controller.android_controller import AndroidController

@pytest.mark.skip(reason="Manual physical test - requires local GUI")
@pytest.mark.asyncio
async def test_windows_physical_control():
    """Test Windows control via PyAutoGUI."""
    # Assuming the vision model expects 1000x1000 and the screen is 1920x1080
    mapper = ScalingCoordinateMapper(1000, 1000, 1920, 1080)
    controller = WindowsController(mapper=mapper)
    
    # Test screenshot
    screenshot = await controller.screenshot()
    assert len(screenshot) > 0
    assert screenshot.startswith(b"\x89PNG")
    
    # Test mapping & click (clicks middle of screen)
    result = await controller.click(500, 500)
    assert result.status == ActionStatus.SUCCESS
    
    # Test typing
    await asyncio.sleep(0.5)
    result = await controller.type_text("test")
    assert result.status == ActionStatus.SUCCESS
    
    # Test scrolling
    await asyncio.sleep(0.5)
    result = await controller.scroll(500, 500, dy=-1)
    assert result.status == ActionStatus.SUCCESS

@pytest.mark.skip(reason="Manual physical test - requires connected Android device")
@pytest.mark.asyncio
async def test_android_physical_control():
    """Test Android control via ADB."""
    # Assuming device is 1080x2400
    mapper = ScalingCoordinateMapper(1000, 1000, 1080, 2400)
    controller = AndroidController(mapper=mapper)
    
    # Test screenshot
    screenshot = await controller.screenshot()
    assert len(screenshot) > 0
    assert screenshot.startswith(b"\x89PNG")
    
    # Test click (center)
    result = await controller.click(500, 500)
    assert result.status == ActionStatus.SUCCESS
    
    # Test typing
    await asyncio.sleep(1.0)
    result = await controller.type_text("hello")
    assert result.status == ActionStatus.SUCCESS
    
    # Test back button
    await asyncio.sleep(1.0)
    result = await controller.back()
    assert result.status == ActionStatus.SUCCESS
