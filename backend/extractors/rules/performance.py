"""
Performance Compliance Rules

Section 4.3 - Performance Display Rules and Germany-specific rules.
"""

from dataclasses import dataclass


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


@dataclass
class GermanyPerformanceRules:
    """Germany-specific performance rules"""
    
    # Rolling performance requirements
    ROLLING_MUST_INCLUDE_SINCE_INCEPTION: bool = True
    FIRST_YEAR_INCLUDES_MAX_SUBSCRIPTION_FEE: bool = True
    LAST_YEAR_INCLUDES_MAX_REDEMPTION_FEE: bool = True
    
    # Less than 1 year
    ONLY_NAV_TABLE_NOT_GRAPH: bool = True

