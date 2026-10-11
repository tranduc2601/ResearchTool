"""Builds strict prompts for the VLM to force structured output."""
import json
from research_tool.domain import WorldState

class VisionPromptBuilder:
    @staticmethod
    def build_analysis_prompt(state: WorldState, goal: str, screen_width: int = 1920, screen_height: int = 1080) -> str:
        """
        Build a prompt forcing the model to output a strictly formatted JSON.
        We provide the current state and the goal.
        """
        return f"""You are an autonomous agent controlling a computer GUI to collect information.

CURRENT CONTEXT:
Goal: "{goal}"
Active App: {state.app or 'Unknown'}
Platform: {state.platform}
Screen Resolution: {screen_width}x{screen_height}
Recent Actions Taken: {', '.join(state.navigation_history[-3:]) if state.navigation_history else 'None'}

YOUR TASK:
Analyze the provided screenshot. You must decide the single next best action to progress toward the goal.
Respond ONLY with a valid JSON object matching this schema exactly. Do not include markdown code blocks or any conversational text.

SCHEMA:
{{
    "page_type": "string (NAVIGATION | PRODUCT_PAGE | SEARCH_RESULTS | UNKNOWN)",
    "current_entity_name": "string (e.g., name of the product currently on screen, or null)",
    "confidence": "string (KNOWN | UNCERTAIN | UNKNOWN)",
    "next_action": {{
        "action_type": "string (CLICK | TYPE_TEXT | SCROLL | DRAG | PRESS_KEY | BACK | WAIT | GOAL_MET | GOAL_FAILED | HUMAN_REQUIRED | RECOVER | CONTINUE)",
        "box_2d": "string or null (For CLICK, SCROLL, DRAG. Output exactly in format <|box_start|>(y1,x1),(y2,x2)<|box_end|> using normalized 1-1000 coordinates)",
        "text": "string or null (required for TYPE_TEXT, PRESS_KEY)",
        "dx": "integer or null (for DRAG)",
        "dy": "integer or null (for DRAG, SCROLL)"
    }},
    "extracted_entities": [
        {{
            "name": "string (e.g., product name)",
            "brand": "string or null",
            "model_sku": "string or null"
        }}
    ],
    "extracted_evidence": [
        {{
            "evidence_type": "string (REVIEW | SPECIFICATION | PRICE | FEATURE)",
            "raw_text": "string (the exact text you read)"
        }}
    ]
}}

RULES:
1. If you need to click something, you MUST output its bounding box in `box_2d` using EXACTLY `<|box_start|>(y1,x1),(y2,x2)<|box_end|>` format, where coordinates are scaled 1-1000. DO NOT guess pixel coordinates.
2. If scrolling, use action_type="SCROLL" and provide `box_2d` (where to place mouse) and dy (amount to scroll, e.g. -1 for down).
3. If the goal is met and all information has been recorded, use "GOAL_MET".
4. If a CAPTCHA or popup blocks you, use "HUMAN_REQUIRED".
5. AVOID REPETITION: Look at 'Recent Actions Taken'. If your planned action is identical to a recent action and the screen hasn't changed, DO NOT repeat it! Choose a different action, scroll down, or click somewhere else.
6. If you need to search the web but see no browser, use action_type="PRESS_KEY" with text="win" (to open start menu), then you can use TYPE_TEXT to search for "edge" or "chrome".
7. Do NOT include any text outside the JSON object.
"""
