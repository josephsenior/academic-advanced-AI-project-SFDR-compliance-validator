"""
Cover Page Compliance Rules

Section 2 - Cover Page Rules.
"""

from dataclasses import dataclass


@dataclass
class CoverPageRules:
    """Section 2 - Cover Page Rules"""
    
    # Required elements
    MUST_INCLUDE_FUND_NAME: bool = True
    MUST_INCLUDE_DATE: bool = True
    MUST_INCLUDE_PROMOTIONAL_MENTION: bool = True
    MUST_INCLUDE_TARGET_AUDIENCE: bool = True
    
    # Premarketing warning
    PREMARKETING_REQUIRES_WARNING: bool = True
    PREMARKETING_WARNING_MUST_BE_RED_BOLD: bool = True
    PREMARKETING_WARNING_PHRASES = [
        "document de pré-marketing",
        "pre-marketing document",
        "Vormarketing-Dokument",
        "documento de pre-marketing"
    ]
    
    # Confidentiality notice
    MUST_INCLUDE_DO_NOT_DISCLOSE: bool = True
    DO_NOT_DISCLOSE_PHRASES = [
        "ne pas diffuser",
        "do not disclose",
        "ne pas diffuser",
        "nicht weitergeben",
        "confidentiel",
        "confidential",
        "vertraulich"
    ]
    
    # Client-specific document requirements
    CLIENT_SPECIFIC_MUST_INCLUDE_CLIENT_NAME: bool = True

