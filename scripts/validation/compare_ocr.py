"""
OCR Comparison Tool.

Benchmarks Tesseract against PaddleOCR on a directory of UI screenshots.
Outputs compare_ocr_results.csv.
"""
import time
import argparse
import csv
from pathlib import Path

def setup_paddleocr():
    try:
        from paddleocr import PaddleOCR
        # Use English by default, add 'vi' if doing Vietnamese
        return PaddleOCR(use_angle_cls=True, lang='vi', use_gpu=False)
    except ImportError:
        print("Could not import paddleocr. pip install paddlepaddle paddleocr")
        return None

def setup_tesseract():
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from research_tool.implementations.ocr.tesseract_ocr import TesseractOCRProvider
    return TesseractOCRProvider()

def run_ocr_comparison(img_dir: str):
    img_paths = list(Path(img_dir).glob("*.png")) + list(Path(img_dir).glob("*.jpg"))
    if not img_paths:
        print(f"No images found in {img_dir}")
        return
        
    print(f"Found {len(img_paths)} images. Initializing OCR engines...")
    
    paddle = setup_paddleocr()
    tesseract = setup_tesseract()
    
    if not paddle or not tesseract.enabled:
        print("Missing OCR dependencies.")
        return
        
    results = []
    
    # Run async tesseract in sync wrapper
    import asyncio
    
    for i, img_path in enumerate(img_paths):
        print(f"Processing {img_path.name}...")
        
        with open(img_path, 'rb') as f:
            img_bytes = f.read()
            
        # PaddleOCR
        start = time.time()
        # PaddleOCR expects a file path or numpy array. We'll pass the path.
        paddle_res = paddle.ocr(str(img_path), cls=True)
        paddle_time = time.time() - start
        
        # Parse paddle text
        paddle_texts = []
        if paddle_res and paddle_res[0]:
            for line in paddle_res[0]:
                paddle_texts.append(line[1][0])
                
        # Tesseract
        start = time.time()
        tess_res = asyncio.run(tesseract.extract_text(img_bytes))
        tess_time = time.time() - start
        tess_texts = [e.text for e in tess_res]
        
        results.append({
            "image": img_path.name,
            "tesseract_time": round(tess_time, 3),
            "paddle_time": round(paddle_time, 3),
            "tesseract_boxes": len(tess_texts),
            "paddle_boxes": len(paddle_texts),
            "tesseract_sample": " | ".join(tess_texts[:5]),
            "paddle_sample": " | ".join(paddle_texts[:5])
        })
        
    out_file = "compare_ocr_results.csv"
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nSaved comparison to {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, required=True, help="Directory containing test images")
    args = parser.parse_args()
    
    run_ocr_comparison(args.dir)
