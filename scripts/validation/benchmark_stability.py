"""
Latency and Resource Stability Harness.

Runs a VLM on a loop for a specified number of iterations or time limit.
Tracks VRAM, RAM, and Latency.
Outputs to stability_metrics.csv.
"""
import time
import argparse
import csv
import gc
from pathlib import Path

try:
    import psutil
except ImportError:
    print("Please pip install psutil")
    exit(1)

def get_vram_usage():
    """Get VRAM usage using PyTorch or PyNVML."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024**2) # MB
    except ImportError:
        pass
    return 0.0

def get_ram_usage():
    """Get system RAM usage of the current process in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024**2)

def run_stability_benchmark(model_name: str, iterations: int = 200, max_hours: float = 1.0):
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from benchmark_vlm import VLMBenchmark
    from PIL import Image

    print(f"Initializing Stability Benchmark for {model_name}...")
    benchmark = VLMBenchmark(model_name)
    benchmark.load_model()
    
    # Create dummy image
    dummy_img = "tmp_stability.png"
    Image.new('RGB', (1920, 1080), color=(100, 100, 100)).save(dummy_img)
    
    metrics = []
    start_time = time.time()
    max_seconds = max_hours * 3600
    
    print(f"Running for {iterations} iterations or {max_hours} hours...")
    
    for i in range(iterations):
        if time.time() - start_time > max_seconds:
            print("Time limit reached. Stopping early.")
            break
            
        print(f"Iteration {i+1}/{iterations}...")
        
        iter_start = time.time()
        benchmark.run_inference(dummy_img, "What is in this image? Respond briefly.")
        latency = time.time() - iter_start
        
        # Track memory
        ram_mb = get_ram_usage()
        vram_mb = get_vram_usage()
        
        metrics.append({
            "iteration": i+1,
            "latency_s": round(latency, 3),
            "ram_mb": round(ram_mb, 2),
            "vram_mb": round(vram_mb, 2)
        })
        
        # Periodic cleanup to simulate real agent behavior
        if i % 10 == 0:
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass

    # Save results
    out_file = "stability_metrics.csv"
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["iteration", "latency_s", "ram_mb", "vram_mb"])
        writer.writeheader()
        writer.writerows(metrics)
        
    # Calculate stats
    latencies = [m["latency_s"] for m in metrics]
    latencies.sort()
    mean_lat = sum(latencies) / len(latencies)
    p50 = latencies[len(latencies)//2]
    p95 = latencies[int(len(latencies)*0.95)]
    
    print("\n--- Stability Summary ---")
    print(f"Total Iterations: {len(metrics)}")
    print(f"Mean Latency: {mean_lat:.2f}s")
    print(f"P50 (Median): {p50:.2f}s")
    print(f"P95 Latency : {p95:.2f}s")
    print(f"Final RAM   : {metrics[-1]['ram_mb']} MB")
    print(f"Final VRAM  : {metrics[-1]['vram_mb']} MB")
    print(f"Results saved to {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="qwen2-vl")
    parser.add_argument("--iters", type=int, default=200)
    args = parser.parse_args()
    
    run_stability_benchmark(args.model, args.iters)
