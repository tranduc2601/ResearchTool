"""PaddleOCR implementation."""
import structlog
from typing import Optional
from research_tool.interfaces.ocr_provider import OCRProvider, OCRResult, OCRWord
from research_tool.interfaces.vision_provider import BoundingBox

logger = structlog.get_logger()

# Optional dependency
try:
    from paddleocr import PaddleOCR
    from PIL import Image
    import io
    import numpy as np
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

class PaddleOCRProvider(OCRProvider):
    """
    PaddleOCR provider. Very accurate for multi-language and dense text.
    """
    
    def __init__(self, use_gpu: bool = False):
        self.enabled = PADDLE_AVAILABLE
        self.use_gpu = use_gpu
        self._ocr = None
            
        if not self.enabled:
            logger.warning("paddleocr_not_installed", message="pip install paddlepaddle paddleocr")

    def _init_ocr(self, lang: str):
        if not self._ocr:
            # Map common hints to PaddleOCR lang codes (e.g. 'vi' -> 'latin' or 'en', but let's use 'en' or 'vi' if supported)
            # PaddleOCR supports 'en', 'ch', 'vi', etc.
            self._ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=self.use_gpu, show_log=False)
            
    async def extract_text(self, image: bytes, region: BoundingBox | None = None, language_hint: str = "vi") -> OCRResult:
        """Extracts text and bounding boxes from a screenshot using PaddleOCR."""
        if not self.enabled:
            return OCRResult(full_text="", words=[])
            
        try:
            import asyncio
            return await asyncio.to_thread(self._run_paddle, image, region, language_hint)
        except Exception as e:
            logger.exception("ocr_failed", error=str(e))
            return OCRResult(full_text="", words=[])
            
    def _run_paddle(self, screenshot_bytes: bytes, region: BoundingBox | None, lang: str) -> OCRResult:
        self._init_ocr(lang)
        
        pil_image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        if region:
            pil_image = pil_image.crop((region.x, region.y, region.x + region.width, region.y + region.height))
            
        img_np = np.array(pil_image)
        
        # result is a list of lists of [[box_points], (text, confidence)]
        result = self._ocr.ocr(img_np, cls=True)
        
        words = []
        full_text_parts = []
        
        if result and result[0]:
            for line in result[0]:
                box_points = line[0]
                text, conf = line[1]
                
                # box_points is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                x1 = min([p[0] for p in box_points])
                y1 = min([p[1] for p in box_points])
                x2 = max([p[0] for p in box_points])
                y2 = max([p[1] for p in box_points])
                
                # if there is a region offset, we could add it back here if we want global coords
                # but let's assume we return coords relative to the passed region
                
                bbox = BoundingBox(x=int(x1), y=int(y1), width=int(x2-x1), height=int(y2-y1))
                words.append(OCRWord(text=text, bounding_box=bbox, confidence=conf))
                full_text_parts.append(text)
                    
        return OCRResult(full_text=" ".join(full_text_parts), words=words, language=lang)
