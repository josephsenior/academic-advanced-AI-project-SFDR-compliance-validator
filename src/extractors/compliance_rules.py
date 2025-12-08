"""
Compliance Rules Module

Contains all rules from "Synthèse règles présentations commerciales.docx"
for validating commercial presentations.

These rules are organized by section matching the source document.
"""

from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field
from enum import Enum
from dataclasses import dataclass


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

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


# Retail share classes
RETAIL_SHARE_CLASSES = {"CR", "DR", "CN", "DN", "GC"}

# Performance periods in order of priority
PERFORMANCE_PERIODS = ["10Y", "5Y", "3Y", "1Y", "YTD", "MTD", "SINCE_INCEPTION"]

# Minimum performance history requirements
MIN_PERFORMANCE_HISTORY_YEARS_ANNUALIZED = 10
MIN_PERFORMANCE_HISTORY_YEARS_OTHER = 5
MIN_HISTORY_FOR_CUMULATIVE = 3  # Years before cumulative can be shown
MIN_HISTORY_FOR_ANY_PERFORMANCE = 1  # Less than 1 year = no performance display

# Countries with specific rules
COUNTRIES_WITH_SPECIFIC_RULES = {
    "germany": "DE",
    "belgium": "BE",
    "switzerland": "CH",
    "france": "FR"
}


# ============================================================================
# RULE DEFINITIONS - SECTION 1: GENERAL RULES
# ============================================================================

@dataclass
class GeneralRules:
    """Section 1 - General Rules"""
    
    # Disclaimer requirements
    RETAIL_REQUIRES_RETAIL_DISCLAIMERS: bool = True
    PROFESSIONAL_REQUIRES_PROFESSIONAL_DISCLAIMERS: bool = True
    
    # Source and date requirements
    ALL_DATA_CHARTS_REQUIRE_SOURCE_AND_DATE: bool = True
    SOURCE_MUST_BE_IN_FOOTNOTE: bool = True
    
    # SRI requirements
    SRI_MUST_BE_ON_SAME_SLIDE_AS_DISCLAIMER: bool = True
    
    # Glossary requirements for retail
    RETAIL_REQUIRES_GLOSSARY: bool = True
    GLOSSARY_TERMS_MUST_BE_IN_DOCUMENT: bool = True
    
    # Risk warning formatting
    RISK_WARNINGS_MUST_BE_BOLD: bool = True
    RISK_WARNINGS_SAME_FONT_AS_MAIN: bool = True
    RISK_WARNINGS_MUST_BE_VISIBLE: bool = True  # Not in footnotes
    
    # Opinion attenuation
    OPINIONS_MUST_BE_ATTENUATED: bool = True
    ATTENUATION_PHRASES = [
        "selon notre opinion",
        "selon nos analyses", 
        "le fonds a pour objectif de",
        "according to our opinion",
        "according to our analysis",
        "the fund aims to",
        "in our view",
        "we believe",
        "in unserer Einschätzung",
        "unserer Meinung nach"
    ]
    
    # Strategy must match legal docs
    STRATEGY_MUST_MATCH_LEGAL_DOCS: bool = True
    
    # Registration abroad compliance
    MARKETING_COUNTRIES_MUST_MATCH_REGISTRATION: bool = True
    
    # Internal limits prohibition
    INTERNAL_LIMITS_PROHIBITED: bool = True
    
    # Anglicisms in retail
    RETAIL_AVOID_ANGLICISMS: bool = True
    ANGLICISMS_MUST_BE_DEFINED: bool = True
    
    # Strategy vs Fund confusion
    NO_STRATEGY_FUND_CONFUSION: bool = True
    
    # Other funds mention
    NO_OTHER_FUNDS_MENTION_UNLESS_RANGE: bool = True
    
    # ETF liquidity
    ETF_CANNOT_BE_CALLED_LIQUID: bool = True
    
    # Belgium FSMA
    BELGIUM_RETAIL_REQUIRES_FSMA_VALIDATION: bool = True
    
    # Language alignment
    MULTILINGUAL_MUST_BE_ALIGNED: bool = True


# ============================================================================
# RULE DEFINITIONS - SECTION 2: COVER PAGE RULES
# ============================================================================

