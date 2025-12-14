"""
Utilities for document extraction
"""

from .text_utils import (
    split_sentences,
    detect_language_safe,
    detect_performance_blocks,
    detect_source_notes,
    parse_numeric_value,
    PERCENT_PATTERN,
    DATE_PATTERN,
    EMAIL_PATTERN,
    PHONE_PATTERN,
    ISIN_PATTERN,
    SHARE_CLASS_PATTERN,
)
from .keywords import (
    DISCLAIMER_KEYWORDS,
    GLOSSARY_KEYWORDS,
    COUNTRY_SECTION_KEYWORDS,
    ISSUER_SECTION_KEYWORDS,
    LEGAL_NOTICE_KEYWORDS,
    DISCLAIMER_CATEGORIES,
    detect_disclaimer_flags,
    detect_glossary,
    detect_legal_notice,
    categorize_disclaimer,
)
from .field_extractors import (
    extract_title_fields,
    extract_identifiers,
    extract_issuer_mentions,
    analyze_performance_sentence,
    parse_table_source,
    detect_countries,
    country_entries,
)
from .ocr_utils import (
    configure_tesseract,
    prepare_image_for_ocr,
    extract_text_from_image,
)
from .table_extractor import (
    normalize_table_rows,
    extract_pptx_table,
    extract_docx_table,
)

__all__ = [
    'split_sentences',
    'detect_language_safe',
    'detect_performance_blocks',
    'detect_source_notes',
    'parse_numeric_value',
    'PERCENT_PATTERN',
    'DATE_PATTERN',
    'EMAIL_PATTERN',
    'PHONE_PATTERN',
    'ISIN_PATTERN',
    'SHARE_CLASS_PATTERN',
    'DISCLAIMER_KEYWORDS',
    'GLOSSARY_KEYWORDS',
    'COUNTRY_SECTION_KEYWORDS',
    'ISSUER_SECTION_KEYWORDS',
    'LEGAL_NOTICE_KEYWORDS',
    'DISCLAIMER_CATEGORIES',
    'detect_disclaimer_flags',
    'detect_glossary',
    'detect_legal_notice',
    'categorize_disclaimer',
    'extract_title_fields',
    'extract_identifiers',
    'extract_issuer_mentions',
    'analyze_performance_sentence',
    'parse_table_source',
    'detect_countries',
    'country_entries',
    'configure_tesseract',
    'prepare_image_for_ocr',
    'extract_text_from_image',
    'normalize_table_rows',
    'extract_pptx_table',
    'extract_docx_table',
]

