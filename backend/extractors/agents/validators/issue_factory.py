"""
Factory functions for creating ComplianceIssue objects
"""

import re
from typing import Optional

from ...rules import (
    ComplianceIssue,
    ComplianceIssueType,
    ClientType,
    FundType
)


def create_source_date_issue(
    issue_type_str: str,
    location: str,
    message: str,
    table_index: Optional[int] = None,
    slide_number: Optional[int] = None,
    page_number: Optional[int] = None,
    severity: str = "error",
    client_type: Optional[ClientType] = None,
    fund_type: Optional[FundType] = None
) -> ComplianceIssue:
    """Helper to create source/date ComplianceIssue"""
    # Map old issue type strings to new enum values
    issue_type_map = {
        "missing_source": ComplianceIssueType.MISSING_SOURCE,
        "missing_date": ComplianceIssueType.MISSING_DATE_INFO,
        "both_missing": ComplianceIssueType.BOTH_MISSING,
        "date_too_old": ComplianceIssueType.DATE_TOO_OLD,
        "invalid_date_format": ComplianceIssueType.INVALID_DATE_FORMAT,
        "date_inconsistent": ComplianceIssueType.DATE_INCONSISTENT,
    }
    
    issue_type = issue_type_map.get(issue_type_str, ComplianceIssueType.MISSING_SOURCE_DATE)
    
    # Extract slide number from location if not provided
    if slide_number is None and "slide" in location.lower():
        match = re.search(r'slide\s+(\d+)', location, re.IGNORECASE)
        if match:
            slide_number = int(match.group(1))
    
    return ComplianceIssue(
        issue_type=issue_type,
        issue_category="source_date",
        rule_reference="Section 1 - Source and Date Requirements",
        location=location,
        slide_number=slide_number,
        page_number=page_number,
        table_index=table_index,
        severity=severity,
        message=message,
        context=None,
        suggestion="Add source and date information to this table/chart",
        client_type=client_type,
        fund_type=fund_type,
        auto_fixable=True
    )


def create_numerical_issue(
    location: str,
    message: str,
    document_value: float,
    reference_value: Optional[float] = None,
    reference_source: Optional[str] = None,
    period: Optional[str] = None,
    basis: Optional[str] = None,
    label: Optional[str] = None,
    tolerance: Optional[float] = None,
    severity: str = "error",
    client_type: Optional[ClientType] = None,
    fund_type: Optional[FundType] = None
) -> ComplianceIssue:
    """Helper to create numerical validation ComplianceIssue"""
    # Extract slide number from location
    slide_number = None
    if "slide" in location.lower():
        match = re.search(r'slide\s+(\d+)', location, re.IGNORECASE)
        if match:
            slide_number = int(match.group(1))
    
    # Build context string
    context_parts = []
    if label:
        context_parts.append(f"Label: {label}")
    if period:
        context_parts.append(f"Period: {period}")
    if basis:
        context_parts.append(f"Basis: {basis}")
    context_parts.append(f"Document value: {document_value}")
    if reference_value is not None:
        context_parts.append(f"Reference value: {reference_value}")
        diff = abs(document_value - reference_value)
        context_parts.append(f"Difference: {diff}")
    
    context = " | ".join(context_parts)
    
    # Build suggestion
    if reference_value is not None:
        suggestion = f"Update value to match reference: {reference_value}"
    else:
        suggestion = "Verify this value against official reference documents (Prospectus, KID, SFDR)"
    
    # Build details dict
    details = {
        "document_value": document_value,
        "reference_value": reference_value,
        "reference_source": reference_source,
        "period": period,
        "basis": basis,
        "label": label,
        "tolerance": tolerance
    }
    
    return ComplianceIssue(
        issue_type=ComplianceIssueType.NUMERICAL_MISMATCH,
        issue_category="numerical",
        rule_reference="Section 1 - Numerical Consistency",
        location=location,
        slide_number=slide_number,
        severity=severity,
        message=message,
        context=context,
        suggestion=suggestion,
        client_type=client_type,
        fund_type=fund_type,
        details=details
    )


def create_cross_reference_issue(
    issue_type_str: str,
    location: str,
    message: str,
    value1: Optional[float] = None,
    value2: Optional[float] = None,
    location1: Optional[str] = None,
    location2: Optional[str] = None,
    period: Optional[str] = None,
    severity: str = "error",
    client_type: Optional[ClientType] = None,
    fund_type: Optional[FundType] = None
) -> ComplianceIssue:
    """Helper to create cross-reference ComplianceIssue"""
    issue_type_map = {
        "performance_mismatch": ComplianceIssueType.PERFORMANCE_MISMATCH,
        "duplicate_inconsistency": ComplianceIssueType.DUPLICATE_INCONSISTENCY,
    }
    
    issue_type = issue_type_map.get(issue_type_str, ComplianceIssueType.PERFORMANCE_MISMATCH)
    
    # Extract slide number
    slide_number = None
    if "slide" in location.lower():
        match = re.search(r'slide\s+(\d+)', location, re.IGNORECASE)
        if match:
            slide_number = int(match.group(1))
    
    # Build context
    context_parts = []
    if value1 is not None:
        context_parts.append(f"Value 1: {value1} at {location1 or 'unknown'}")
    if value2 is not None:
        context_parts.append(f"Value 2: {value2} at {location2 or 'unknown'}")
    if period:
        context_parts.append(f"Period: {period}")
    if value1 is not None and value2 is not None:
        diff = abs(value1 - value2)
        context_parts.append(f"Difference: {diff}")
    
    context = " | ".join(context_parts) if context_parts else None
    
    # Build details
    details = {
        "value1": value1,
        "value2": value2,
        "location1": location1,
        "location2": location2,
        "period": period
    }
    
    return ComplianceIssue(
        issue_type=issue_type,
        issue_category="cross_reference",
        rule_reference="Section 1 - Cross-Reference Consistency",
        location=location,
        slide_number=slide_number,
        severity=severity,
        message=message,
        context=context,
        suggestion="Verify these values match across all references in the document",
        client_type=client_type,
        fund_type=fund_type,
        details=details
    )

