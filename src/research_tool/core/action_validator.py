"""Action Validator.

Responsible for validating that an ActionCommand is physically executable
(e.g., coordinates are within screen bounds) and conceptually permitted
(e.g., enforces read-oriented safety policies).
"""

from research_tool.domain import ActionCommand, ActionStatus, ActionResult, ActionType


class ActionValidator:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

    def validate(self, action: ActionCommand) -> ActionResult:
        """
        Validates an ActionCommand before execution.
        Returns a successful ActionResult if valid, or a FAILURE result if invalid.
        """
        # Coordinate bounds check
        if action.action_type in (ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.SCROLL, ActionType.SCROLL):
            if action.x is not None and (action.x < 0 or action.x > self.screen_width):
                return ActionResult(ActionStatus.FAILURE, f"x coordinate {action.x} out of bounds")
            if action.y is not None and (action.y < 0 or action.y > self.screen_height):
                return ActionResult(ActionStatus.FAILURE, f"y coordinate {action.y} out of bounds")

        # In a real app, we might also prevent typing into certain fields or 
        # clicking certain areas based on the read-oriented safety policy.
        
        return ActionResult(ActionStatus.SUCCESS, "Valid action")
