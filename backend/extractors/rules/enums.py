"""
Compliance Rules Enums

All enums used in compliance validation.
"""

from enum import Enum


class ClientType(str, Enum):
    """Target client type for document"""
    RETAIL = "retail"
    PROFESSIONAL = "professional"
    WELL_INFORMED = "well_informed"  # For RAIF funds


class DocumentType(str, Enum):
    """Type of commercial document"""
    FUND_PRESENTATION = "fund_presentation"
    STRATEGY_PRESENTATION = "strategy_presentation"
    FUND_REPORTING = "fund_reporting"
    NEW_OFFER = "new_offer"
    VIDEO = "video"
    MONEY_MARKET_WEEKLY = "money_market_weekly"


class ManagementCompany(str, Enum):
    """Management company"""
    OBAM_SAS = "OBAM SAS"
    OBAM_GMBH = "OBAM GmbH"
    OBAM_LUX = "OBAM Lux"


class ESGApproach(str, Enum):
    """ESG approach classification per ESG Cartography"""
    ENGAGEANTE = "engageante"  # ≥20% exclusion AND ≥90% coverage
    REDUITE = "reduite"  # Limited to <10% of presentation
    LIMITEE_AU_PROSPECTUS = "limitee_au_prospectus"  # Only in prospectus
    NONE = "none"  # No ESG approach


class FundType(str, Enum):
    """Special fund types with specific rules"""
    STANDARD = "standard"
    DATED_FUND_ACTIVE = "dated_fund_active"  # Active management dated fund
    DATED_FUND_BUY_HOLD = "dated_fund_buy_hold"  # Buy and hold dated fund
    PRIVATE_EQUITY = "private_equity"
    ETF = "etf"
    MONEY_MARKET = "money_market"
    RAIF = "raif"  # Reserved Alternative Investment Fund


class PerformanceBasis(str, Enum):
    """Basis for performance calculation"""
    NET = "net"
    GROSS = "gross"
    BACKTEST = "backtest"
    SIMULATION = "simulation"


