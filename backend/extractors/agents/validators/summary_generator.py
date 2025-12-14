"""
Summary Generator Module

Generates human-readable summaries of validation results.
"""

from typing import List
from ..models import DataConsistencyResult


def generate_summary(result: DataConsistencyResult) -> List[str]:
    """Generate human-readable summary of validation results."""
    summary = []
    
    # Group issues by category
    issues_by_category = {}
    for issue in result.compliance_issues:
        category = issue.issue_category
        if category not in issues_by_category:
            issues_by_category[category] = []
        issues_by_category[category].append(issue)
    
    # Source/Date summary
    if result.total_tables_checked > 0:
        summary.append(
            f"Source/Date Validation: {result.tables_with_source_date}/{result.total_tables_checked} "
            f"tables have complete source and date information"
        )
        if result.tables_missing_source_date > 0:
            summary.append(
                f"WARNING: {result.tables_missing_source_date} table(s) missing source/date information"
            )
        if 'source_date' in issues_by_category:
            error_count = sum(1 for issue in issues_by_category['source_date'] if issue.severity == "error")
            warning_count = len(issues_by_category['source_date']) - error_count
            if error_count > 0:
                summary.append(f"ERROR: {error_count} source/date error(s) found")
            if warning_count > 0:
                summary.append(f"WARNING: {warning_count} source/date warning(s) found")
    
    # Numerical validation summary
    if result.total_numerical_values_checked > 0:
        summary.append(
            f"Numerical Validation: {result.values_matching_reference}/{result.total_numerical_values_checked} "
            f"values match reference documents"
        )
        if result.values_with_inconsistencies > 0:
            summary.append(
                f"WARNING: {result.values_with_inconsistencies} value(s) have inconsistencies"
            )
        if 'numerical' in issues_by_category:
            error_count = sum(1 for issue in issues_by_category['numerical'] if issue.severity == "error")
            warning_count = len(issues_by_category['numerical']) - error_count
            if error_count > 0:
                summary.append(f"ERROR: {error_count} numerical inconsistency/ies")
            if warning_count > 0:
                summary.append(f"WARNING: {warning_count} numerical warning(s)")
    
    # Cross-reference validation summary
    if 'cross_reference' in issues_by_category:
        error_count = sum(1 for issue in issues_by_category['cross_reference'] if issue.severity == "error")
        warning_count = len(issues_by_category['cross_reference']) - error_count
        if error_count > 0:
            summary.append(f"ERROR: {error_count} cross-reference error(s) found")
        if warning_count > 0:
            summary.append(f"WARNING: {warning_count} cross-reference warning(s) found")
    
    # ESG validation summary
    if 'esg' in issues_by_category:
        critical_count = sum(1 for issue in issues_by_category['esg'] if issue.severity == "critical")
        error_count = sum(1 for issue in issues_by_category['esg'] if issue.severity == "error")
        warning_count = len(issues_by_category['esg']) - critical_count - error_count
        if critical_count > 0:
            summary.append(f"CRITICAL: {critical_count} ESG compliance issue(s)")
        if error_count > 0:
            summary.append(f"ERROR: {error_count} ESG error(s)")
        if warning_count > 0:
            summary.append(f"WARNING: {warning_count} ESG warning(s)")
    
    # Other compliance issues
    other_categories = [cat for cat in issues_by_category if cat not in ['source_date', 'numerical', 'cross_reference', 'esg']]
    if other_categories:
        for category in other_categories:
            issues = issues_by_category[category]
            critical_count = sum(1 for issue in issues if issue.severity == "critical")
            error_count = sum(1 for issue in issues if issue.severity == "error")
            warning_count = len(issues) - critical_count - error_count
            if critical_count > 0:
                summary.append(f"CRITICAL: {critical_count} {category} issue(s)")
            if error_count > 0:
                summary.append(f"ERROR: {error_count} {category} error(s)")
            if warning_count > 0:
                summary.append(f"WARNING: {warning_count} {category} warning(s)")

    # Overall status
    if result.overall_status == "pass":
        summary.append("PASS: All validations passed")
    elif result.overall_status == "warning":
        summary.append("WARNING: Validation completed with warnings")
    elif result.overall_status == "critical":
        summary.append("CRITICAL: Validation found critical compliance violations")
    elif result.overall_status == "error":
        summary.append("ERROR: Validation found errors that require attention")
    
    return summary

