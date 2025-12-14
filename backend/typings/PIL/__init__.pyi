from typing import Any
from .Image import Image as ImageType
from .ImageOps import grayscale as grayscale, autocontrast as autocontrast
from .ImageFilter import MedianFilter as MedianFilter


class _ImageModule:
	Image: ImageType


# Provide a module-like `Image` symbol. Use `Any` as a fallback to satisfy
# annotations like `Image.Image` in the codebase while still exposing the
# `ImageType` class via runtime stubs above.
Image: Any

def open(fp: object) -> ImageType: ...