class ComplianceIssueType(str, Enum):
    """Types of compliance issues"""
    # General
    MISSING_RETAIL_DISCLAIMER = "missing_retail_disclaimer"
    MISSING_PROFESSIONAL_DISCLAIMER = "missing_professional_disclaimer"
    MISSING_SOURCE_DATE = "missing_source_date"
    MISSING_SRI_DISCLAIMER = "missing_sri_disclaimer"
    MISSING_GLOSSARY = "missing_glossary"
    RISK_WARNING_NOT_BOLD = "risk_warning_not_bold"
    RISK_WARNING_IN_FOOTNOTE = "risk_warning_in_footnote"
    OPINION_NOT_ATTENUATED = "opinion_not_attenuated"
    INTERNAL_LIMITS_PRESENT = "internal_limits_present"
    ETF_CALLED_LIQUID = "etf_called_liquid"
    
    # Cover page
    MISSING_FUND_NAME = "missing_fund_name"
    MISSING_DATE = "missing_date"
    MISSING_PROMOTIONAL_MENTION = "missing_promotional_mention"
    MISSING_TARGET_AUDIENCE = "missing_target_audience"
    MISSING_PREMARKETING_WARNING = "missing_premarketing_warning"
    PREMARKETING_NOT_RED_BOLD = "premarketing_not_red_bold"
    MISSING_DO_NOT_DISCLOSE = "missing_do_not_disclose"
    
    # Slide 2
    MISSING_STANDARD_DISCLAIMER = "missing_standard_disclaimer"
    DISCLAIMER_FUND_NAME_NOT_ADAPTED = "disclaimer_fund_name_not_adapted"
    MISSING_RISK_PROFILE = "missing_risk_profile"
    MISSING_MARKETING_COUNTRIES = "missing_marketing_countries"
    
    # Content
    STARTS_WITH_PERFORMANCE = "starts_with_performance"
    MORNINGSTAR_MISSING_DATE = "morningstar_missing_date"
    MORNINGSTAR_MISSING_CATEGORY = "morningstar_missing_category"
    PORTFOLIO_LINES_NOT_IN_PROSPECTUS = "portfolio_lines_not_in_prospectus"
    MISSING_FUND_CHARACTERISTICS = "missing_fund_characteristics"
    DATA_MISMATCH_WITH_LEGAL_DOCS = "data_mismatch_with_legal_docs"
    MISSING_TEAM_CHANGE_DISCLAIMER = "missing_team_change_disclaimer"
    
    # ESG
    ESG_COMMUNICATION_EXCEEDS_LIMIT = "esg_communication_exceeds_limit"
    ESG_NOT_ALLOWED_FOR_APPROACH = "esg_not_allowed_for_approach"
    ESG_RETAIL_NOT_ALLOWED = "esg_retail_not_allowed"
    ESG_OVERMENTIONED_ARTICLE8 = "esg_overmentioned_article8"
    ESG_FORBIDDEN_ARTICLE6 = "esg_forbidden_article6"
    ESG_LEVEL_MISMATCH = "esg_level_mismatch"
    ENGAGING_CRITERIA_NOT_MET = "engaging_criteria_not_met"
    ESG_VISUAL_VIOLATION = "esg_visual_violation"
    ESG_KEYWORD_OVERUSE = "esg_keyword_overuse"
    SFDR_ARTICLE_INCONSISTENCY = "sfdr_article_inconsistency"
    
    # Securities
    INVESTMENT_RECOMMENDATION = "investment_recommendation"
    SECURITY_VALUATION_MENTION = "security_valuation_mention"
    SECURITIES_COMPARISON = "securities_comparison"
    MULTIPLE_SECURITY_MENTIONS = "multiple_security_mentions"
    SECURITY_PROJECTION = "security_projection"
    BUY_SELL_RECOMMENDATION = "buy_sell_recommendation"
    
    # Performance
    PERFORMANCE_STARTS_DOCUMENT = "performance_starts_document"
    PERFORMANCE_DISPROPORTIONATE = "performance_disproportionate"
    NON_RETAIL_SHARES_IN_RETAIL = "non_retail_shares_in_retail"
    INSUFFICIENT_PERFORMANCE_HISTORY = "insufficient_performance_history"
    CUMULATIVE_LESS_THAN_3_YEARS = "cumulative_less_than_3_years"
    YTD_WITHOUT_FULL_HISTORY = "ytd_without_full_history"
    PERFORMANCE_LESS_THAN_1_YEAR = "performance_less_than_1_year"
    MTD_PERFORMANCE_SHOWN = "mtd_performance_shown"
    MISSING_BENCHMARK_COMPARISON = "missing_benchmark_comparison"
    MISSING_NET_PERFORMANCE_INDICATION = "missing_net_performance_indication"
    UNOFFICIAL_BENCHMARK_USED = "unofficial_benchmark_used"
    GROSS_WITHOUT_FEE_DISCLAIMER = "gross_without_fee_disclaimer"
    TRACK_RECORD_FOR_RETAIL = "track_record_for_retail"
    MISSING_PERFORMANCE_DISCLAIMER = "missing_performance_disclaimer"
    MISSING_PERIOD_SOURCE = "missing_period_source"
    
    # Country Registration
    UNREGISTERED_COUNTRY = "unregistered_country"
    MISSING_COUNTRY_DISCLAIMER = "missing_country_disclaimer"
    
    # Germany specific
    GERMANY_MISSING_SUBSCRIPTION_FEE = "germany_missing_subscription_fee"
    GERMANY_MISSING_REDEMPTION_FEE = "germany_missing_redemption_fee"
    GERMANY_NAV_GRAPH_NOT_TABLE = "germany_nav_graph_not_table"
    MISSING_UNKNOWN_NAV_DISCLAIMER = "missing_unknown_nav_disclaimer"
    NAV_FORMAT_ISSUE = "nav_format_issue"
    MISSING_GERMAN_SPECIFIC_DISCLAIMER = "missing_german_specific_disclaimer"
    
    # Dataset Details (Gap Analysis)
    MISSING_FWW_DISCLAIMER = "missing_fww_disclaimer"
    MISSING_WEEKLY_MM_LEGAL_CITATION = "missing_weekly_mm_legal_citation"
    MISSING_NEW_OFFER_DISCLAIMER = "missing_new_offer_disclaimer"
    
    # Backtest/Simulation
    BACKTEST_FOR_RETAIL = "backtest_for_retail"
    BACKTEST_MISSING_DISCLAIMER = "backtest_missing_disclaimer"
    SIMULATION_MISSING_DISCLAIMER = "simulation_missing_disclaimer"
    
    # Dated funds
    YTM_FOR_ACTIVE_RETAIL = "ytm_for_active_retail"
    YTW_FOR_ACTIVE_RETAIL = "ytw_for_active_retail"
    
    # Private equity
    NET_IRR_FOR_RETAIL = "net_irr_for_retail"
    INSTITUTIONAL_TRACK_FOR_RETAIL = "institutional_track_for_retail"
    
    # Language
    LANGUAGE_MISALIGNMENT = "language_misalignment"
    
    # Strategy
    STRATEGY_FOR_RETAIL = "strategy_for_retail"
    STRATEGY_FUND_CONFUSION = "strategy_fund_confusion"
    
    # Source/Date Issues
    MISSING_SOURCE = "missing_source"
    MISSING_DATE_INFO = "missing_date_info"
    BOTH_MISSING = "both_missing"
    DATE_TOO_OLD = "date_too_old"
    INVALID_DATE_FORMAT = "invalid_date_format"
    DATE_INCONSISTENT = "date_inconsistent"
    
    # Numerical Validation
    NUMERICAL_MISMATCH = "numerical_mismatch"
    TOLERANCE_EXCEEDED = "tolerance_exceeded"
    
    # Cross-Reference Issues
    PERFORMANCE_MISMATCH = "performance_mismatch"
    DUPLICATE_INCONSISTENCY = "duplicate_inconsistency"
    
    # New: Translation Consistency
    TRANSLATION_INCONSISTENCY = "translation_inconsistency"
    
    # New: Anglicism Detection
    ANGLICISM_UNDEFINED = "anglicism_undefined"
    
    # New: Visual Prominence
    VISUAL_CONTRAST_VIOLATION = "visual_contrast_violation"
    
    # New: Dynamic Prospectus
    FEE_DISCLOSURE_INCOMPLETE = "fee_disclosure_incomplete"

