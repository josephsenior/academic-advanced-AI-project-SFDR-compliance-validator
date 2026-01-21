"""
OCR Utilities

Utilities for image preprocessing and OCR operations.
"""

import os
from typing import Optional
from PIL import Image, ImageOps, ImageFilter
import pytesseract


def configure_tesseract() -> tuple[Optional[str], str, str]:
    """Configure Tesseract path from environment variable if provided."""
    if pytesseract is None:
        return None, "eng", "--psm 6"
    
    tesseract_cmd = os.getenv("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    tesseract_lang = os.getenv("TESSERACT_LANG", "eng")
    tesseract_config = os.getenv("TESSERACT_CONFIG", "--psm 6")
    
    return tesseract_cmd, tesseract_lang, tesseract_config


def prepare_image_for_ocr(image: Image.Image) -> Image.Image:
    """Prepare image for OCR by converting to grayscale and enhancing contrast."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    if ImageOps:
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        
    # Optimization: Upscale 2x for small text (Disclaimers)
    width, height = image.size
    image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
    
    # Optimization: Binarization (Thresholding) to remove noise
    # Threshold = 128
    image = image.point(lambda x: 0 if x < 128 else 255, '1')

    if ImageFilter:
        image = image.filter(ImageFilter.MedianFilter(size=3))
    return image


def extract_text_from_image(
    image: Image.Image,
    lang: str = "eng",
    config: str = "--psm 6"
) -> str:
    """Extract text from image using Tesseract OCR."""
    if pytesseract is None:
        raise ImportError("pytesseract not installed")
    
    prepared_image = prepare_image_for_ocr(image)
    return pytesseract.image_to_string(
        prepared_image,
        lang=lang,
        config=config
    ).strip()

