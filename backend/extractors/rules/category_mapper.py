"""
Issue Category Mapper

Maps issue types to their appropriate categories for proper organization.
"""

from .enums import ComplianceIssueType


def get_issue_category(issue_type: ComplianceIssueType) -> str:
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
    issue_type_str = issue_type.value if hasattr(issue_type, 'value') else str(issue_type)
    
    # Performance issues
    if any(keyword in issue_type_str for keyword in [
        'performance', 'benchmark', 'history', 'morningstar', 'backtest', 'simulation', 'track_record'
    ]):
        return "performance"
    
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
    
    # Source/date issues
    if 'source_date' in issue_type_str or 'missing_source' in issue_type_str:
        return "source_date"
    
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

