"""Android physical control implementation using ADB."""
import asyncio
import structlog
from typing import Optional

from research_tool.interfaces.computer_controller import ComputerController
from research_tool.domain.action import ActionResult, ActionStatus
from research_tool.interfaces.coordinate_mapper import CoordinateMapper

logger = structlog.get_logger()

class AndroidController(ComputerController):
    """Controls an Android device physically using ADB or Scrcpy."""
    
    def __init__(
        self, 
        device_serial: str | None = None, 
        mapper: CoordinateMapper | None = None,
        use_scrcpy: bool = False,
        scrcpy_path: str = "scrcpy",
        adb_path: str = "adb"
    ):
        self.device_serial = device_serial
        self.mapper = mapper
        self.use_scrcpy = use_scrcpy
        self.scrcpy_path = scrcpy_path
        self.adb_path = adb_path
        self._scrcpy_process = None

    def _adb_prefix(self) -> list[str]:
        base = [self.adb_path]
        if self.device_serial:
            base.extend(["-s", self.device_serial])
        return base

    async def _run_adb(self, *args: str) -> tuple[int, bytes, bytes]:
        """Run an ADB command and return (returncode, stdout, stderr)."""
        cmd = self._adb_prefix() + list(args)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode or 0, stdout, stderr

    def _map_coordinates(self, x: int, y: int) -> tuple[int, int]:
        if self.mapper:
            return self.mapper.vision_to_screen(x, y)
        return x, y

    async def start_scrcpy(self):
        """Start the scrcpy background process for fast capture (v4l2/socket)."""
        if not self.use_scrcpy:
            return
            
        logger.info("Starting scrcpy background process...")
        cmd = [self.scrcpy_path, "--no-window", "--record", "tmp_scrcpy.mp4"]
        if self.device_serial:
            cmd.extend(["-s", self.device_serial])
            
        self._scrcpy_process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

    async def get_active_url(self) -> str | None:
        """
        Active URL extraction on Android via ADB is highly app-specific (requires UIAutomator).
        Returns None for now.
        """
        return None

    async def get_window_title(self) -> str | None:
        """Get the active app package name using dumpsys."""
        code, stdout, _ = await self._run_adb("shell", "dumpsys", "window", "windows", "|", "grep", "-E", "'mCurrentFocus'")
        if code == 0:
            output = stdout.decode('utf-8', errors='ignore').strip()
            # e.g. "mCurrentFocus=Window{c15555 u0 com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity}"
            if "mCurrentFocus" in output:
                return output.split(" ")[-1].strip("}")
        return None

    async def screenshot(self) -> bytes:
        """Take a screenshot."""
        if self.use_scrcpy:
            # We would typically grab the latest frame from a local video sink or v4l2 device here.
            # For this code-only backend implementation, we fallback to fast adb for now 
            # if the socket reader isn't implemented, or we can use scrcpy --record and grab a frame.
            pass
            
        code, stdout, stderr = await self._run_adb("exec-out", "screencap", "-p")
        if code != 0:
            logger.error("adb_screenshot_failed", stderr=stderr.decode('utf-8', errors='ignore'))
            # Fallback to stub or raise
            return b""
        return stdout

    async def click(self, x: int, y: int) -> ActionResult:
        """Tap at the given coordinates."""
        target_x, target_y = self._map_coordinates(x, y)
        code, _, stderr = await self._run_adb("shell", "input", "tap", str(target_x), str(target_y))
        if code == 0:
            return ActionResult(ActionStatus.SUCCESS, f"Tapped ({target_x}, {target_y})")
        return ActionResult(ActionStatus.FAILURE, f"ADB tap failed: {stderr.decode('utf-8', errors='ignore')}")

    async def type_text(self, text: str) -> ActionResult:
        """Type the given text."""
        # ADB input text requires escaping spaces and special characters. 
        # For simplicity in PoC, replace spaces with %s
        escaped_text = text.replace(" ", "%s")
        code, _, stderr = await self._run_adb("shell", "input", "text", escaped_text)
        if code == 0:
            return ActionResult(ActionStatus.SUCCESS, f"Typed '{text}'")
        return ActionResult(ActionStatus.FAILURE, f"ADB text failed: {stderr.decode('utf-8', errors='ignore')}")

    async def scroll(self, x: int, y: int, dy: int) -> ActionResult:
        """Swipe to simulate scrolling."""
        target_x, target_y = self._map_coordinates(x, y)
        # ADB swipe format: input swipe x1 y1 x2 y2 [duration(ms)]
        # If dy is negative, swipe UP (content goes down)
        # If dy is positive, swipe DOWN (content goes up)
        
        # Determine end coordinates. A simple 300px swipe is enough for a standard scroll.
        swipe_amount = 300
        end_y = target_y + swipe_amount if dy > 0 else target_y - swipe_amount
        # Ensure we don't swipe off screen (assumes min 0, max 2000 for standard phone, should use mapper real bounds ideally)
        end_y = max(10, min(end_y, 2500))
        
        code, _, stderr = await self._run_adb("shell", "input", "swipe", str(target_x), str(target_y), str(target_x), str(end_y))
        if code == 0:
            return ActionResult(ActionStatus.SUCCESS, f"Swiped from {target_y} to {end_y}")
        return ActionResult(ActionStatus.FAILURE, f"ADB swipe failed: {stderr.decode('utf-8', errors='ignore')}")

    async def press_key(self, key: str) -> ActionResult:
        """Press a key event."""
        # Keycode mapping for common keys
        keymap = {
            "enter": "66",
            "back": "4",
            "home": "3",
            "tab": "61"
        }
        keycode = keymap.get(key.lower(), None)
        if not keycode:
            return ActionResult(ActionStatus.FAILURE, f"Unknown keycode for {key}")
            
        code, _, stderr = await self._run_adb("shell", "input", "keyevent", keycode)
        if code == 0:
            return ActionResult(ActionStatus.SUCCESS, f"Pressed {key} (keycode {keycode})")
        return ActionResult(ActionStatus.FAILURE, f"ADB keyevent failed: {stderr.decode('utf-8', errors='ignore')}")

    async def back(self) -> ActionResult:
        """Navigate back."""
        return await self.press_key("back")
