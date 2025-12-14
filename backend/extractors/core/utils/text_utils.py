"""
Text Processing Utilities

Utilities for text processing, language detection, and pattern matching.
"""

import re
from typing import List, Optional
from langdetect import detect as detect_language

# Pattern definitions
PERCENT_PATTERN = re.compile(r"\b\d{1,3}(?:[\.,]\d+)?\s?%")
DATE_PATTERN = re.compile(
    r"(\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b|\b\d{4}[\-/]\d{1,2}[\-/]\d{1,2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b)",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{6,}")
ISIN_PATTERN = re.compile(r"\b[A-Z]{2}[A-Z0-9]{9}[0-9]\b")
SHARE_CLASS_PATTERN = re.compile(r"\b[A-Z]{1,4}-[A-Z]{3}\b")


def split_sentences(text: str) -> List[str]:
    """Split text into sentences using conservative regex."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def detect_language_safe(text: str) -> Optional[str]:
    """Detect language with error handling."""
    if detect_language is None or len(text) < 20:
        return None
    try:
        return detect_language(text)
    except Exception:
        return None


def detect_performance_blocks(text: str) -> List[str]:
    """Detect sentences containing percentage values."""
    blocks = []
    for sentence in split_sentences(text):
        if PERCENT_PATTERN.search(sentence):
            blocks.append(sentence)
    return blocks


def detect_source_notes(text: str) -> List[str]:
    """Detect source/date notes in text."""
    lowered = text.lower()
    notes = []
    if "source" in lowered or "date" in lowered:
        notes.append(text.strip())
    return notes


def parse_numeric_value(cell: str) -> Optional[float]:
    """Parse numeric value from cell text."""
    cleaned = cell.strip().replace('%', '').replace(' ', '').replace(',', '.')
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None