@dataclass
class CoverPageRules:
    """Section 2 - Cover Page Rules for Standard Presentation (~30 pages)"""
    
    # Required elements
    MUST_INCLUDE_FUND_NAME: bool = True
    MUST_INCLUDE_MONTH_YEAR: bool = True
    MUST_INCLUDE_PROMOTIONAL_MENTION: bool = True
    MUST_INCLUDE_TARGET_AUDIENCE: bool = True  # retail or professional
    
    # Promotional mention phrases
    PROMOTIONAL_MENTIONS = [
        "document promotionnel",
        "promotional document",
        "Werbedokument",
        "à caractère promotionnel",
        "marketing document",
        "zu Werbezwecken"
    ]
    
    # Pre-marketing requirements
    PREMARKETING_WARNING_REQUIRED: bool = True
    PREMARKETING_MUST_BE_RED: bool = True
    PREMARKETING_MUST_BE_BOLD: bool = True
    PREMARKETING_WARNING_FR = """VEUILLEZ NOTER QUE LE FONDS N'A PAS ENCORE ÉTÉ AGRÉÉ PAR L'AUTORITÉ DES MARCHÉS FINANCIERS (à adapter selon le régulateur) ET N'A PAS ÉTÉ AUTORISÉ À ÊTRE COMMERCIALISÉ EN FRANCE OU DANS D'AUTRES ÉTATS MEMBRES DE L'UNION EUROPÉENNE OU DANS TOUTE AUTRE JURIDICTION.
LES INVESTISSEURS DÉCLARENT ET RECONNAISSENT QU'AUCUNE OFFRE OU PLACEMENT OU SOLLICITATION DIRECTE OU INDIRECTE N'A ÉTÉ FAITE À L'INITIATIVE DE LA SOCIÉTÉ DE GESTION.
CETTE PRÉSENTATION VOUS EST SOUMISE SUR UNE BASE CONFIDENTIELLE ET UNIQUEMENT À DES FINS DE DISCUSSION. ELLE NE CONSTITUE PAS UNE OFFRE OU UNE INVITATION À SOUSCRIRE DES PARTS DU FONDS. LES INFORMATIONS QUI Y SONT PRÉSENTÉES NE DOIVENT PAS ÊTRE INVOQUÉES POUR SOUSCRIRE DES PARTS DU FONDS ET PEUVENT FAIRE L'OBJET DE MODIFICATIONS."""
    
    # Professional document requirements
    PROFESSIONAL_REQUIRES_DO_NOT_DISCLOSE: bool = True
    DO_NOT_DISCLOSE_PHRASES = [
        "do not disclose",
        "ne pas diffuser",
        "nicht weitergeben",
        "confidentiel",
        "confidential",
        "vertraulich"
    ]
    
    # Client-specific document requirements
    CLIENT_SPECIFIC_MUST_INCLUDE_CLIENT_NAME: bool = True


# ============================================================================
# RULE DEFINITIONS - SECTION 3: SLIDE 2 RULES
# ============================================================================

@dataclass
class Slide2Rules:
    """Section 3 - Slide 2 Rules (after cover page)"""
    
    # Required elements
    MUST_INCLUDE_STANDARD_DISCLAIMER: bool = True
    MUST_ADAPT_FUND_NAME_IN_DISCLAIMER: bool = True
    MUST_ADAPT_ELIGIBLE_CLIENTS: bool = True
    
    # Risk profile
    MUST_INCLUDE_COMPLETE_RISK_PROFILE: bool = True
    RISK_PROFILE_MUST_MATCH_PROSPECTUS: bool = True
    
    # Marketing countries
    MUST_INCLUDE_MARKETING_COUNTRIES: bool = True
    COUNTRIES_MUST_MATCH_REGISTRATION_ABROAD: bool = True


# ============================================================================
# RULE DEFINITIONS - SECTION 4: CONTENT RULES
# ============================================================================

@dataclass
class ContentRules:
    """Section 4 - Content Rules for following pages"""
    
    # Document cannot start with performance
    CANNOT_START_WITH_PERFORMANCE: bool = True
    MUST_START_WITH_FUND_PRESENTATION: bool = True
    
    # Morningstar rating requirements
    MORNINGSTAR_REQUIRES_DATE: bool = True
    MORNINGSTAR_REQUIRES_CATEGORY: bool = True
    
    # Portfolio lines
    PORTFOLIO_LINES_MUST_BE_IN_PROSPECTUS: bool = True
    
    # End of presentation
    MUST_INCLUDE_FUND_CHARACTERISTICS: bool = True
    
    # Data consistency
    DATA_MUST_MATCH_LEGAL_DOCS: bool = True  # KID, Prospectus, SFDR Annex
    
    # Validation responsibility
    MUST_INDICATE_VALIDATION_RESPONSIBLE: bool = True
    
    # Management team
    TEAM_MAY_CHANGE_DISCLAIMER_REQUIRED: bool = True
    TEAM_DISCLAIMER_PHRASES = [
        "L'équipe est susceptible de changer",
        "The team is subject to change",
        "Das Team kann sich ändern",
        "The management team may change"
    ]


