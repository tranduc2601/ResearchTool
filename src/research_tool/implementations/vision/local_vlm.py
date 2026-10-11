"""Local VLM implementation of the VisionProvider."""
import json
import io
import structlog
from typing import Optional
from PIL import Image
import asyncio

from research_tool.interfaces.vision_provider import VisionProvider, VisionResult, UIElement, BoundingBox, ElementLocation
from research_tool.domain.world_state import WorldState, PageType, Confidence
from research_tool.domain.action import ActionCommand, ActionType
from research_tool.implementations.vision.prompt_builder import VisionPromptBuilder
from research_tool.interfaces.ocr_provider import OCRProvider

logger = structlog.get_logger()

# Optional dependencies for real execution
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoProcessor, AutoTokenizer
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class LocalVisionProvider(VisionProvider):
    """
    A concrete VisionProvider using a local VLM (default Qwen2-VL-2B-Instruct).
    Quantized to 4-bit to fit in 4GB VRAM.
    """

    def __init__(self, model_name: str = "Qwen/Qwen2-VL-2B-Instruct", ocr_provider: OCRProvider | None = None):
        self.model_name = model_name
        self.ocr_provider = ocr_provider
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.device = "cuda" if (TORCH_AVAILABLE and torch.cuda.is_available()) else "cpu"
        self._is_loaded = False

    def _load_model(self):
        if self._is_loaded:
            return
        if not TORCH_AVAILABLE:
            raise RuntimeError("transformers and torch are required for LocalVisionProvider")

        logger.info("loading_vlm", model=self.model_name, device=self.device)
        from transformers import BitsAndBytesConfig
        
        quant_config = None
        if self.device == "cuda":
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )

        if "qwen" in self.model_name.lower():
            from transformers import Qwen2VLForConditionalGeneration
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                quantization_config=quant_config,
                device_map="auto"
            )
            self.processor = AutoProcessor.from_pretrained(self.model_name)
        elif "moondream" in self.model_name.lower():
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                quantization_config=quant_config,
                device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        else:
            raise ValueError(f"Unsupported local model architecture: {self.model_name}")
            
        self._is_loaded = True
        logger.info("vlm_loaded")

    async def _run_inference(self, image: Image.Image, prompt: str) -> str:
        """Run the actual forward pass in a thread pool to avoid blocking the event loop."""
        return await asyncio.to_thread(self._run_inference_sync, image, prompt)

    def _run_inference_sync(self, image: Image.Image, prompt: str) -> str:
        self._load_model()
        
        if "qwen" in self.model_name.lower():
            from qwen_vl_utils import process_vision_info
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
            
            generated_ids = self.model.generate(**inputs, max_new_tokens=1024)
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            return self.processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            
        elif "moondream" in self.model_name.lower():
            enc_image = self.model.encode_image(image)
            return self.model.answer_question(enc_image, prompt, self.tokenizer)

    def _parse_json_response(self, text: str) -> dict:
        """Robustly extract JSON from the raw response string."""
        # Remove any markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.error("vlm_json_decode_error", text=text, error=str(e))
            # Fallback to a safe WAIT action
            return {
                "page_type": "UNKNOWN",
                "current_entity_name": None,
                "confidence": "UNKNOWN",
                "next_action": {"action_type": "WAIT"}
            }

    async def analyze_screen(self, screenshot: bytes, context: WorldState, query: str = "") -> VisionResult:
        image = Image.open(io.BytesIO(screenshot)).convert("RGB")
        img_w, img_h = image.size
        
        # If we have OCR enabled, we can optionally overlay text or append OCR context to the prompt
        ocr_text = ""
        if self.ocr_provider:
            # We don't want to block, so wait on it
            ocr_result = await self.ocr_provider.extract_text(screenshot)
            if ocr_result and ocr_result.words:
                ocr_text = "\nDetected Text via OCR:\n" + ", ".join([w.text for w in ocr_result.words[:20]])
        
        prompt = VisionPromptBuilder.build_analysis_prompt(context, query, img_w, img_h)
        prompt += ocr_text

        raw_output = await self._run_inference(image, prompt)
        parsed = self._parse_json_response(raw_output)
        
        # Construct domain models
        page_type_str = parsed.get("page_type", "UNKNOWN").upper()
        try:
            page_type = PageType[page_type_str]
        except KeyError:
            page_type = PageType.UNKNOWN
            
        conf_str = parsed.get("confidence", "UNKNOWN").upper()
        try:
            confidence = Confidence[conf_str]
        except KeyError:
            confidence = Confidence.UNCERTAIN

        act_dict = parsed.get("next_action", {})
        action_type_str = act_dict.get("action_type", "WAIT").upper()
        try:
            action_type = ActionType[action_type_str]
        except KeyError:
            action_type = ActionType.WAIT

        box_str = act_dict.get("box_2d")
        cx, cy = None, None
        if box_str:
            import re
            m = re.search(r'<\|box_start\|>\((\d+),(\d+)\),\((\d+),(\d+)\)<\|box_end\|>', box_str)
            if m:
                y1, x1, y2, x2 = map(int, m.groups())
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
            else:
                # Fallback for generic coordinate array [y1, x1, y2, x2] or just (x, y)
                nums = re.findall(r'\d+', box_str)
                if len(nums) >= 4:
                    y1, x1, y2, x2 = map(int, nums[:4])
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                elif len(nums) == 2:
                    # Model output a single point, likely (x, y) or (y, x) but let's assume (x, y) as it's common hallucination
                    # Or maybe (y, x) because Qwen uses y,x? If the prompt says "y1,x1", it might output (y, x). 
                    # We'll just assume (x, y) if it's standard hallucination, but to be robust, let's look at the string format.
                    cx, cy = map(int, nums)
        
        # Fallback if x, y was directly provided (just in case model disobeys and outputs x,y)
        if cx is None and act_dict.get("x") is not None:
            cx = act_dict.get("x")
        if cy is None and act_dict.get("y") is not None:
            cy = act_dict.get("y")

        command = ActionCommand(
            action_type=action_type,
            x=cx,
            y=cy,
            text=act_dict.get("text"),
            dx=act_dict.get("dx"),
            dy=act_dict.get("dy"),
        )
        
        return VisionResult(
            page_type=page_type,
            detected_elements=[], # We could parse bounding boxes if requested
            current_entity_name=parsed.get("current_entity_name"),
            confidence=confidence,
            next_action=command,
            raw_output=parsed,
            screenshot_used=screenshot
        )

    async def locate_element(self, screenshot: bytes, description: str) -> ElementLocation | None:
        """Find an element using VLM grounding capabilities."""
        image = Image.open(io.BytesIO(screenshot)).convert("RGB")
        prompt = f"Find the UI element: {description}. Return its bounding box [x1, y1, x2, y2]."
        
        raw_output = await self._run_inference(image, prompt)
        # Naive extraction for the coordinate arrays typically output by Qwen
        import re
        numbers = re.findall(r'\d+', raw_output)
        if len(numbers) >= 4:
            x1, y1, x2, y2 = [int(n) for n in numbers[:4]]
            return ElementLocation(
                bounding_box=BoundingBox(x1, y1, x2-x1, y2-y1),
                confidence=1.0,
                element_type="element",
                label=description
            )
        return None
