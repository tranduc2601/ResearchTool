"""Abstract interface for mapping coordinates between systems.

A vision model may operate on a 1024x1024 grid, while the real
screen is 1920x1080. The mapper translates these coordinates.
"""

from abc import ABC, abstractmethod


class CoordinateMapper(ABC):
    @abstractmethod
    def vision_to_screen(self, x: int, y: int) -> tuple[int, int]:
        """Convert a vision-space coordinate to a native screen coordinate."""
        ...

    @abstractmethod
    def screen_to_vision(self, x: int, y: int) -> tuple[int, int]:
        """Convert a native screen coordinate to a vision-space coordinate."""
        ...
