"""Tesseract-based CPU OCR implementation."""
import structlog
from typing import Optional
from research_tool.interfaces.ocr_provider import OCRProvider, OCREntity

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

    async def extract_text(self, screenshot_bytes: bytes) -> list[OCREntity]:
        """Extracts text and bounding boxes from a screenshot."""
        if not self.enabled:
            return []
            
        try:
            # We must run this in a thread because pytesseract is blocking and CPU heavy
            import asyncio
            return await asyncio.to_thread(self._run_tesseract, screenshot_bytes)
        except Exception as e:
            logger.exception("ocr_failed", error=str(e))
            return []
            
    def _run_tesseract(self, screenshot_bytes: bytes) -> list[OCREntity]:
        image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        
        # Use Output.DICT to get bounding boxes
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        entities = []
        n_boxes = len(data['level'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                # Filter out very small boxes or artifacts
                if len(text) > 2 or text.isalnum():
                    entities.append(OCREntity(text=text, x=x, y=y, width=w, height=h))
                    
        return entities
