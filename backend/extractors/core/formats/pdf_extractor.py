"""
PDF Document Extractor

Extracts text and metadata from PDF files using native text extraction or OCR.
"""

from pathlib import Path
from typing import Dict, List, Any
import re

from pdf2image import convert_from_path
import pytesseract

from ..utils import (
    detect_performance_blocks,
    detect_language_safe,
    detect_disclaimer_flags,
    detect_glossary,
    detect_legal_notice,
    categorize_disclaimer,
    extract_title_fields,
    extract_identifiers,
    extract_issuer_mentions,
    analyze_performance_sentence,
    detect_countries,
    country_entries,
    prepare_image_for_ocr,
    extract_text_from_image,
)
from ...parsers.registration import COUNTRY_PATTERNS


def extract_pdf(
    file_path: Path,
    tesseract_lang: str = "eng",
    tesseract_config: str = "--psm 6"
) -> Dict[str, Any]:
    """
    Extract text from PDF using OCR or native text extraction.
    
    Args:
        file_path: Path to PDF file
        tesseract_lang: Tesseract language code
        tesseract_config: Tesseract configuration
        
    Returns:
        Dict with extracted data
    """
    use_ocr = True
    pages_data: List[Dict[str, Any]] = []
    full_text: List[str] = []
    page_summaries: List[Dict[str, Any]] = []
    performance_sections: List[Dict[str, Any]] = []
    disclaimer_pages: List[int] = []
    glossary_pages: List[int] = []
    country_mentions = set()
    identifiers: List[Dict[str, Any]] = []
    country_entries_list: List[Dict[str, Any]] = []
    issuer_mentions: List[Dict[str, Any]] = []
    legal_notice_page = None
    performance_table_entries: List[Dict[str, Any]] = []

    # Try native text extraction first, using dynamic import to avoid static mypy import errors
    try:
        import importlib
        PyPDF2_mod = None
        try:
            PyPDF2_mod = importlib.import_module('PyPDF2')
        except Exception:
            PyPDF2_mod = None

        if PyPDF2_mod is not None:
            PdfReader = getattr(PyPDF2_mod, 'PdfReader', None)
        else:
            PdfReader = None

        if PdfReader is not None:
            reader = PdfReader(str(file_path))
            extracted_texts: List[str] = []
            for page in reader.pages:
                try:
                    t = page.extract_text() or ""
                except Exception:
                    t = ""
                extracted_texts.append(t.strip())

            total_chars = sum(len(t) for t in extracted_texts)
            if total_chars > 200:
                # Good quality text-based PDF; avoid OCR
                use_ocr = False
                for page_num, text in enumerate(extracted_texts, 1):
                    pages_data.append({
                        'page_number': page_num,
                        'text': text,
                        'ocr_engine': None
                    })
                    if text:
                        full_text.append(text)
                        # Compile regex patterns for detect_countries
                        compiled_patterns = {country: re.compile(pattern, re.IGNORECASE) for country, pattern in COUNTRY_PATTERNS.items()}
                        page_countries = detect_countries(text, compiled_patterns)
                        country_mentions.update(page_countries)

                        perf_sentences = detect_performance_blocks(text)
                        if perf_sentences:
                            entries = [analyze_performance_sentence(sentence) for sentence in perf_sentences]
                            performance_sections.append({
                                'page_number': page_num,
                                'sentences': perf_sentences,
                                'entries': entries
                            })

                        if detect_disclaimer_flags(text):
                            disclaimer_pages.append(page_num)

                        if detect_glossary(text):
                            glossary_pages.append(page_num)

                        if page_num == 1 and 'title_info' not in locals():
                            title_info = extract_title_fields(text)

                        identifier_entries = extract_identifiers(text, {'page_number': page_num})
                        if identifier_entries:
                            identifiers.extend(identifier_entries)

                        heading = None
                        country_entries_list.extend(
                            country_entries(page_countries, heading, text, {'page_number': page_num})
                        )

                        issuer_mentions.extend(
                            extract_issuer_mentions(text, {'page_number': page_num})
                        )

                        if legal_notice_page is None and detect_legal_notice(text):
                            legal_notice_page = page_num
            else:
                use_ocr = True
        else:
            use_ocr = True
    except Exception:
        use_ocr = True

    # Fall back to OCR if needed
    if use_ocr:
        if convert_from_path is None:
            raise ImportError("pdf2image not installed")
        if pytesseract is None:
            raise ImportError("pytesseract not installed")

        images = convert_from_path(str(file_path), dpi=300)
        for page_num, image in enumerate(images, 1):
            image = prepare_image_for_ocr(image)
            ocr_text = extract_text_from_image(image, tesseract_lang, tesseract_config)
            cleaned_text = ocr_text.strip()
            pages_data.append({
                'page_number': page_num,
                'text': cleaned_text,
                'ocr_engine': 'pytesseract'
            })
            if cleaned_text:
                full_text.append(cleaned_text)

                # Compile regex patterns for detect_countries
                compiled_patterns = {country: re.compile(pattern, re.IGNORECASE) for country, pattern in COUNTRY_PATTERNS.items()}
                page_countries = detect_countries(cleaned_text, compiled_patterns)
                country_mentions.update(page_countries)

                perf_sentences = detect_performance_blocks(cleaned_text)
                if perf_sentences:
                    entries = [analyze_performance_sentence(sentence) for sentence in perf_sentences]
                    performance_sections.append({
                        'page_number': page_num,
                        'sentences': perf_sentences,
                        'entries': entries
                    })

                if detect_disclaimer_flags(cleaned_text):
                    disclaimer_pages.append(page_num)

                if detect_glossary(cleaned_text):
                    glossary_pages.append(page_num)

                if page_num == 1 and 'title_info' not in locals():
                    title_info = extract_title_fields(cleaned_text)

                identifier_entries = extract_identifiers(cleaned_text, {'page_number': page_num})
                if identifier_entries:
                    identifiers.extend(identifier_entries)

                heading = None
                country_entries_list.extend(
                    country_entries(page_countries, heading, cleaned_text, {'page_number': page_num})
                )

                issuer_mentions.extend(
                    extract_issuer_mentions(cleaned_text, {'page_number': page_num})
                )

                if legal_notice_page is None and detect_legal_notice(cleaned_text):
                    legal_notice_page = page_num

            page_summaries.append({
                'page_number': page_num,
                'contains_disclaimer': page_num in disclaimer_pages,
                'disclaimer_categories': categorize_disclaimer(cleaned_text) if cleaned_text and page_num in disclaimer_pages else [],
                'contains_performance': any(section['page_number'] == page_num for section in performance_sections),
                'contains_glossary': page_num in glossary_pages,
                'countries': page_countries if cleaned_text else [],
                'language': detect_language_safe(cleaned_text) if cleaned_text else None,
            })

    # If pages_data was populated by text-extraction branch, ensure page_summaries
    # for that branch are present
    if not use_ocr and not page_summaries:
        for page_data in pages_data:
            page_num = page_data['page_number']
            text = page_data.get('text', '')
            # Compile regex patterns for detect_countries
            compiled_patterns = {country: re.compile(pattern, re.IGNORECASE) for country, pattern in COUNTRY_PATTERNS.items()}
            page_countries = detect_countries(text, compiled_patterns) if text else []
            page_summaries.append({
                'page_number': page_num,
                'contains_disclaimer': page_num in disclaimer_pages,
                'disclaimer_categories': categorize_disclaimer(text) if text and page_num in disclaimer_pages else [],
                'contains_performance': any(section['page_number'] == page_num for section in performance_sections),
                'contains_glossary': page_num in glossary_pages,
                'countries': page_countries,
                'language': detect_language_safe(text) if text else None,
            })

    return {
        'text': '\n'.join(full_text),
        'pages': pages_data,
        'page_summaries': page_summaries,
        'performance_sections': performance_sections,
        'disclaimer_pages': disclaimer_pages,
        'glossary_pages': glossary_pages,
        'structure': {
            'disclaimer_pages': disclaimer_pages,
            'performance_pages': [section['page_number'] for section in performance_sections],
            'glossary_pages': glossary_pages,
            'countries_detected': sorted(country_mentions),
            'disclaimer_categories': {
                page['page_number']: page['disclaimer_categories']
                for page in page_summaries if page.get('disclaimer_categories')
            },
            'country_entries': country_entries_list,
            'issuer_mentions': issuer_mentions,
            'has_glossary': bool(glossary_pages),
            'has_management_notice': legal_notice_page is not None,
            'legal_notice_page': legal_notice_page,
        },
        'identifiers': identifiers,
        'country_entries': country_entries_list,
        'issuer_mentions': issuer_mentions,
        'performance_table_entries': performance_table_entries,
        'title_information': title_info if 'title_info' in locals() else None,
        'tables': [],
        'total_pages': len(pages_data),
        'total_tables': 0,
        'ocr': use_ocr
    }