# ============================================================================
# RULE DEFINITIONS - SECTION 4.1: ESG RULES
# ============================================================================

@dataclass
class ESGRules:
    """Section 4.1 - ESG Communication Rules (excluding professional funds)"""
    
    # ESG approach thresholds
    ENGAGEANTE_MIN_EXCLUSION_PCT: float = 20.0
    ENGAGEANTE_MIN_COVERAGE_PCT: float = 90.0
    
    # Communication limits
    ENGAGEANTE_NO_LIMIT: bool = True
    REDUITE_MAX_VOLUME_PCT: float = 10.0  # Max 10% of presentation volume
    LIMITEE_ONLY_FOR_INSTITUTIONAL_PRO: bool = True
    OTHER_FUNDS_ONLY_OBAM_EXCLUSIONS: bool = True
    
    # ESG keywords to detect
    ESG_KEYWORDS = [
        "ESG", "environnement", "environment", "Umwelt",
        "social", "sozial", "governance", "gouvernance",
        "durable", "sustainable", "nachhaltig",
        "responsable", "responsible", "verantwortlich",
        "ISR", "SRI", "carbon", "carbone", "Kohlenstoff",
        "climat", "climate", "Klima", "green", "vert", "grün",
        "impact", "éthique", "ethical", "ethisch"
    ]


# ============================================================================
# RULE DEFINITIONS - SECTION 4.2: SECURITIES MENTION RULES
# ============================================================================

@dataclass
class SecuritiesMentionRules:
    """Section 4.2 - Rules for mentioning securities in presentations"""
    
    # PROHIBITED actions
    NO_INVESTMENT_RECOMMENDATIONS: bool = True
    NO_VALUATION_MENTIONS: bool = True  # undervalued/overvalued
    NO_INVESTMENT_STRATEGY_SUGGESTIONS: bool = True
    NO_SECURITIES_COMPARISON: bool = True
    NO_MULTIPLE_MENTIONS_SAME_SECURITY: bool = True
    NO_FUTURE_PROJECTIONS_FOR_SECURITIES: bool = True
    NO_OPINION_ON_CURRENT_FUTURE_VALUE: bool = True
    NO_BUY_SELL_REINFORCE: bool = True
    NO_SPECIFIC_ANALYSIS_ON_SECURITY: bool = True
    NO_FAVORABLE_UNFAVORABLE_OPINION: bool = True
    
    # Prohibited phrases (investment recommendations)
    RECOMMENDATION_PHRASES = [
        "acheter", "buy", "kaufen",
        "vendre", "sell", "verkaufen",
        "renforcer", "reinforce", "verstärken",
        "sous-évalué", "undervalued", "unterbewertet",
        "surévalué", "overvalued", "überbewertet",
        "correctement évalué", "correctly valued", "korrekt bewertet",
        "nous recommandons", "we recommend", "wir empfehlen",
        "à notre avis", "in our opinion", "unserer Meinung nach",
        "selon nous", "according to us", "nach unserer Einschätzung"
    ]
    
    # ALLOWED mentions
    ALLOWED_MARKET_TRENDS: bool = True
    ALLOWED_MACRO_INDICATORS: bool = True  # FX rates, interest rates, commodities
    ALLOWED_GENERAL_SECTORS: bool = True
    ALLOWED_FACTUAL_INFO: bool = True  # Recent events, public announcements
    ALLOWED_PORTFOLIO_HOLDINGS_WITH_PAST_PERF: bool = True
    ALLOWED_ILLUSTRATIVE_EXAMPLES: bool = True  # Without projections
    
    # Interview rules
    INTERVIEW_ONLY_PUBLIC_FACTS: bool = True
    INTERVIEW_CAN_COMMENT_HISTORICAL: bool = True
    INTERVIEW_NO_CURRENT_FUTURE_VALUE_OPINION: bool = True


