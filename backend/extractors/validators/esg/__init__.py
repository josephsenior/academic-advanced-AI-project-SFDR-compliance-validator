"""
ESG Compliance Agent Module

Modularized ESG compliance validation system.
"""

from .models import (
    ESGLevel,
    ESGMentions,
    ImageAnalysisResult,
    ESGViolation,
    ESGComplianceOutput,
)
from .analyzer import ESGAnalyzer
from .validator import ESGComplianceAgent
from .loaders import DocumentLoader, MetadataLoader
from .reporting import generate_enhanced_compliance_report, save_report_as_pdf
from .utils import normalize_esg_level, extract_fund_metadata_from_prospectus

__all__ = [
    # Models
    'ESGLevel',
    'ESGMentions',
    'ImageAnalysisResult',
    'ESGViolation',
    'ESGComplianceOutput',
    # Classes
    'ESGAnalyzer',
    'ESGComplianceAgent',
    'DocumentLoader',
    'MetadataLoader',
    # Functions
    'normalize_esg_level',
    'extract_fund_metadata_from_prospectus',
    'generate_enhanced_compliance_report',
    'save_report_as_pdf',
]

