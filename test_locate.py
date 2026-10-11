import asyncio
import io
import re
from PIL import Image, ImageDraw
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path('src').resolve()))

from research_tool.implementations.vision.local_vlm import LocalVisionProvider
from research_tool.domain.world_state import WorldState, PageType

async def main():
    img = Image.new('RGB', (1920, 1080), color = 'white')
    d = ImageDraw.Draw(img)
    d.rectangle([(100, 100), (300, 150)], fill='blue')
    d.text((150, 120), "Search", fill='white')
    d.rectangle([(100, 200), (300, 250)], fill='green')
    d.text((150, 220), "Submit", fill='white')
    
    vision = LocalVisionProvider(model_name="Qwen/Qwen2-VL-2B-Instruct")
    
    prompt = "Find the UI element: Submit. Output its bounding box using <|box_start|>(y1,x1),(y2,x2)<|box_end|>."
    
    print("Running inference...")
    raw_output = await vision._run_inference(img, prompt)
    print("\n--- RAW OUTPUT ---")
    print(raw_output)
    
if __name__ == '__main__':
    asyncio.run(main())
