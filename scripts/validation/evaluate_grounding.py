"""
Grounding Benchmark Tool.

Evaluates a VLM's ability to locate a specific UI element based on a prompt.
Reads a JSONL file with format:
{"image": "path.png", "prompt": "Find the login button", "target_bbox": [x1, y1, x2, y2]}

Outputs results to grounding_results.csv
"""
import json
import csv
import argparse
from pathlib import Path

def calculate_iou(box1, box2):
    """Calculate Intersection over Union for two bounding boxes [x1, y1, x2, y2]."""
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    iou = intersection_area / float(box1_area + box2_area - intersection_area)
    return iou

def evaluate_grounding(dataset_path: str, model_name: str, tolerance_px: int = 50):
    # Dynamic import to avoid breaking if not installed
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    try:
        from benchmark_vlm import VLMBenchmark
    except ImportError:
        print("Could not import VLMBenchmark from benchmark_vlm.py. Check PYTHONPATH.")
        return

    benchmark = VLMBenchmark(model_name)
    benchmark.load_model()
    
    results = []
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    print(f"Loaded {len(lines)} samples.")
    
    for i, line in enumerate(lines):
        data = json.loads(line)
        img_path = data['image']
        prompt = data['prompt']
        target_bbox = data['target_bbox'] # [x1, y1, x2, y2]
        
        # We append instructions to force coordinate output
        full_prompt = f"{prompt}\nReturn ONLY the bounding box coordinates [x1, y1, x2, y2] of the target element."
        
        try:
            # Inference
            raw_output = benchmark.run_inference(img_path, full_prompt)
            
            # Parse output (very basic parser, models like Qwen output specific box formats)
            import re
            numbers = re.findall(r'\d+', raw_output)
            
            status = "NO_ANSWER"
            iou = 0.0
            pred_bbox = None
            
            if len(numbers) >= 4:
                pred_bbox = [int(n) for n in numbers[:4]]
                iou = calculate_iou(target_bbox, pred_bbox)
                
                # Simple point-in-box check if IoU is too strict for tiny buttons
                pred_center_x = (pred_bbox[0] + pred_bbox[2]) / 2
                pred_center_y = (pred_bbox[1] + pred_bbox[3]) / 2
                
                in_target_x = target_bbox[0] - tolerance_px <= pred_center_x <= target_bbox[2] + tolerance_px
                in_target_y = target_bbox[1] - tolerance_px <= pred_center_y <= target_bbox[3] + tolerance_px
                
                if iou > 0.5 or (in_target_x and in_target_y):
                    status = "SUCCESS"
                elif iou > 0.1 or (in_target_x or in_target_y):
                    status = "NEAR_MISS"
                else:
                    status = "WRONG_TARGET"
            else:
                status = "WRONG_FORMAT"
                
            results.append({
                "sample_id": i,
                "image": img_path,
                "status": status,
                "iou": round(iou, 3),
                "target": str(target_bbox),
                "predicted": str(pred_bbox) if pred_bbox else raw_output
            })
            
            print(f"Sample {i}: {status} (IoU: {iou:.2f})")
            
        except Exception as e:
            print(f"Error on sample {i}: {e}")
            results.append({
                "sample_id": i,
                "image": img_path,
                "status": "ERROR",
                "iou": 0.0,
                "target": str(target_bbox),
                "predicted": str(e)
            })

    # Save results
    out_file = "grounding_results.csv"
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "image", "status", "iou", "target", "predicted"])
        writer.writeheader()
        writer.writerows(results)
        
    # Print summary
    successes = sum(1 for r in results if r['status'] == 'SUCCESS')
    print("\n--- Grounding Summary ---")
    print(f"Total: {len(results)}")
    print(f"Success: {successes} ({(successes/len(results))*100:.1f}%)")
    print(f"Results saved to {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="Path to JSONL dataset")
    parser.add_argument("--model", type=str, default="qwen2-vl", choices=["qwen2-vl", "moondream2"])
    args = parser.parse_args()
    
    evaluate_grounding(args.dataset, args.model)
