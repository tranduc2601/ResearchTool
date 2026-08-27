"""Builds strict prompts for the VLM to force structured output."""
import json
from research_tool.domain import WorldState

class VisionPromptBuilder:
    @staticmethod
    def build_analysis_prompt(state: WorldState, goal: str) -> str:
        """
        Build a prompt forcing the model to output a strictly formatted JSON.
        We provide the current state and the goal.
        """
        return f"""You are an autonomous agent controlling a computer GUI to collect information.

CURRENT CONTEXT:
Goal: "{goal}"
Active App: {state.active_app or 'Unknown'}
Platform: {state.platform}

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
        "x": "integer or null (required for CLICK, DRAG, SCROLL)",
        "y": "integer or null (required for CLICK, DRAG, SCROLL)",
        "text": "string or null (required for TYPE_TEXT, PRESS_KEY, HOTKEY)",
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
1. If you need to click something, provide its exact center X, Y coordinates based on the image size.
2. If scrolling, use action_type="SCROLL" and provide x,y (where to place mouse) and dy (amount to scroll, e.g. -1 for down).
3. If the goal is met and all information has been recorded, use "GOAL_MET".
4. If a CAPTCHA or blocking popup appears that you cannot handle, use "HUMAN_REQUIRED".
5. Do NOT include any text outside the JSON object.
"""
