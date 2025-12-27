from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Dict


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def _get_issue_category(issue_type: str) -> str:
    """
    Map issue type to category.
    
    Categories:
    - performance: Performance-related issues
    - structure: Document structure issues (cover page, slide 2, etc.)
    - disclaimer: Disclaimer-related issues
    - esg: ESG/SFDR compliance issues
    - registration: Country registration issues
    - source_date: Source/date validation issues
    - numerical: Numerical data validation issues
    - cross_reference: Cross-reference validation issues
    - compliance: General compliance issues (fallback)
    """
    issue_type_str = str(issue_type).lower()
    
    # Performance issues
    if any(keyword in issue_type_str for keyword in [
        'performance', 'benchmark', 'history', 'morningstar', 'backtest', 'simulation', 'track_record'
    ]):
        return "performance"
    
    # Source/date issues (Check before generic structure "missing_date")
    if any(keyword in issue_type_str for keyword in [
        'source_date', 'missing_source', 'missing_date_info', 'both_missing', 'date_too_old', 'date_inconsistent'
    ]):
        return "source_date"
        
    # Structure issues (cover page, slide 2, etc.)
    if any(keyword in issue_type_str for keyword in [
        'missing_fund_name', 'missing_date', 'missing_risk_profile',
        'missing_glossary', 'missing_target_audience', 'missing_promotional',
        'premarketing', 'starts_with', 'fund_characteristics'
    ]):
        return "structure"
    
    # Disclaimer issues
    if any(keyword in issue_type_str for keyword in [
        'disclaimer', 'warning', 'risk_warning', 'sri_disclaimer'
    ]):
        return "disclaimer"
    
    # ESG issues
    if any(keyword in issue_type_str for keyword in [
        'esg', 'sfdr', 'article_6', 'article_8', 'article_9'
    ]):
        return "esg"
    
    # Registration issues
    if 'registration' in issue_type_str or 'country' in issue_type_str:
        return "registration"
    
    # Numerical issues
    if 'numerical' in issue_type_str or 'mismatch' in issue_type_str or 'data_mismatch' in issue_type_str:
        return "numerical"
    
    # Cross-reference issues
    if 'cross_reference' in issue_type_str or 'reference' in issue_type_str:
        return "cross_reference"
    
    # Securities issues
    if any(keyword in issue_type_str for keyword in [
        'security', 'securities', 'investment_recommendation', 'buy_sell', 'valuation', 'projection', 'comparison'
    ]):
        return "securities"
    
    # Fund type specific issues
    if any(keyword in issue_type_str for keyword in [
        'ytm', 'ytw', 'irr', 'etf', 'private_equity', 'money_market', 'raif', 'dated_fund'
    ]):
        return "compliance"  # Fund type issues are compliance-related
    
    # Default to compliance
    return "compliance"


def format_validation_result(result: Any, metadata: Dict[str, Any], filename: str = None) -> Dict[str, Any]:
    """Format DataConsistencyResult into dashboard-friendly dict."""

    compliance_score = 100
    total_issues = len(result.compliance_issues)
    if total_issues > 0:
        # Decrease score based on severity
        severity_weights = {
            "error": 25,
            "critical": 25,
            "warning": 10,
            "high": 10,
            "medium": 5,
            "low": 2,
        }
        total_penalty = sum(severity_weights.get(i.severity, 0) for i in result.compliance_issues)
        compliance_score = max(0, 100 - total_penalty)

    # Descriptive status label
    if compliance_score == 100:
        compliance_status_label = "Totally compliant"
    elif compliance_score > 0:
        compliance_status_label = "Partially compliant"
    else:
        compliance_status_label = "Non-compliant"

    critical_count = sum(1 for i in result.compliance_issues if i.severity in ["critical", "error"])
    high_count = sum(1 for i in result.compliance_issues if i.severity in ["high", "warning"])
    medium_count = sum(1 for i in result.compliance_issues if i.severity == "medium")
    low_count = sum(1 for i in result.compliance_issues if i.severity == "low")

    # Group issues by category
    issues_by_category: Dict[str, Any] = {}
    category_counts: Dict[str, Any] = {}

    for issue in result.compliance_issues:
        # Use issue_category if set and not default "compliance", otherwise infer from issue_type
        category = issue.issue_category if (hasattr(issue, 'issue_category') and issue.issue_category and issue.issue_category != "compliance") else _get_issue_category(issue.issue_type)
        if category not in issues_by_category:
            issues_by_category[category] = []
            category_counts[category] = {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            }

        # Standardize severity for frontend
        severity = issue.severity
        if severity == "error":
            severity = "critical"
        elif severity == "warning":
            severity = "high"

        issues_by_category[category].append(
            {
                "issue_type": issue.issue_type,
                "severity": severity,
                "category": category,
                "location": issue.location,
                "slide_number": issue.slide_number,
                "message": issue.message,
                "context": issue.context,
                "suggestion": issue.suggestion,
                "auto_fixable": issue.auto_fixable,
                "rule_reference": issue.rule_reference,
            }
        )

        category_counts[category]["total"] += 1
        if issue.severity == "critical":
            category_counts[category]["critical"] += 1
        elif issue.severity == "error":
            category_counts[category]["critical"] += 1  # Errors are critical severity
        elif issue.severity == "high":
            category_counts[category]["high"] += 1
        elif issue.severity == "warning":
            category_counts[category]["high"] += 1  # Warnings count as high severity
        elif issue.severity == "medium":
            category_counts[category]["medium"] += 1
        else:
            category_counts[category]["low"] += 1

    # Build compliance_issues list with correct categories and standardized severities
    compliance_issues_with_category = []
    for issue in result.compliance_issues:
        category = issue.issue_category if issue.issue_category and issue.issue_category != "compliance" else _get_issue_category(issue.issue_type)
        
        severity = issue.severity
        if severity == "error":
            severity = "critical"
        elif severity == "warning":
            severity = "high"

        compliance_issues_with_category.append({
            "issue_type": issue.issue_type,
            "severity": severity,
            "category": category,
            "location": issue.location,
            "slide_number": issue.slide_number,
            "message": issue.message,
            "context": issue.context,
            "suggestion": issue.suggestion,
            "auto_fixable": issue.auto_fixable,
            "rule_reference": issue.rule_reference,
        })

    return {
        "document_id": result.document_id,
        "filename": filename,
        "overall_status": result.overall_status,
        "compliance_score": compliance_score,
        "compliance_status_label": compliance_status_label,
        "total_issues": total_issues,
        "compliance_issues": compliance_issues_with_category,
        "issues_by_severity": {
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
        },
        "issues_by_category": issues_by_category,
        "category_counts": category_counts,
        "statistics": {
            "total_tables_checked": result.total_tables_checked,
            "tables_with_source_date": result.tables_with_source_date,
            "tables_missing_source_date": result.tables_missing_source_date,
            "total_charts_analyzed": result.total_charts_analyzed,
            "charts_with_source_date": result.charts_with_source_date,
            "charts_missing_source_date": result.charts_missing_source_date,
            "total_numerical_values_checked": result.total_numerical_values_checked,
            "values_matching_reference": result.values_matching_reference,
        },
        "metadata": metadata,
        "summary": result.summary,
    }
