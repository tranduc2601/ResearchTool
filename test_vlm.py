import asyncio
import io
import json
from PIL import Image, ImageDraw
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path('src').resolve()))

from research_tool.implementations.vision.local_vlm import LocalVisionProvider
from research_tool.domain.world_state import WorldState, PageType
from research_tool.implementations.vision.prompt_builder import VisionPromptBuilder

async def main():
    print("Creating dummy screenshot...")
    img = Image.new('RGB', (1920, 1080), color = 'white')
    d = ImageDraw.Draw(img)
    d.rectangle([(100, 100), (300, 150)], fill='blue')
    d.text((150, 120), "Search", fill='white')
    d.rectangle([(100, 200), (300, 250)], fill='green')
    d.text((150, 220), "Submit", fill='white')
    
    sw, sh = img.size
    print(f"Screen size: {sw}x{sh}")
    
    print("Loading VLM...")
    vision = LocalVisionProvider(model_name="Qwen/Qwen2-VL-2B-Instruct")
    
    state = WorldState(run_id="test", platform="windows", app="desktop")
    goal = "Find the search bar and click it"
    
    prompt = VisionPromptBuilder.build_analysis_prompt(state, goal, sw, sh)
    
    print("Running inference...")
    raw_output = await vision._run_inference(img, prompt)
    print("\n--- RAW OUTPUT ---")
    print(raw_output)
    print("------------------")
    
    parsed = vision._parse_json_response(raw_output)
    print("\n--- PARSED JSON ---")
    print(json.dumps(parsed, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