# ============================================================================
# RULE DEFINITIONS - SECTION 4.3: PERFORMANCE RULES
# ============================================================================

@dataclass
class PerformanceRules:
    """Section 4.3 - Performance Display Rules"""
    
    # Document structure
    CANNOT_START_WITH_PERFORMANCE: bool = True
    PERFORMANCE_NOT_CENTRAL_ELEMENT: bool = True
    PERFORMANCE_SAME_FONT_AS_TEXT: bool = True
    PERFORMANCE_NOT_DISPROPORTIONATE: bool = True
    
    # Retail share classes only for retail docs
    RETAIL_ONLY_RETAIL_SHARES: bool = True
    RETAIL_SHARE_CLASSES = ["CR", "DR", "CN", "DN", "GC"]
    
    # Minimum duration requirements
    MIN_YEARS_ANNUALIZED: int = 10
    MIN_YEARS_OTHER: int = 5
    USE_SINCE_INCEPTION_IF_LESS: bool = True
    
    # Performance format
    MUST_SHOW_ROLLING_ANNUAL: bool = True
    MUST_SHOW_ANNUALIZED: bool = True
    MUST_SHOW_CUMULATIVE: bool = True  # If >3 years
    NO_CUMULATIVE_IF_LESS_THAN_3_YEARS: bool = True  # Except YTD/MTD
    
    # YTD rules
    YTD_ONLY_WITH_FULL_HISTORY: bool = True  # Must show 10Y, 5Y, 3Y, 1Y too
    YTD_CANNOT_BE_ALONE: bool = True
    
    # Less than 1 year rules
    NO_PERFORMANCE_IF_LESS_THAN_1_YEAR: bool = True
    NAV_GRAPH_ALLOWED_IF_LESS_THAN_1_YEAR: bool = True
    NAV_TABLE_FOR_GERMANY_IF_LESS_THAN_1_YEAR: bool = True
    NO_MTD_PERFORMANCE: bool = True  # Except YTD
    
    # Benchmark requirements
    MUST_COMPARE_TO_OFFICIAL_BENCHMARK: bool = True
    MUST_COMPARE_TO_TARGET_IF_EXISTS: bool = True
    NO_UNOFFICIAL_BENCHMARK_COMPARISON: bool = True
    DELETED_BENCHMARK_MUST_SHOW_HISTORY: bool = True
    MODIFIED_BENCHMARK_MUST_CHAIN: bool = True
    
    # Other benchmark presentation
    OTHER_BENCHMARKS_IN_SEPARATE_SLIDE: bool = True
    OTHER_BENCHMARKS_NO_FUND_PERF: bool = True
    
    # Net vs Gross
    RETAIL_MUST_BE_NET: bool = True
    GROSS_REQUIRES_FEE_IMPACT_DISCLAIMER: bool = True
    
    # New share class
    NEW_SHARE_CAN_USE_EXISTING_SHARE_PERF: bool = True
    NEW_SHARE_MUST_MENTION_FEE_DIFFERENCE: bool = True
    
    # Source requirements
    MUST_INDICATE_PERIOD_AND_SOURCE: bool = True
    
    # Track record
    NO_OTHER_FUND_TRACK_RECORD_FOR_RETAIL: bool = True
    NO_STRATEGY_TRACK_RECORD_FOR_RETAIL: bool = True
    NO_TEAM_TRACK_RECORD_FOR_RETAIL: bool = True


# ============================================================================
# RULE DEFINITIONS - GERMANY SPECIFIC PERFORMANCE RULES
# ============================================================================

@dataclass
class GermanyPerformanceRules:
    """Germany-specific performance rules"""
    
    # Rolling performance requirements
    ROLLING_MUST_INCLUDE_SINCE_INCEPTION: bool = True
    FIRST_YEAR_INCLUDES_MAX_SUBSCRIPTION_FEE: bool = True
    LAST_YEAR_INCLUDES_MAX_REDEMPTION_FEE: bool = True
    
    # Less than 1 year
    ONLY_NAV_TABLE_NOT_GRAPH: bool = True


# ============================================================================
# RULE DEFINITIONS - STRATEGY PRESENTATION RULES (PROFESSIONAL ONLY)
# ============================================================================

