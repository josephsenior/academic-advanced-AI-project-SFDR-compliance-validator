"""
Numerical Data Validation Module

Validates numerical data against reference documents (Prospectus, KID, SFDR).
"""

from typing import Dict, Any, List, Optional

from ...rules import ComplianceIssue
from ..reference_data import ReferenceData
from .issue_factory import create_numerical_issue
from .utils import format_location, values_match, infer_period_from_column
from .reference_data_utils import get_reference_performance, get_reference_table_value


def validate_numerical_data(
    extraction_result: Dict[str, Any],
    reference_data: Optional[ReferenceData],
    default_tolerance: float = 0.01,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate numerical data against reference documents.
    
    Returns:
        Dict with validation results
    """
    inconsistencies: List[ComplianceIssue] = []
    total_checked = 0
    matching = 0
    
    if not reference_data:
        return {
            'inconsistencies': [],
            'total_checked': 0,
            'matching': 0,
            'inconsistent': 0
        }
    
    # Validate performance sections
    performance_sections = extraction_result.get('performance_sections', [])
    for section in performance_sections:
        entries = section.get('entries', [])
        slide_num = section.get('slide_number')
        page_num = section.get('page_number')
        location_str = format_location(slide_num, page_num, None)
        
        for entry in entries:
            value = entry.get('value')
            period = entry.get('period')
            basis = entry.get('basis')
            
            if value is None:
                continue
            
            total_checked += 1
            
            # Look up reference value
            ref_value = get_reference_performance(reference_data, period, basis)
            
            if ref_value is None:
                # No reference data available for this period/basis
                inconsistencies.append(create_numerical_issue(
                    location=location_str,
                    message=f"Performance value {value}% ({period}, {basis}) at {location_str} cannot be validated - no reference data available",
                    document_value=value,
                    reference_value=None,
                    reference_source=reference_data.source_document if hasattr(reference_data, 'source_document') else None,
                    period=period,
                    basis=basis,
                    severity="warning"
                ))
            else:
                # Compare values with tolerance
                if values_match(value, ref_value, default_tolerance):
                    matching += 1
                else:
                    diff = abs(value - ref_value)
                    diff_pct = (diff / abs(ref_value) * 100) if ref_value != 0 else float('inf')
                    inconsistencies.append(create_numerical_issue(
                        location=location_str,
                        message=f"Performance mismatch at {location_str}: document shows {value}% but reference shows {ref_value}% (difference: {diff_pct:.2f}%)",
                        document_value=value,
                        reference_value=ref_value,
                        reference_source=reference_data.source_document if hasattr(reference_data, 'source_document') else None,
                        period=period,
                        basis=basis,
                        tolerance=default_tolerance,
                        severity="error"
                    ))
    
    # Validate performance table entries
    table_entries = extraction_result.get('performance_table_entries', [])
    for entry in table_entries:
        value = entry.get('value')
        label = entry.get('label')
        column = entry.get('column')
        slide_num = entry.get('slide_number')
        table_idx = entry.get('table_index')
        location_str = format_location(slide_num, None, table_idx)
        
        if value is None:
            continue
        
        total_checked += 1
        
        # Try to match against reference table data
        ref_value = get_reference_table_value(reference_data, label, column)
        
        if ref_value is None:
            # Try to infer period from column name
            period = infer_period_from_column(column)
            if period:
                # Try performance lookup
                ref_value = get_reference_performance(reference_data, period, None)
        
        if ref_value is None:
            inconsistencies.append(create_numerical_issue(
                location=location_str,
                message=f"Table entry '{label}' = {value}% at {location_str} cannot be validated - no reference data available",
                document_value=value,
                reference_value=None,
                reference_source=reference_data.source_document if hasattr(reference_data, 'source_document') else None,
                label=label,
                severity="warning"
            ))
        else:
            if values_match(value, ref_value, default_tolerance):
                matching += 1
            else:
                diff = abs(value - ref_value)
                diff_pct = (diff / abs(ref_value) * 100) if ref_value != 0 else float('inf')
                inconsistencies.append(create_numerical_issue(
                    location=location_str,
                    message=f"Table entry mismatch at {location_str}: '{label}' shows {value}% but reference shows {ref_value}% (difference: {diff_pct:.2f}%)",
                    document_value=value,
                    reference_value=ref_value,
                    reference_source=reference_data.source_document if hasattr(reference_data, 'source_document') else None,
                    label=label,
                    tolerance=default_tolerance,
                    severity="error"
                ))
    
    return {
        'inconsistencies': inconsistencies,
        'total_checked': total_checked,
        'matching': matching,
        'inconsistent': len(inconsistencies)
    }

