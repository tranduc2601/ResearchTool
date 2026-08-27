"""Smoke test for Qwen2-VL local model loading."""
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw
import json
import torch

from research_tool.implementations.vision.local_vlm import LocalVisionProvider
from research_tool.domain.world_state import WorldState

async def main():
    print("Initializing Vision Provider...")
    provider = LocalVisionProvider(model_name="Qwen/Qwen2-VL-2B-Instruct")
    
    # Create a dummy image
    img = Image.new('RGB', (800, 600), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10,10), "Test Image for Qwen2-VL", fill=(255, 255, 0))
    
    import io
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    
    state = WorldState(run_id="smoke_test", platform="windows", app="test_app")
    
    print("Running analyze_screen (this will trigger model loading)...")
    result = await provider.analyze_screen(img_bytes, state, query="Look at the screen")
    
    print("=" * 40)
    print("Inference Result:")
    print("Page Type:", result.page_type)
    print("Action:", result.next_action)
    print("Raw Output JSON:")
    print(json.dumps(result.raw_output, indent=2))
    
    if provider.device == "cuda":
        print("CUDA Memory Allocated: ", torch.cuda.memory_allocated() / (1024**2), "MB")
    else:
        print("Running on CPU.")

if __name__ == "__main__":
    asyncio.run(main())
