"""
Chart Validation Module

Validates charts extracted by chart analyzer for source and date information.
"""

from typing import Dict, Any, List, Optional

from ...rules import ComplianceIssue
from .issue_factory import create_source_date_issue
from .utils import format_location
from .source_date_validator import validate_date_format_and_recency


def validate_charts(
    charts: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    enable_date_validation: bool = True,
    max_date_age_days: int = 365
) -> Dict[str, Any]:
    """
    Validate charts extracted by chart analyzer.
    
    Returns:
        Dict with validation results
    """
    issues: List[ComplianceIssue] = []
    total_charts = len(charts)
    charts_with_source_date = 0
    
    for chart in charts:
        slide_num = chart.get('slide_number')
        location_str = format_location(slide_num, None, None)
        source_info = chart.get('source_date_info', {})
        
        has_source = source_info.get('has_source', False)
        has_date = source_info.get('has_date', False)
        
        if has_source and has_date:
            # Validate date format if enabled
            if enable_date_validation:
                date_text = source_info.get('date_text')
                if date_text:
                    date_validation = validate_date_format_and_recency(
                        date_text, source_info, location_str, slide_num, None, None, metadata, max_date_age_days
                    )
                    if date_validation:
                        issues.extend(date_validation)
                    else:
                        charts_with_source_date += 1
                else:
                    charts_with_source_date += 1
            else:
                charts_with_source_date += 1
        elif not has_source and not has_date:
            issues.append(create_source_date_issue(
                issue_type_str="both_missing",
                location=f"Chart at {location_str}",
                message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} is missing both source and date information",
                slide_number=slide_num,
                severity="error"
            ))
        elif not has_source:
            issues.append(create_source_date_issue(
                issue_type_str="missing_source",
                location=f"Chart at {location_str}",
                message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} has date but is missing source name",
                slide_number=slide_num,
                severity="error"
            ))
        elif not has_date:
            issues.append(create_source_date_issue(
                issue_type_str="missing_date",
                location=f"Chart at {location_str}",
                message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} has source but is missing date",
                slide_number=slide_num,
                severity="error"
            ))
    
    return {
        'issues': issues,
        'total_charts': total_charts,
        'charts_with_source_date': charts_with_source_date,
        'charts_missing_source_date': total_charts - charts_with_source_date
    }

