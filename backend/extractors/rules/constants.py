"""
Compliance Rules Constants

Constants used across compliance validation rules.
"""

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

