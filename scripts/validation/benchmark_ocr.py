"""Benchmark script for evaluating OCR providers.
Compares Tesseract vs PaddleOCR in latency and basic extraction (mocked if not installed).
"""
import asyncio
import time
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from research_tool.implementations.ocr.tesseract_ocr import TesseractOCRProvider
from research_tool.implementations.ocr.paddle_ocr import PaddleOCRProvider

def create_test_image(filename: str):
    """Creates a dummy image with some text for OCR testing."""
    img = Image.new('RGB', (800, 400), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Just draw some standard text
    text = "The quick brown fox jumps over the lazy dog.\nAutonomous Visual Information Explorer.\nOCR Benchmark Test 12345"
    d.text((50, 50), text, fill=(0, 0, 0))
    img.save(filename)

async def run_benchmark(iterations: int = 5):
    img_path = "tmp_ocr_benchmark.png"
    if not Path(img_path).exists():
        create_test_image(img_path)
        
    with open(img_path, "rb") as f:
        img_bytes = f.read()
        
    providers = {
        "Tesseract": TesseractOCRProvider(),
        "PaddleOCR": PaddleOCRProvider(use_gpu=False)
    }
    
    for name, provider in providers.items():
        print(f"\n--- Benchmarking {name} ---")
        if not getattr(provider, 'enabled', True):
            print(f"{name} is not installed or enabled. Skipping.")
            continue
            
        # Warmup
        print("Warming up...")
        await provider.extract_text(img_bytes, language_hint="en")
        
        latencies = []
        for i in range(iterations):
            start = time.time()
            result = await provider.extract_text(img_bytes, language_hint="en")
            latencies.append(time.time() - start)
            
        print(f"Extraction result sample: {result.full_text[:50]}...")
        print(f"Words extracted: {len(result.words)}")
        
        avg_latency = sum(latencies) / len(latencies)
        p90 = sorted(latencies)[int(len(latencies) * 0.9)]
        print(f"Average Latency: {avg_latency:.3f}s")
        print(f"P90 Latency: {p90:.3f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iters", type=int, default=5, help="Number of iterations")
    args = parser.parse_args()
    
    asyncio.run(run_benchmark(args.iters))
