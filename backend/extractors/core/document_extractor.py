"""
Document Text Extractor
========================

This module focuses exclusively on **data extraction/structuring**, which is the
foundation for all subsequent compliance agents (disclaimer checks, ESG limits,
registration validation, etc.).  The goal is to produce a rich, opinionated
representation of a marketing document without performing any compliance logic
here – that work remains for later modules.

### Design Choices

* We rely on lightweight, locally executable libraries (`python-pptx`,
  `python-docx`, `pdf2image`, `pytesseract`) so the extraction step remains
  reproducible and auditable.  Cloud OCR services could offer higher accuracy,
  but they introduce latency, cost, and possibly data residency concerns.  We
  keep the interface flexible so a future implementation could swap the OCR
  layer behind the same data structure if needed.
* The extractor enriches the raw text with **presentation-aware metadata** such
  as slide roles, detected disclaimers, country mentions, and table source
  notes.  These heuristics are intentionally simple (regex/keyword driven) so
  they are deterministic and easy to troubleshoot.  More advanced NLP models
  can sit on top later, but the downstream compliance agents already have
  immediately useful signals.
* Where heuristics may produce false positives (e.g., any sentence containing a
  percentage might not be a performance statement), we surface both the signal
  and the original text fragment so that validators – human or automated – can
  double-check the context.
"""

from pathlib import Path
from typing import Dict, Any

# Import utility modules
from .utils import configure_tesseract
# Import format-specific extractors
from .formats import extract_pptx, extract_docx, extract_pdf
from .utils import (
    extract_title_fields,
    extract_identifiers,
    categorize_disclaimer,
    analyze_performance_sentence,
    extract_issuer_mentions,
    country_entries,
    detect_legal_notice,
)


class DocumentExtractor:
    """
    Extract text and tables from various document formats.
    
    This class orchestrates document extraction by delegating to format-specific
    extractors (PPTX, DOCX, PDF) based on the file extension.
    """
    
    def __init__(self, enable_chart_analysis: bool = True):
        """
        Initialize the document extractor.
        
        Args:
            enable_chart_analysis: Whether to enable chart analysis using LLM
        """
        # Configure Tesseract
        _, self.tesseract_lang, self.tesseract_config = configure_tesseract()
        
        # Initialize chart analyzer if enabled
        self.enable_chart_analysis = enable_chart_analysis
        self.chart_analyzer = None
        if enable_chart_analysis:
            try:
                from .chart_analyzer import ChartAnalyzer
                self.chart_analyzer = ChartAnalyzer(use_llm=True)
            except Exception as e:
                print(f"Warning: Chart analyzer not available: {e}")
                self.enable_chart_analysis = False

        # Define supported formats with wrapper functions
        self.supported_formats = {
            '.pptx': lambda path: extract_pptx(
                path,
                chart_analyzer=self.chart_analyzer,
                enable_chart_analysis=self.enable_chart_analysis,
                tesseract_lang=self.tesseract_lang,
                tesseract_config=self.tesseract_config
            ),
            '.docx': lambda path: extract_docx(
                path,
                tesseract_lang=self.tesseract_lang,
                tesseract_config=self.tesseract_config
            ),
            '.pdf': lambda path: extract_pdf(
                path,
                tesseract_lang=self.tesseract_lang,
                tesseract_config=self.tesseract_config
            )
        }
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and tables from document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict with extracted data including:
            - text: Full extracted text
            - slides/pages/paragraphs: Structured content
            - tables: Extracted table data
            - performance_sections: Detected performance data
            - structure: Document structure metadata
            - identifiers: ISINs and share classes
            - country_entries: Country mentions
            - issuer_mentions: Issuer references
            - title_information: Title page metadata
        """
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type from extension
        file_ext = file_path.suffix.lower()
        
        # Check if format is supported
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")

        # Get appropriate extraction function
        extractor_func = self.supported_formats[file_ext]
        
        try:
            # Call appropriate function (pptx, docx, or pdf)
            result = extractor_func(file_path)
            result['extraction_method'] = file_ext[1:]
            result['file_path'] = str(file_path)
            result['file_size'] = file_path.stat().st_size
            return result
        except Exception as e:
            # If error occurs, return error
            return {
                'error': str(e),
                'extraction_method': file_ext[1:],
                'file_path': str(file_path)
            }

    # Compatibility wrappers for legacy test helpers
    def _extract_title_fields(self, text: str):
        return extract_title_fields(text)

    def _extract_identifiers(self, text: str, location: Dict[str, Any]):
        return extract_identifiers(text, location)

    def _categorize_disclaimer(self, text: str):
        return categorize_disclaimer(text)

    def _analyze_performance_sentence(self, sentence: str):
        return analyze_performance_sentence(sentence)

    def _extract_issuer_mentions(self, text: str, location: Dict[str, Any]):
        return extract_issuer_mentions(text, location)

    def _country_entries(self, countries, heading, sentence, location: Dict[str, Any]):
        return country_entries(countries, heading, sentence, location)

    def _detect_legal_notice(self, text: str) -> bool:
        return detect_legal_notice(text)
    

def extract_document(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to extract document.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dict with extracted data
    """
    extractor = DocumentExtractor()
    return extractor.extract(file_path)