@dataclass
class StrategyRules:
    """Rules for strategy presentations (professional clients only)"""
    
    # Client restriction
    PROFESSIONAL_ONLY: bool = True
    
    # Document structure
    CANNOT_START_WITH_PERFORMANCE: bool = True
    MUST_START_WITH_STRATEGY_PRESENTATION: bool = True
    
    # Performance duration
    MIN_YEARS: int = 10
    USE_SINCE_INCEPTION_IF_LESS: bool = True
    
    # Backtest
    BACKTEST_NO_MIN_PERIOD: bool = True
    
    # Cumulative
    NO_CUMULATIVE_ALONE_IF_LESS_THAN_3_YEARS: bool = True
    
    # YTD
    YTD_ONLY_WITH_FULL_HISTORY: bool = True
    
    # Benchmark
    MUST_COMPARE_TO_STRATEGY_BENCHMARK: bool = True
    CAN_COMPARE_TO_OTHER_BENCHMARK_INFO_ONLY: bool = True
    OTHER_BENCHMARK_MUST_BE_CONSISTENT: bool = True
    OTHER_BENCHMARK_MUST_BE_STABLE: bool = True
    
    # Gross vs Net
    CAN_SHOW_GROSS: bool = True
    GROSS_REQUIRES_DISCLAIMER: bool = True


# ============================================================================
# RULE DEFINITIONS - DATED FUNDS RULES
# ============================================================================

@dataclass
class DatedFundRules:
    """Rules for dated/target date funds"""
    
    # Active management dated funds - Retail
    ACTIVE_NO_YTM_FOR_RETAIL: bool = True
    ACTIVE_NO_YTW_FOR_RETAIL: bool = True
    
    # Buy and hold dated funds - Retail
    BUY_HOLD_CAN_SHOW_YTM: bool = True
    BUY_HOLD_CAN_SHOW_YTW: bool = True
    
    # Professional clients
    PROFESSIONAL_NO_RESTRICTION: bool = True


# ============================================================================
# RULE DEFINITIONS - PRIVATE EQUITY FUNDS RULES
# ============================================================================

@dataclass
class PrivateEquityRules:
    """Rules for Private Equity funds"""
    
    # Net IRR display
    NET_IRR_ONLY_FOR_PROFESSIONAL_DURING_LIFE: bool = True
    NO_NET_IRR_FOR_RETAIL_BEFORE_MATURITY: bool = True
    NO_INSTITUTIONAL_TRACK_RECORD_FOR_RETAIL: bool = True


# ============================================================================
# RULE DEFINITIONS - PERFORMANCE SIMULATIONS
# ============================================================================

@dataclass
class SimulationRules:
    """Rules for performance simulations"""
    
    # Future performance simulation
    FUTURE_NOT_BASED_ON_PAST_SIMULATIONS: bool = True
    FUTURE_BASED_ON_REASONABLE_HYPOTHESES: bool = True
    FUTURE_GROSS_MUST_SHOW_FEE_IMPACT: bool = True
    FUTURE_REALISTIC_MARKET_HYPOTHESES: bool = True
    FUTURE_CONSISTENT_VOLATILITY: bool = True
    FUTURE_CONSISTENT_WITH_HORIZON: bool = True
    
    # Past performance simulation
    PAST_ONLY_FOR_NEW_SHARE_CLASS: bool = True
    PAST_BASED_ON_EXISTING_SHARE: bool = True
    PAST_SHARE_PROPORTION_MUST_NOT_DIFFER_MUCH: bool = True
    PAST_EXISTING_SHARE_SIMULATION_PROHIBITED: bool = True
    PAST_MUST_RECALCULATE_FEES: bool = True


# ============================================================================
# RULE DEFINITIONS - MANDATORY DISCLAIMERS
# ============================================================================

