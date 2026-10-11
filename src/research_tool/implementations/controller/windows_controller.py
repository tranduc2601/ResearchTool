"""Windows physical control implementation using PyAutoGUI and MSS."""
import asyncio
import pyautogui
import mss
import pygetwindow
import structlog
from typing import Optional

from research_tool.interfaces.computer_controller import ComputerController
from research_tool.domain.action import ActionResult, ActionStatus
from research_tool.interfaces.coordinate_mapper import CoordinateMapper

logger = structlog.get_logger()

# Configure pyautogui
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5  # Add a small delay between PyAutoGUI actions

class WindowsController(ComputerController):
    """Controls a Windows machine physically."""
    
    def __init__(self, mapper: CoordinateMapper | None = None):
        self.mapper = mapper
        self.sct = mss.mss()

    def _map_coordinates(self, x: int, y: int) -> tuple[int, int]:
        if self.mapper:
            return self.mapper.vision_to_screen(x, y)
        return x, y

    async def get_active_url(self) -> str | None:
        """
        Extract active URL. On Windows, this is difficult without accessibility hooks.
        For now, we return None and rely on the Vision model reading the URL bar.
        """
        return None

    async def get_window_title(self) -> str | None:
        """Get the title of the currently active window."""
        try:
            window = pygetwindow.getActiveWindow()
            if window:
                return window.title
        except Exception as e:
            logger.warning("failed_to_get_active_window", error=str(e))
        return None

    async def screenshot(self) -> bytes:
        """Take a screenshot of the primary monitor."""
        # This blocks briefly, but mss is fast enough (usually <50ms) to run in the event loop directly
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        # We need PNG bytes. mss provides raw pixels, so we'll use Pillow to encode.
        from PIL import Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def move(self, x: int, y: int, smooth: bool = True) -> ActionResult:
        """Move the mouse pointer to the given coordinates."""
        try:
            target_x, target_y = self._map_coordinates(x, y)
            duration = 0.2 if smooth else 0.0
            await asyncio.to_thread(pyautogui.moveTo, target_x, target_y, duration)
            return ActionResult(ActionStatus.SUCCESS, f"Moved to ({target_x}, {target_y})")
        except pyautogui.FailSafeException:
            return ActionResult(ActionStatus.BLOCKED, "Failsafe triggered during move")
        except Exception as e:
            logger.exception("windows_move_failed")
            return ActionResult(ActionStatus.FAILURE, str(e))

    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Click at the given coordinates."""
        try:
            target_x, target_y = self._map_coordinates(x, y)
            await asyncio.to_thread(pyautogui.click, x=target_x, y=target_y, button=button)
            return ActionResult(ActionStatus.SUCCESS, f"Clicked {button} at ({target_x}, {target_y})")
        except pyautogui.FailSafeException:
            return ActionResult(ActionStatus.BLOCKED, "Failsafe triggered during click")
        except Exception as e:
            logger.exception("windows_click_failed")
            return ActionResult(ActionStatus.FAILURE, str(e))

    async def double_click(self, x: int, y: int) -> ActionResult:
        """Double-click at the given coordinates."""
        try:
            target_x, target_y = self._map_coordinates(x, y)
            await asyncio.to_thread(pyautogui.doubleClick, x=target_x, y=target_y)
            return ActionResult(ActionStatus.SUCCESS, f"Double-clicked at ({target_x}, {target_y})")
        except pyautogui.FailSafeException:
            return ActionResult(ActionStatus.BLOCKED, "Failsafe triggered during double_click")
        except Exception as e:
            logger.exception("windows_double_click_failed")
            return ActionResult(ActionStatus.FAILURE, str(e))

    async def type_text(self, text: str, clear_first: bool = False) -> ActionResult:
        """Type the given text."""
        try:
            if clear_first:
                # ctrl+a then backspace to clear
                await asyncio.to_thread(pyautogui.hotkey, 'ctrl', 'a')
                await asyncio.to_thread(pyautogui.press, 'backspace')
            
            # Use pyperclip to support Unicode (like Vietnamese) safely on Windows
            import pyperclip
            pyperclip.copy(text)
            await asyncio.to_thread(pyautogui.hotkey, 'ctrl', 'v')
            
            return ActionResult(ActionStatus.SUCCESS, f"Typed '{text}'")
        except Exception as e:
            logger.exception("windows_type_failed")
            return ActionResult(ActionStatus.FAILURE, str(e))

    async def scroll(self, x: int, y: int, dy: int) -> ActionResult:
        """Scroll at the given coordinates."""
        try:
            target_x, target_y = self._map_coordinates(x, y)
            # Move to location then scroll
            await asyncio.to_thread(pyautogui.moveTo, x=target_x, y=target_y)
            # PyAutoGUI scroll amount varies by OS. Usually -120 or 120 per click on Windows
            scroll_amount = dy * 10
            await asyncio.to_thread(pyautogui.scroll, clicks=scroll_amount)
            return ActionResult(ActionStatus.SUCCESS, f"Scrolled by {scroll_amount} at ({target_x}, {target_y})")
        except pyautogui.FailSafeException:
            return ActionResult(ActionStatus.BLOCKED, "Failsafe triggered during scroll")
        except Exception as e:
            logger.exception("windows_scroll_failed")
            return ActionResult(ActionStatus.FAILURE, str(e))

    async def press_key(self, key: str) -> ActionResult:
        """Press a specific key (e.g. 'enter', 'esc')."""
        try:
            await asyncio.to_thread(pyautogui.press, key)
            return ActionResult(ActionStatus.SUCCESS, f"Pressed {key}")
        except Exception as e:
            logger.exception("windows_press_failed")
            return ActionResult(ActionStatus.FAILURE, str(e))

    async def back(self) -> ActionResult:
        """Navigate back. Maps to alt+left or browser back button on Windows."""
        try:
            # Most common way to go back in Windows apps/browsers
            await asyncio.to_thread(pyautogui.hotkey, 'alt', 'left')
            return ActionResult(ActionStatus.SUCCESS, "Executed Alt+Left for BACK")
        except Exception as e:
            return ActionResult(ActionStatus.FAILURE, str(e))
