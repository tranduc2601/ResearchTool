"""
Benchmark script for evaluating local VLMs against Gate #1 metrics.
Hardware Target: RTX 3050 Ti (4GB VRAM), Ryzen 5 5600H, 16GB RAM.

Usage:
    python scripts/benchmark_vlm.py --model qwen2-vl
    python scripts/benchmark_vlm.py --model moondream2
"""
import argparse
import time
import asyncio
import gc
from pathlib import Path

# Try to import torch, but handle if it's not installed in the current environment
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, AutoProcessor
    from PIL import Image
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import structlog
logger = structlog.get_logger()


class VLMBenchmark:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self.tokenizer = None

    def load_model(self):
        """Loads the model with 4-bit quantization to fit in 4GB VRAM."""
        logger.info(f"Loading {self.model_name} on {self.device}...")
        start = time.time()
        
        # We use BitsAndBytesConfig for 4-bit loading
        from transformers import BitsAndBytesConfig
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

        if self.model_name == "moondream2":
            # Moondream2 (1.8B) - Can easily fit in 4GB even at 8-bit, but we'll use 4-bit to be safe
            model_id = "vikhyatk/moondream2"
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, 
                trust_remote_code=True,
                quantization_config=quant_config,
                device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            
        elif self.model_name == "qwen2-vl":
            # Qwen2-VL (2B)
            from transformers import Qwen2VLForConditionalGeneration
            model_id = "Qwen/Qwen2-VL-2B-Instruct"
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_id,
                trust_remote_code=True,
                quantization_config=quant_config,
                device_map="auto"
            )
            self.processor = AutoProcessor.from_pretrained(model_id)
            
        else:
            raise ValueError(f"Unknown model: {self.model_name}")
            
        logger.info(f"Loaded in {time.time() - start:.2f}s")
        self.report_vram()

    def report_vram(self):
        if self.device == "cuda":
            allocated = torch.cuda.memory_allocated() / (1024**3)
            reserved = torch.cuda.memory_reserved() / (1024**3)
            logger.info("vram_usage", allocated_gb=f"{allocated:.2f}", reserved_gb=f"{reserved:.2f}")

    def run_inference(self, image_path: str, prompt: str) -> str:
        """Runs inference and measures latency."""
        image = Image.open(image_path).convert("RGB")
        
        start = time.time()
        if self.model_name == "moondream2":
            enc_image = self.model.encode_image(image)
            result = self.model.answer_question(enc_image, prompt, self.tokenizer)
        elif self.model_name == "qwen2-vl":
            from qwen_vl_utils import process_vision_info
            # Setup chat format for Qwen2-VL
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            generated_ids = self.model.generate(**inputs, max_new_tokens=128)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            result = self.processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

        latency = time.time() - start
        logger.info("inference_complete", latency_sec=f"{latency:.2f}", result=result)
        self.report_vram()
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True, choices=["qwen2-vl", "moondream2"])
    parser.add_argument("--image", type=str, default="test_image.png")
    args = parser.parse_args()

    if not TORCH_AVAILABLE:
        logger.error("PyTorch/Transformers not installed. Please install: pip install torch transformers pillow accelerate bitsandbytes torchvision")
        return

    # Create dummy image if none exists
    if not Path(args.image).exists():
        logger.warning(f"Image {args.image} not found. Creating a dummy 1080p image.")
        Image.new('RGB', (1920, 1080), color = (73, 109, 137)).save(args.image)

    benchmark = VLMBenchmark(args.model)
    benchmark.load_model()
    
    logger.info("Starting Benchmark... (Gate #1 Metrics)")
    
    # Run 5 iterations to test P50/P95 latency and VRAM stability
    latencies = []
    prompt = "Find the search bar. What are its bounding box coordinates?"
    
    for i in range(5):
        logger.info(f"--- Iteration {i+1} ---")
        start = time.time()
        benchmark.run_inference(args.image, prompt)
        latencies.append(time.time() - start)
        
        # Force garbage collection to test VRAM stability
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    latencies.sort()
    logger.info("benchmark_complete", 
                median_latency=f"{latencies[len(latencies)//2]:.2f}s",
                p95_latency=f"{latencies[int(len(latencies)*0.95)]:.2f}s")

if __name__ == "__main__":
    main()