@dataclass
class DisclaimerRules:
    """Mandatory disclaimers by context"""
    
    # Position requirement
    MUST_BE_BELOW_OR_BESIDE_PERFORMANCE: bool = True
    MUST_BE_READABLE: bool = True
    
    # Past performance disclaimer (required always)
    PAST_PERFORMANCE_DISCLAIMER_FR = "les performances passées ne présagent pas des performances futures et ne sont pas constantes dans le temps"
    PAST_PERFORMANCE_DISCLAIMER_EN = "past performance is not a reliable indication of future return and is not constant over time"
    PAST_PERFORMANCE_DISCLAIMER_DE = "Historische Wertentwicklungen, Simulationen oder Prognosen sind kein verlässlicher Indikator für künftige Wertentwicklungen und unterliegen im Zeitverlauf Schwankungen"
    
    # Backtest disclaimer (professional only, France only)
    BACKTEST_DISCLAIMER_FR = """Les chiffres se réfèrent à des simulations des performances passées. Ces simulations sont le résultat d'estimations d'OBAM SAS à un moment donné, sur la base de paramètres sélectionnés par Oddo BHF Asset Management, de conditions de marché à ce moment donné et de données historiques qui ne préjugent en rien de résultats futurs. En conséquence, ces simulations n'ont qu'une valeur indicative et ne sauraient constituer en aucune manière une promesse de rendement."""
    BACKTEST_DISCLAIMER_EN = """The figures refer to simulations of past performances. These simulations are the result of estimates by ODDO BHF AM at a given moment on the basis of parameters selected by ODDO BHF AM SAS/GmbH/Lux, market conditions at this given moment and historical data that are not a guide to future results. As a result, these simulations only have an indicative value and do not in any case constitute a promised return"""
    
    # Future simulation disclaimer
    FUTURE_SIMULATION_DISCLAIMER_FR = """La simulation présentée ne constitue pas une prévision de la performance future de vos investissements. Elle a seulement pour but d'illustrer les mécanismes de votre investissement sur la durée de placement. L'évolution de la valeur de votre investissement pourra s'écarter de ce qui est affiché, à la hausse comme à la baisse."""
    FUTURE_SIMULATION_DISCLAIMER_EN = """The simulation presented does not constitute a forecast of the future performance of your investments. It is solely designed to illustrate the mechanisms of your investment over the investment period. The value of your investment may deviate upwards or downwards from what is displayed."""
    
    # Multiple scenarios disclaimer (add to future simulation)
    MULTIPLE_SCENARIOS_DISCLAIMER_FR = """Les gains et les pertes peuvent dépasser les montants affichés, respectivement, dans les scénarios les plus favorables et les plus défavorables. En poursuivant, vous reconnaissez avoir pris connaissance de cet avertissement, l'avoir compris et en accepter le contenu."""
    MULTIPLE_SCENARIOS_DISCLAIMER_EN = """Gains and losses may exceed the presented amounts in respectively the most favourable and unfavourable scenarios. By continuing, you acknowledge that you have taken note of this disclaimer, have understood it and accept the content."""
    
    # Past simulation disclaimer
    PAST_SIMULATION_DISCLAIMER_FR = """Les performances affichées ne représentent pas les performances réelles de la part X sur une période donnée. Elles sont issues de simulations calculées par la société de gestion à partir des performances de la part Y du même fonds, retraitées des frais de gestion fixes, des frais de gestion variables, devises"""
    
    # Merger disclaimer
    MERGER_DISCLAIMER_TEMPLATE = """les performances présentées sont celles du Fonds « {absorbed_fund} » (de droit {jurisdiction} - lancé le {launch_date}) qui a été absorbé par le fonds « {absorbing_fund} » en date du {merger_date}. « {absorbing_fund} » poursuit exactement la même stratégie d'investissement et le même objectif de gestion que le fonds « {absorbed_fund} ». L'équipe de gestion et la structure des coûts restent inchangées."""


# ============================================================================
# RULE DEFINITIONS - FUND CHANGES RULES
# ============================================================================

@dataclass
class FundChangesRules:
    """Rules for funds with changes (benchmark, strategy, risk profile)"""
    
    # Change notification
    MUST_INDICATE_CHANGE_NATURE_AND_DATE: bool = True
    MUST_KEEP_PAST_PERFORMANCE: bool = True
    
    # Post-change performance
    CAN_SHOW_ONLY_POST_CHANGE_IF_MORE_THAN_1_YEAR: bool = True
    DEDICATED_FUNDS_EXCLUDED_FROM_POST_CHANGE_RULE: bool = True
    
    # Benchmark display
    BENCHMARK_ACCORDING_TO_PROSPECTUS: bool = True  # e.g., dividends included
    
    # Merger rules
    MERGER_CAN_USE_ABSORBED_HISTORY_IF: bool = True  # Conditions below
    MERGER_ABSORBING_CREATED_BY_MERGER: bool = True
    MERGER_SAME_STRATEGY: bool = True
    MERGER_SAME_OBJECTIVE: bool = True
    MERGER_SAME_TEAM: bool = True
    MERGER_SAME_COST_STRUCTURE: bool = True


