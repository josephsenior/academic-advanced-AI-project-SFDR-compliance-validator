"""
Compliance Rules Module

Contains all rules from "Synthèse règles présentations commerciales.docx"
for validating commercial presentations.

These rules are organized by section matching the source document.
"""

# Enums
from .enums import (
    ClientType,
    DocumentType,
    ManagementCompany,
    ESGApproach,
    FundType,
    PerformanceBasis,
    ComplianceIssueType,
)

# Constants
from .constants import (
    RETAIL_SHARE_CLASSES,
    PERFORMANCE_PERIODS,
    MIN_PERFORMANCE_HISTORY_YEARS_ANNUALIZED,
    MIN_PERFORMANCE_HISTORY_YEARS_OTHER,
    MIN_HISTORY_FOR_CUMULATIVE,
    MIN_HISTORY_FOR_ANY_PERFORMANCE,
    COUNTRIES_WITH_SPECIFIC_RULES,
)

# Models
from .models import ComplianceIssue

# Rule dataclasses
from .general import GeneralRules
from .cover_page import CoverPageRules
from .slide2 import Slide2Rules
from .content import ContentRules
from .esg import ESGRules
from .securities import SecuritiesMentionRules
from .performance import PerformanceRules, GermanyPerformanceRules
from .fund_types import StrategyRules, DatedFundRules, PrivateEquityRules
from .disclaimer import DisclaimerRules
from .fund_changes import FundChangesRules

# Helpers
from .helpers import (
    get_performance_disclaimer,
    get_backtest_disclaimer,
    get_simulation_disclaimer,
    is_retail_share_class,
    detect_language,
)

# Slide validation
from .slide_validation import SlideValidationRules

__all__ = [
    # Enums
    'ClientType',
    'DocumentType',
    'ManagementCompany',
    'ESGApproach',
    'FundType',
    'PerformanceBasis',
    'ComplianceIssueType',
    # Constants
    'RETAIL_SHARE_CLASSES',
    'PERFORMANCE_PERIODS',
    'MIN_PERFORMANCE_HISTORY_YEARS_ANNUALIZED',
    'MIN_PERFORMANCE_HISTORY_YEARS_OTHER',
    'MIN_HISTORY_FOR_CUMULATIVE',
    'MIN_HISTORY_FOR_ANY_PERFORMANCE',
    'COUNTRIES_WITH_SPECIFIC_RULES',
    # Models
    'ComplianceIssue',
    # Rules
    'GeneralRules',
    'CoverPageRules',
    'Slide2Rules',
    'ContentRules',
    'ESGRules',
    'SecuritiesMentionRules',
    'PerformanceRules',
    'GermanyPerformanceRules',
    'StrategyRules',
    'DatedFundRules',
    'PrivateEquityRules',
    'DisclaimerRules',
    'SimulationRules',
    'FundChangesRules',
    # Helpers
    'get_performance_disclaimer',
    'get_backtest_disclaimer',
    'get_simulation_disclaimer',
    'is_retail_share_class',
    'detect_language',
    # Slide validation
    'SlideValidationRules',
]

