"""
Utility functions for data consistency validation
"""

import re
from typing import Optional


def format_location(
    slide_number: Optional[int],
    page_number: Optional[int],
    table_index: Optional[int]
) -> str:
    """Format location string for reporting."""
    parts = []
    if slide_number is not None:
        parts.append(f"slide {slide_number}")
    if page_number is not None:
        parts.append(f"page {page_number}")
    if table_index is not None:
        parts.append(f"table {table_index}")
    
    if not parts:
        return "unknown location"
    
    return ", ".join(parts)


def values_match(value1: float, value2: float, tolerance: float) -> bool:
    """Check if two values match within tolerance."""
    if value1 == value2:
        return True
    
    if value2 == 0:
        return abs(value1) < tolerance
    
    diff = abs(value1 - value2)
    relative_diff = diff / abs(value2)
    return relative_diff <= tolerance


def periods_match(period1: Optional[str], period2: Optional[str]) -> bool:
    """Check if two period strings refer to the same period."""
    if not period1 or not period2:
        return False
    
    p1 = period1.lower().strip()
    p2 = period2.lower().strip()
    
    if p1 == p2:
        return True
    
    # Normalize common variations
    period_mappings = {
        '1y': ['1 year', '1yr', 'one year', '12 months'],
        '3y': ['3 years', '3yrs', 'three years', '36 months'],
        '5y': ['5 years', '5yrs', 'five years', '60 months'],
        'ytd': ['year to date', 'year-to-date'],
    }
    
    for key, variations in period_mappings.items():
        if p1 == key and p2 in variations:
            return True
        if p2 == key and p1 in variations:
            return True
    
    return False


def infer_period_from_column(column: Optional[str]) -> Optional[str]:
    """Infer period from column name (e.g., '1Y', 'YTD')."""
    if not column:
        return None
    
    column_lower = column.lower().strip()
    period_patterns = {
        '1y': r'\b1y\b|\b1\s*year\b|\b12\s*months\b',
        '3y': r'\b3y\b|\b3\s*years\b|\b36\s*months\b',
        '5y': r'\b5y\b|\b5\s*years\b|\b60\s*months\b',
        'ytd': r'\byt[d]\b|\byear\s*to\s*date\b',
    }
    
    for period, pattern in period_patterns.items():
        if re.search(pattern, column_lower):
            return period
    
    return None

