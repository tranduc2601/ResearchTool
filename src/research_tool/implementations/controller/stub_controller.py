"""Stub ComputerController — records calls without performing real actions."""

from __future__ import annotations

from dataclasses import dataclass

from typing import Any

import structlog

from research_tool.interfaces import ComputerController

logger = structlog.get_logger()


@dataclass
class CallRecord:
    method: str
    args: dict[str, Any]


class StubController(ComputerController):
    """
    Records all calls in self.calls without touching the real display.
    Useful for testing orchestrator logic without a live screen.

    screenshot() returns a 1x1 white PNG bytes.
    get_active_url() returns self.current_url (default None).
    get_window_title() returns self.current_title (default "Stub").
    """

    def __init__(self) -> None:
        self.calls: list[CallRecord] = []
        self.current_url: str | None = None
        self.current_title: str = "Stub"
        # Minimal valid 1x1 white PNG
        self._stub_png: bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    def _record(self, method: str, **kwargs) -> None:
        self.calls.append(CallRecord(method=method, args=kwargs))
        logger.debug(f"StubController.{method}", **kwargs)

    async def screenshot(self) -> bytes:
        self._record("screenshot")
        return self._stub_png

    async def move(self, x: int, y: int, smooth: bool = True) -> None:
        self._record("move", x=x, y=y, smooth=smooth)

    async def click(self, x: int, y: int, button: str = "left") -> None:
        self._record("click", x=x, y=y, button=button)

    async def double_click(self, x: int, y: int) -> None:
        self._record("double_click", x=x, y=y)

    async def scroll(self, x: int, y: int, dy: int) -> None:
        self._record("scroll", x=x, y=y, dy=dy)

    async def type_text(self, text: str, clear_first: bool = False) -> None:
        self._record("type_text", text=text, clear_first=clear_first)

    async def press_key(self, key: str) -> None:
        self._record("press_key", key=key)

    async def back(self) -> None:
        self._record("back")

    async def get_window_title(self) -> str:
        self._record("get_window_title")
        return self.current_title

    async def get_active_url(self) -> str | None:
        self._record("get_active_url")
        return self.current_url
