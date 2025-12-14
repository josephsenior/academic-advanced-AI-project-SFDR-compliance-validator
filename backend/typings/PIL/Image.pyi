from typing import Any

class Image:
    mode: str

    def convert(self, mode: str) -> 'Image': ...
    def save(self, fp: Any, format: str | None = ...) -> None: ...
