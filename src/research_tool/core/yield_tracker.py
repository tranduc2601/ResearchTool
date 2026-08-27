"""Diminishing-returns / yield tracker.

Maintains a rolling 20-minute window of discovery metrics.
The Orchestrator reads this to decide LOW_YIELD / SATURATION state.

V1 thresholds (from architecture plan §19):
    window_minutes: 20
    low_yield_candidates: < 2 unique candidates/window → LOW_YIELD
    saturation_candidates: < 2 for 2 consecutive windows → SATURATION
    saturation_evidence: < 5 for 2 consecutive windows → SATURATION
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

@dataclass
class YieldWindow:
    """Stats for one time window."""
    window_start: datetime
    window_end: datetime
    new_candidates: int = 0
    new_evidence: int = 0
    new_seeds: int = 0
    duplicate_count: int = 0

    @property
    def is_low_yield(self, threshold: int = 2) -> bool:
        return self.new_candidates < threshold

class YieldTracker:
    """
    Rolling window yield tracker.
    
    Usage:
        tracker = YieldTracker(window_minutes=20)
        tracker.record_candidate()
        tracker.record_evidence()
        status = tracker.current_status()  # "NORMAL" | "LOW_YIELD" | "SATURATION"
        snapshot = tracker.snapshot()  # dict for checkpoint
    """

    def __init__(
        self,
        window_minutes: int = 20,
        low_yield_candidates: int = 2,
        saturation_candidates: int = 2,
        saturation_evidence: int = 5,
        max_consecutive_low: int = 2,
    ):
        self.window_minutes = window_minutes
        self.low_yield_candidates = low_yield_candidates
        self.saturation_candidates = saturation_candidates
        self.saturation_evidence = saturation_evidence
        self.max_consecutive_low = max_consecutive_low

        self._windows: deque[YieldWindow] = deque(maxlen=10)
        self._current: YieldWindow = self._new_window()
        self._consecutive_low: int = 0

    def _new_window(self) -> YieldWindow:
        now = datetime.now(timezone.utc)
        return YieldWindow(
            window_start=now,
            window_end=now + timedelta(minutes=self.window_minutes),
        )

    def _rotate_if_needed(self) -> None:
        """Close current window and start new one if window_end has passed."""
        now = datetime.now(timezone.utc)
        if now >= self._current.window_end:
            # Evaluate the completed window
            if self._current.new_candidates < self.low_yield_candidates:
                self._consecutive_low += 1
            else:
                self._consecutive_low = 0
            self._windows.append(self._current)
            self._current = self._new_window()

    def record_candidate(self) -> None:
        """Call when a new unique candidate entity is discovered."""
        self._rotate_if_needed()
        self._current.new_candidates += 1

    def record_evidence(self) -> None:
        """Call when a new evidence item is saved."""
        self._rotate_if_needed()
        self._current.new_evidence += 1

    def record_seed(self) -> None:
        """Call when a new seed is created."""
        self._rotate_if_needed()
        self._current.new_seeds += 1

    def record_duplicate(self) -> None:
        """Call when a duplicate/already-visited item is encountered."""
        self._rotate_if_needed()
        self._current.duplicate_count += 1

    def current_status(self) -> str:
        """
        Return current yield status:
        - "SATURATION": 2+ consecutive low-yield windows
        - "LOW_YIELD": current window is below threshold
        - "NORMAL": otherwise
        """
        self._rotate_if_needed()
        if self._consecutive_low >= self.max_consecutive_low:
            return "SATURATION"
        if self._current.new_candidates < self.low_yield_candidates:
            return "LOW_YIELD"
        return "NORMAL"

    def snapshot(self) -> dict:
        """Return a JSON-serializable snapshot for checkpointing."""
        return {
            "window_start": self._current.window_start.isoformat(),
            "window_end": self._current.window_end.isoformat(),
            "new_candidates": self._current.new_candidates,
            "new_evidence": self._current.new_evidence,
            "new_seeds": self._current.new_seeds,
            "duplicate_count": self._current.duplicate_count,
            "consecutive_low_windows": self._consecutive_low,
            "status": self.current_status(),
        }
