"""
Utility functions for working with reference data
"""

from typing import Optional
from ..reference_data import ReferenceData
from .utils import periods_match


def get_reference_performance(
    reference_data: Optional[ReferenceData],
    period: Optional[str],
    basis: Optional[str]
) -> Optional[float]:
    """Get reference performance value for given period and basis."""
    if not reference_data or not period:
        return None
    
    period_lower = period.lower() if period else None
    basis_lower = basis.lower() if basis else None
    
    # Handle both ReferenceData object and dict
    performance_data = None
    if isinstance(reference_data, ReferenceData):
        performance_data = reference_data.performance_data
    elif isinstance(reference_data, dict):
        performance_data = reference_data.get('performance_data', {})
    
    if not performance_data:
        return None
    
    # Try exact match first
    if period_lower in performance_data:
        period_data = performance_data[period_lower]
        if basis_lower and basis_lower in period_data:
            return period_data[basis_lower]
        # Try 'net' as default
        if 'net' in period_data:
            return period_data['net']
        # Return first available value
        if period_data:
            return list(period_data.values())[0]
    
    # Try fuzzy matching for period
    for ref_period, period_data in performance_data.items():
        if periods_match(period_lower, ref_period):
            if basis_lower and basis_lower in period_data:
                return period_data[basis_lower]
            if 'net' in period_data:
                return period_data['net']
            if period_data:
                return list(period_data.values())[0]
    
    return None


def get_reference_table_value(
    reference_data: Optional[ReferenceData],
    label: Optional[str],
    column: Optional[str] = None
) -> Optional[float]:
    """Get reference table value for given label and column."""
    if not reference_data or not label:
        return None
    
    label_lower = label.lower().strip()
    
    # Handle both ReferenceData object and dict
    table_data = None
    if isinstance(reference_data, ReferenceData):
        table_data = reference_data.table_data
    elif isinstance(reference_data, dict):
        table_data = reference_data.get('table_data', {})
    
    if not table_data:
        return None
    
    # Try exact match
    if label_lower in table_data:
        return table_data[label_lower]
    
    # Try fuzzy matching
    for ref_label, value in table_data.items():
        if label_lower in ref_label.lower() or ref_label.lower() in label_lower:
            return value
    
    return None

