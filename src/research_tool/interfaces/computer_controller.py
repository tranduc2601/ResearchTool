"""Abstract interface for computer control (mouse, keyboard, screen).

The ComputerController is the Agent's "body" — it translates high-level
actions into actual input events on Windows or Android (via scrcpy/ADB).

Two concrete implementations will exist:
- WindowsController (pyautogui / win32)
- AndroidScrcpyController (scrcpy + ADB)

The core uses this interface exclusively, never a concrete controller.
"""

from abc import ABC, abstractmethod
from research_tool.domain import ActionResult


class ComputerController(ABC):
    @abstractmethod
    async def screenshot(self) -> bytes:
        """Capture the current screen as PNG bytes."""
        ...

    @abstractmethod
    async def move(self, x: int, y: int, smooth: bool = True) -> ActionResult:
        """Move the mouse/pointer to (x, y)."""
        ...

    @abstractmethod
    async def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Click at (x, y). button: 'left' | 'right' | 'middle'."""
        ...

    @abstractmethod
    async def double_click(self, x: int, y: int) -> ActionResult:
        """Double-click at (x, y)."""
        ...

    @abstractmethod
    async def scroll(self, x: int, y: int, dy: int) -> ActionResult:
        """Scroll at (x, y) by dy clicks (positive = down, negative = up)."""
        ...

    @abstractmethod
    async def type_text(self, text: str, clear_first: bool = False) -> ActionResult:
        """Type text at the current focus position."""
        ...

    @abstractmethod
    async def press_key(self, key: str) -> ActionResult:
        """Press a key by name (e.g. 'enter', 'escape', 'ctrl+a')."""
        ...

    @abstractmethod
    async def back(self) -> ActionResult:
        """Navigate back (browser back or Android back gesture)."""
        ...

    @abstractmethod
    async def get_window_title(self) -> str:
        """Return the active window/tab title."""
        ...

    @abstractmethod
    async def get_active_url(self) -> str | None:
        """Return the active URL if in a browser context, else None."""
        ...