# ============================================================================
# VALIDATION ISSUE TYPES
# ============================================================================

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


# ============================================================================
# COMPLIANCE ISSUE MODEL
# ============================================================================

class ComplianceIssue(BaseModel):
    """A single compliance issue found during validation"""
    
    issue_type: ComplianceIssueType = Field(description="Type of compliance issue")
    issue_category: str = Field(default="compliance", description="Category: 'source_date', 'numerical', 'esg', 'structure', 'registration', 'disclaimer', 'performance', 'cross_reference', 'compliance'")
    rule_reference: str = Field(description="Reference to rule in source document (e.g., 'Section 4.3')")
    location: str = Field(description="Location in document (slide/page)")
    slide_number: Optional[int] = Field(None, description="Slide number if applicable")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    table_index: Optional[int] = Field(None, description="Table index if applicable")
    chart_index: Optional[int] = Field(None, description="Chart index if applicable")
    severity: str = Field(default="error", description="'error', 'warning', or 'critical'")
    message: str = Field(description="Human-readable description")
    context: Optional[str] = Field(None, description="Relevant text context")
    suggestion: Optional[str] = Field(None, description="Suggested fix")
    
    # Additional context
    client_type: Optional[ClientType] = Field(None, description="Client type if relevant")
    country: Optional[str] = Field(None, description="Country if relevant")
    fund_type: Optional[FundType] = Field(None, description="Fund type if relevant")
    
    # Extended data for specific issue types
    details: Optional[Dict[str, Any]] = Field(None, description="Additional structured data (e.g., numerical values, ESG excerpts, performance data)")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_performance_disclaimer(language: str = "en") -> str:
    """Get the mandatory performance disclaimer in specified language"""
    disclaimers = {
        "fr": DisclaimerRules.PAST_PERFORMANCE_DISCLAIMER_FR,
        "en": DisclaimerRules.PAST_PERFORMANCE_DISCLAIMER_EN,
        "de": DisclaimerRules.PAST_PERFORMANCE_DISCLAIMER_DE
    }
    return disclaimers.get(language.lower(), disclaimers["en"])


def get_backtest_disclaimer(language: str = "en") -> str:
    """Get the backtest disclaimer in specified language"""
    disclaimers = {
        "fr": DisclaimerRules.BACKTEST_DISCLAIMER_FR,
        "en": DisclaimerRules.BACKTEST_DISCLAIMER_EN
    }
    return disclaimers.get(language.lower(), disclaimers["en"])


def get_simulation_disclaimer(language: str = "en", multiple_scenarios: bool = False) -> str:
    """Get the simulation disclaimer in specified language"""
    base = {
        "fr": DisclaimerRules.FUTURE_SIMULATION_DISCLAIMER_FR,
        "en": DisclaimerRules.FUTURE_SIMULATION_DISCLAIMER_EN
    }
    scenarios = {
        "fr": DisclaimerRules.MULTIPLE_SCENARIOS_DISCLAIMER_FR,
        "en": DisclaimerRules.MULTIPLE_SCENARIOS_DISCLAIMER_EN
    }
    
    disclaimer = base.get(language.lower(), base["en"])
    if multiple_scenarios:
        disclaimer += "\n" + scenarios.get(language.lower(), scenarios["en"])
    return disclaimer


def is_retail_share_class(share_class: str) -> bool:
    """Check if a share class is a retail share class"""
    return share_class.upper() in RETAIL_SHARE_CLASSES


def detect_language(text: str) -> str:
    """Simple language detection based on common words"""
    text_lower = text.lower()
    
    # French indicators
    fr_words = ["le", "la", "les", "de", "du", "des", "fonds", "gestion", "risque", "investissement"]
    fr_count = sum(1 for w in fr_words if f" {w} " in f" {text_lower} ")
    
    # German indicators
    de_words = ["der", "die", "das", "und", "ist", "fonds", "anlage", "risiko"]
    de_count = sum(1 for w in de_words if f" {w} " in f" {text_lower} ")
    
    # English indicators
    en_words = ["the", "and", "is", "fund", "investment", "risk", "performance"]
    en_count = sum(1 for w in en_words if f" {w} " in f" {text_lower} ")
    
    if fr_count > de_count and fr_count > en_count:
        return "fr"
    elif de_count > en_count:
        return "de"
    else:
        return "en"
