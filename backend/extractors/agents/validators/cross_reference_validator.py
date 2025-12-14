"""
Cross-Reference Validation Module

Validates that performance data in text matches table data.
"""

from typing import Dict, Any, List, Optional, Tuple

from ...rules import ComplianceIssue
from .issue_factory import create_cross_reference_issue
from .utils import format_location, values_match, infer_period_from_column


def validate_cross_references(
    extraction_result: Dict[str, Any],
    default_tolerance: float = 0.01
) -> Dict[str, Any]:
    """
    Cross-reference validation: Check if performance data in text matches table data.
    
    Returns:
        Dict with validation results
    """
    issues: List[ComplianceIssue] = []
    
    # Build a map of performance values from tables by period and basis
    table_performance_map: Dict[Tuple[Optional[str], Optional[str]], List[Dict[str, Any]]] = {}
    
    table_entries = extraction_result.get('performance_table_entries', [])
    for entry in table_entries:
        period = infer_period_from_column(entry.get('column'))
        # Try to infer basis from label
        basis = None
        label_lower = (entry.get('label') or '').lower()
        if 'net' in label_lower:
            basis = 'net'
        elif 'gross' in label_lower:
            basis = 'gross'
        
        key = (period, basis)
        if key not in table_performance_map:
            table_performance_map[key] = []
        table_performance_map[key].append(entry)
    
    # Compare with performance sections (text-based performance data)
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
            
            # Look for matching table entries
            key = (period, basis)
            matching_table_entries = table_performance_map.get(key, [])
            
            # Also try without basis (more lenient matching)
            if not matching_table_entries:
                key_no_basis = (period, None)
                matching_table_entries = table_performance_map.get(key_no_basis, [])
            
            if matching_table_entries:
                # Check if any table entry matches
                found_match = False
                for table_entry in matching_table_entries:
                    table_value = table_entry.get('value')
                    if table_value is not None:
                        if values_match(value, table_value, default_tolerance):
                            found_match = True
                            break
                
                if not found_match:
                    # Found mismatch
                    table_entry = matching_table_entries[0]
                    table_location = format_location(
                        table_entry.get('slide_number'),
                        None,
                        table_entry.get('table_index')
                    )
                    
                    issues.append(create_cross_reference_issue(
                        issue_type_str="performance_mismatch",
                        location=location_str,
                        message=f"Performance mismatch: text shows {value}% ({period}, {basis}) at {location_str}, but table shows {table_entry.get('value')}% at {table_location}",
                        value1=value,
                        value2=table_entry.get('value'),
                        location1=location_str,
                        location2=table_location,
                        period=period,
                        severity="error"
                    ))
    
    # Check for duplicate values with different periods (potential copy-paste errors)
    # Group performance entries by value and check if they have different periods
    value_period_map: Dict[float, List[Dict[str, Any]]] = {}
    for section in performance_sections:
        for entry in section.get('entries', []):
            value = entry.get('value')
            period = entry.get('period')
            if value is not None and period:
                if value not in value_period_map:
                    value_period_map[value] = []
                value_period_map[value].append({
                    'value': value,
                    'period': period,
                    'basis': entry.get('basis'),
                    'location': format_location(
                        section.get('slide_number'),
                        section.get('page_number'),
                        None
                    )
                })
    
    # Flag suspicious duplicates (same value, different periods)
    for value, entries in value_period_map.items():
        if len(entries) > 1:
            periods = [e['period'] for e in entries]
            if len(set(periods)) > 1:
                # Same value appears with different periods - potential error
                locations = [e['location'] for e in entries]
                issues.append(create_cross_reference_issue(
                    issue_type_str="duplicate_inconsistency",
                    location=", ".join(locations),
                    message=f"Suspicious duplicate: value {value}% appears with different periods ({', '.join(set(periods))}) at {', '.join(locations)}",
                    value1=value,
                    value2=value,
                    location1=locations[0],
                    location2=locations[1] if len(locations) > 1 else None,
                    period=", ".join(set(periods)),
                    severity="warning"
                ))
    
    return {
        'issues': issues
    }

