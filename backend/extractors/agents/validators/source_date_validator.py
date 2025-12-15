"""
Source and Date Validation Module

Validates that all tables and charts have proper source and date information.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dateutil import parser as date_parser

from ...rules import ComplianceIssue, ClientType, FundType
from .issue_factory import create_source_date_issue
from .utils import format_location


def validate_source_and_date(
    extraction_result: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    enable_date_validation: bool = True,
    max_date_age_days: int = 365,
    client_type: Optional[ClientType] = None,
    fund_type: Optional[FundType] = None
) -> Dict[str, Any]:
    """
    Validate that all tables/charts have source and date information.
    
    Returns:
        Dict with validation results containing ComplianceIssue objects
    """
    issues: List[ComplianceIssue] = []
    tables = extraction_result.get('tables', [])
    table_sources = extraction_result.get('table_sources', [])
    
    # Create a map of slide/page -> table sources for quick lookup
    source_map: Dict[Tuple[Optional[int], Optional[int]], Dict[str, Any]] = {}
    for source in table_sources:
        slide = source.get('slide_number')
        page = source.get('page_number')
        key = (slide, page)
        source_map[key] = source
    
    total_tables = len(tables)
    tables_with_source_date = 0
    
    for table in tables:
        slide_num = table.get('slide_number')
        page_num = table.get('page_number')
        table_idx = table.get('table_index', 0)
        
        location_key = (slide_num, page_num)
        source_info = source_map.get(location_key)
        
        location_str = format_location(slide_num, page_num, table_idx)
        
        if not source_info:
            # No source information found for this table
            issues.append(create_source_date_issue(
                issue_type_str="both_missing",
                location=location_str,
                message=f"Table at {location_str} is missing both source and date information",
                table_index=table_idx,
                slide_number=slide_num,
                page_number=page_num,
                severity="error",
                client_type=client_type,
                fund_type=fund_type
            ))
        else:
            source_name = source_info.get('source_name')
            source_date = source_info.get('source_date')
            
            has_source = bool(source_name and source_name.strip())
            has_date = bool(source_date and source_date.strip())
            
            if has_source and has_date:
                # Additional date validation if enabled
                if enable_date_validation:
                    date_validation = validate_date_format_and_recency(
                        source_date, source_info, location_str, slide_num, page_num, table_idx, metadata, max_date_age_days
                    )
                    if date_validation:
                        issues.extend(date_validation)
                    else:
                        tables_with_source_date += 1
                else:
                    tables_with_source_date += 1
            elif not has_source and not has_date:
                issues.append(create_source_date_issue(
                    issue_type_str="both_missing",
                    location=location_str,
                    message=f"Table at {location_str} is missing both source and date",
                    table_index=table_idx,
                    slide_number=slide_num,
                    page_number=page_num,
                    severity="error",
                    client_type=client_type,
                    fund_type=fund_type
                ))
            elif not has_source:
                issues.append(create_source_date_issue(
                    issue_type_str="missing_source",
                    location=location_str,
                    message=f"Table at {location_str} has date '{source_date}' but is missing source name",
                    table_index=table_idx,
                    slide_number=slide_num,
                    page_number=page_num,
                    severity="error",
                    client_type=client_type,
                    fund_type=fund_type
                ))
            elif not has_date:
                issues.append(create_source_date_issue(
                    issue_type_str="missing_date",
                    location=location_str,
                    message=f"Table at {location_str} has source '{source_name}' but is missing date",
                    table_index=table_idx,
                    slide_number=slide_num,
                    page_number=page_num,
                    severity="error",
                    client_type=client_type,
                    fund_type=fund_type
                ))
    
    # Also check performance sections for source/date
    performance_sections = extraction_result.get('performance_sections', [])
    for section in performance_sections:
        slide_num = section.get('slide_number')
        page_num = section.get('page_number')
        location_key = (slide_num, page_num)
        
        if location_key not in source_map:
            location_str = format_location(slide_num, page_num, None)
            issues.append(create_source_date_issue(
                issue_type_str="both_missing",
                location=location_str,
                message=f"Performance section at {location_str} may need source and date verification",
                slide_number=slide_num,
                page_number=page_num,
                severity="warning",
                client_type=client_type,
                fund_type=fund_type
            ))
    
    return {
        'issues': issues,
        'total_tables': total_tables,
        'tables_with_source_date': tables_with_source_date,
        'tables_missing_source_date': total_tables - tables_with_source_date
    }


def validate_date_format_and_recency(
    source_date: str,
    source_info: Dict[str, Any],
    location_str: str,
    slide_num: Optional[int],
    page_num: Optional[int],
    table_idx: Optional[int],
    metadata: Optional[Dict[str, Any]],
    max_date_age_days: int = 365
) -> List[ComplianceIssue]:
    """
    Validate date format and check if date is too old or inconsistent with document date.
    
    Returns:
        List of ComplianceIssue objects (empty if no issues)
    """
    issues: List[ComplianceIssue] = []
    
    # Try to parse the date
    parsed_date = None
    try:
        # Try common date formats
        date_str = source_date.strip()
        # Remove common prefixes
        date_str = re.sub(r'^(source|date|as of|as at)[:\s]+', '', date_str, flags=re.IGNORECASE)
        date_str = date_str.strip()
        
        # Try parsing with dateutil (handles many formats)
        parsed_date = date_parser.parse(date_str, dayfirst=True, yearfirst=False)
    except (ValueError, TypeError, AttributeError):
        issues.append(create_source_date_issue(
            issue_type_str="invalid_date_format",
            location=location_str,
            message=f"Table at {location_str} has invalid date format: '{source_date}'",
            table_index=table_idx,
            slide_number=slide_num,
            page_number=page_num,
            severity="error"
        ))
        return issues
    
    if parsed_date is None:
        return issues
    
    # Check if date is too old
    today = datetime.now().date()
    date_only = parsed_date.date() if hasattr(parsed_date, 'date') else parsed_date
    
    if isinstance(date_only, datetime):
        date_only = date_only.date()
    
    days_old = (today - date_only).days
    
    if days_old > max_date_age_days:
        issues.append(create_source_date_issue(
            issue_type_str="date_too_old",
            location=location_str,
            message=f"Table at {location_str} has source date {date_only} which is {days_old} days old (max: {max_date_age_days} days)",
            table_index=table_idx,
            slide_number=slide_num,
            page_number=page_num,
            severity="warning"
        ))
    
    # Check consistency with document date from metadata
    if metadata:
        doc_date_str = None
        title_info = metadata.get('title_information', {})
        if isinstance(title_info, dict):
            doc_date_str = title_info.get('document_date') or title_info.get('date')
        
        if not doc_date_str:
            # Try metadata directly
            doc_date_str = metadata.get('document_date') or metadata.get('date')
        
        if doc_date_str:
            try:
                doc_date = date_parser.parse(str(doc_date_str), dayfirst=True, yearfirst=False)
                doc_date_only = doc_date.date() if hasattr(doc_date, 'date') else doc_date
                
                if isinstance(doc_date_only, datetime):
                    doc_date_only = doc_date_only.date()
                
                # Source date should not be significantly after document date
                if date_only > doc_date_only:
                    days_diff = (date_only - doc_date_only).days
                    if days_diff > 30:  # Allow 30 days tolerance
                        issues.append(create_source_date_issue(
                            issue_type_str="date_inconsistent",
                            location=location_str,
                            message=f"Table at {location_str} has source date {date_only} which is {days_diff} days after document date {doc_date_only}",
                            table_index=table_idx,
                            slide_number=slide_num,
                            page_number=page_num,
                            severity="warning"
                        ))
            except (ValueError, TypeError, AttributeError):
                # Document date parsing failed, skip consistency check
                pass
    
    return issues

