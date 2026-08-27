"""Concrete coordinate mapper for standard scaling."""

from research_tool.interfaces.coordinate_mapper import CoordinateMapper

class ScalingCoordinateMapper(CoordinateMapper):
    """
    Maps coordinates between a normalized/fixed vision grid and a real screen resolution.
    Assumes simple linear scaling without padding/letterboxing by default.
    """
    def __init__(self, vision_width: int, vision_height: int, screen_width: int, screen_height: int):
        self.vw = vision_width
        self.vh = vision_height
        self.sw = screen_width
        self.sh = screen_height

    def vision_to_screen(self, x: int, y: int) -> tuple[int, int]:
        """Convert a vision-space coordinate to a native screen coordinate."""
        # Simple cross-multiplication
        screen_x = int((x / self.vw) * self.sw)
        screen_y = int((y / self.vh) * self.sh)
        
        # Clamp to screen bounds
        screen_x = max(0, min(screen_x, self.sw - 1))
        screen_y = max(0, min(screen_y, self.sh - 1))
        
        return screen_x, screen_y

    def screen_to_vision(self, x: int, y: int) -> tuple[int, int]:
        """Convert a native screen coordinate to a vision-space coordinate."""
        vision_x = int((x / self.sw) * self.vw)
        vision_y = int((y / self.sh) * self.vh)
        
        # Clamp to vision bounds
        vision_x = max(0, min(vision_x, self.vw - 1))
        vision_y = max(0, min(vision_y, self.vh - 1))
        
        return vision_x, vision_y
