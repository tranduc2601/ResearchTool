"""Tesseract-based CPU OCR implementation."""
import structlog
from typing import Optional
from research_tool.interfaces.ocr_provider import OCRProvider, OCRResult, OCRWord
from research_tool.interfaces.vision_provider import BoundingBox

logger = structlog.get_logger()

# Optional dependency
try:
    import pytesseract
    from PIL import Image
    import io
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

class TesseractOCRProvider(OCRProvider):
    """
    CPU-only OCR provider using Tesseract.
    Useful for preserving VRAM on 4GB systems.
    """
    
    def __init__(self, tesseract_cmd: str | None = None):
        self.enabled = TESSERACT_AVAILABLE
        if tesseract_cmd and TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
        if not self.enabled:
            logger.warning("tesseract_not_installed", message="pip install pytesseract pillow, and install tesseract-ocr system binary")

    async def extract_text(self, image: bytes, region: BoundingBox | None = None, language_hint: str = "vi") -> OCRResult:
        """Extracts text and bounding boxes from a screenshot."""
        if not self.enabled:
            return OCRResult(full_text="", words=[])
            
        try:
            import asyncio
            return await asyncio.to_thread(self._run_tesseract, image, region, language_hint)
        except Exception as e:
            logger.exception("ocr_failed", error=str(e))
            return OCRResult(full_text="", words=[])
            
    def _run_tesseract(self, screenshot_bytes: bytes, region: BoundingBox | None, lang: str) -> OCRResult:
        image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        if region:
            image = image.crop((region.x, region.y, region.x + region.width, region.y + region.height))
        
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        full_text = pytesseract.image_to_string(image, lang=lang)
        
        words = []
        n_boxes = len(data['level'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                if len(text) > 2 or text.isalnum():
                    bbox = BoundingBox(x=x, y=y, width=w, height=h)
                    words.append(OCRWord(text=text, bounding_box=bbox))
                    
        return OCRResult(full_text=full_text, words=words, language=lang)
