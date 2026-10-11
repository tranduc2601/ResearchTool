import asyncio
import io
import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Add src to path
sys.path.insert(0, str(Path('src').resolve()))

from research_tool.domain import WorldState
from research_tool.domain.action import ActionType
from research_tool.implementations.vision.local_vlm import LocalVisionProvider
from research_tool.implementations.vision.prompt_builder import VisionPromptBuilder

async def main():
    print("Initializing test...")
    vision = LocalVisionProvider(model_name="Qwen/Qwen2-VL-2B-Instruct")
    
    img = Image.new('RGB', (1080, 2400), color='white')
    d = ImageDraw.Draw(img)
    d.rectangle([(200, 1000), (880, 1200)], fill='blue')
    d.text((400, 1100), "Search", fill='white')
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    screenshot_bytes = buf.getvalue()
    
    state = WorldState(run_id="test", platform="android", app="browser")
    goal = "Click the search button."
    prompt = VisionPromptBuilder.build_analysis_prompt(state, goal, 1080, 2400)
    
    print("Running VLM inference...")
    result = await vision.analyze_screen(screenshot_bytes, state, goal)
    
    print("\n--- RESULTS ---")
    print(f"Action: {result.action_type}")
    print(f"Coordinates (1-1000 scale): x={result.x}, y={result.y}")
    print(f"Text: {result.text}")
    print(f"Raw Output: {result.raw_output}")

    if result.action_type == ActionType.CLICK and result.x is not None and result.y is not None:
        print("SUCCESS! The model output valid coordinates.")
        sys.exit(0)
    else:
        print("FAILURE! Model did not output valid click coordinates.")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
