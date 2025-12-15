"""
Registration Validator

Validates country mentions against registration data.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime

from .models import FundRegistration
from .detector import detect_country_mentions


def find_registration(
    fund_name: str,
    registrations: Dict[str, FundRegistration]
) -> Optional[FundRegistration]:
    """Find registration by fund name with flexible matching"""
    # Try exact match first
    if fund_name in registrations:
        return registrations[fund_name]
    
    # Try case-insensitive match
    fund_name_lower = fund_name.lower()
    for key, reg in registrations.items():
        if key.lower() == fund_name_lower:
            return reg
    
    # Try partial match
    for key, reg in registrations.items():
        if fund_name_lower in key.lower() or key.lower() in fund_name_lower:
            return reg
    
    return None


def is_registered(
    fund_name: str,
    country: str,
    registrations: Dict[str, FundRegistration],
    share_class: Optional[str] = None,
    isin: Optional[str] = None
) -> bool:
    """
    Check if a fund is registered in a specific country.
    
    Args:
        fund_name: Name of the fund
        country: Country name to check
        registrations: Dictionary of fund registrations
        share_class: Optional share class identifier
        isin: Optional ISIN code
    
    Returns:
        True if registered, False otherwise
    """
    # Try to find registration by various keys
    keys_to_try = []
    
    if share_class:
        keys_to_try.append(f"{fund_name}|{share_class}")
    if isin:
        keys_to_try.append(f"{fund_name}|{isin}")
    keys_to_try.append(fund_name)
    
    for key in keys_to_try:
        if key in registrations:
            reg = registrations[key]
            # Check exact match first
            if country in reg.registered_countries:
                return True
            # Check case-insensitive match
            country_lower = country.lower()
            for reg_country in reg.registered_countries:
                if reg_country.lower() == country_lower:
                    return True
    
    return False


def get_registered_countries(
    fund_name: str,
    registrations: Dict[str, FundRegistration],
    share_class: Optional[str] = None,
    isin: Optional[str] = None
) -> Set[str]:
    """
    Get all countries where a fund is registered.
    
    Args:
        fund_name: Name of the fund
        registrations: Dictionary of fund registrations
        share_class: Optional share class identifier
        isin: Optional ISIN code
    
    Returns:
        Set of registered country names
    """
    keys_to_try = []
    
    if share_class:
        keys_to_try.append(f"{fund_name}|{share_class}")
    if isin:
        keys_to_try.append(f"{fund_name}|{isin}")
    keys_to_try.append(fund_name)
    
    for key in keys_to_try:
        if key in registrations:
            return registrations[key].registered_countries.copy()
    
    return set()


def validate_temporal(
    fund_name: str,
    country: str,
    registrations: Dict[str, FundRegistration],
    validation_date: Optional[datetime] = None,
    enable_temporal_validation: bool = True
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate registration temporal constraints.
    
    Args:
        fund_name: Fund name to check
        country: Country to validate
        registrations: Dictionary of fund registrations
        validation_date: Date to validate against (defaults to today)
        enable_temporal_validation: Whether temporal validation is enabled
        
    Returns:
        Tuple of (is_valid, severity, message)
    """
    if not enable_temporal_validation:
        return True, None, None
    
    validation_date = validation_date or datetime.now()
    
    # Find registration
    registration = find_registration(fund_name, registrations)
    if not registration:
        return False, "CRITICAL", f"Fund '{fund_name}' not found in registration database"
    
    # Check if registered in country
    if country not in registration.registered_countries:
        return False, "CRITICAL", f"Fund not registered in {country}"
    
    # Check registration date
    if country in registration.registration_dates:
        reg_date_str = registration.registration_dates[country]
        if reg_date_str:
            try:
                reg_date = datetime.strptime(reg_date_str, '%Y-%m-%d')
                if validation_date < reg_date:
                    return False, "HIGH", f"Registration in {country} not yet effective (starts {reg_date_str})"
            except ValueError:
                pass  # Skip invalid dates
    
    # Check expiry date
    if country in registration.expiry_dates:
        expiry_date_str = registration.expiry_dates[country]
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
                if validation_date > expiry_date:
                    return False, "CRITICAL", f"Registration in {country} expired on {expiry_date_str}"
                
                # Warn if expiring soon (within 90 days)
                days_until_expiry = (expiry_date - validation_date).days
                if days_until_expiry <= 90:
                    return True, "MEDIUM", f"Registration in {country} expiring soon ({days_until_expiry} days, on {expiry_date_str})"
            except ValueError:
                pass  # Skip invalid dates
    
    return True, None, None


def validate_country_mentions(
    mentioned_countries: List[str],
    fund_name: str,
    registrations: Dict[str, FundRegistration],
    share_class: Optional[str] = None,
    isin: Optional[str] = None
) -> Dict[str, bool]:
    """
    Validate that mentioned countries are registered.
    
    Args:
        mentioned_countries: List of country names mentioned in document
        fund_name: Name of the fund
        registrations: Dictionary of fund registrations
        share_class: Optional share class identifier
        isin: Optional ISIN code
    
    Returns:
        Dictionary mapping country names to registration status (True/False)
    """
    registered = get_registered_countries(fund_name, registrations, share_class, isin)
    registered_lower = {c.lower() for c in registered}
    
    validation = {}
    for country in mentioned_countries:
        country_lower = country.lower()
        # Check exact match
        is_registered_val = country in registered or country_lower in registered_lower
        validation[country] = is_registered_val
    
    return validation


def validate_document(
    document_text: str,
    fund_name: str,
    registrations: Dict[str, FundRegistration],
    share_class: Optional[str] = None,
    isin: Optional[str] = None,
    document_date: Optional[datetime] = None,
    enable_context_awareness: bool = True,
    enable_temporal_validation: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive document validation with context awareness and temporal checks.
    
    Args:
        document_text: Full document text to analyze
        fund_name: Fund name
        registrations: Dictionary of fund registrations
        share_class: Optional share class
        isin: Optional ISIN
        document_date: Document date for temporal validation
        enable_context_awareness: Whether to use context-aware detection
        enable_temporal_validation: Whether to validate temporal constraints
        
    Returns:
        Dictionary with validation results, issues, and recommendations
    """
    # Detect all country mentions with context
    all_mentions = detect_country_mentions(
        document_text,
        enable_context_awareness=enable_context_awareness
    )
    
    # Filter for distribution claims only (if context awareness enabled)
    distribution_mentions = [m for m in all_mentions if m.is_distribution_claim]
    
    # Get unique countries from distribution claims
    distribution_countries = list(set(m.country for m in distribution_mentions))
    
    issues = []
    warnings = []
    
    for mention in distribution_mentions:
        country = mention.country
        
        # Check registration status
        is_registered_val = is_registered(fund_name, country, registrations, share_class, isin)
        
        if not is_registered_val:
            issues.append({
                "severity": "CRITICAL",
                "country": country,
                "message": f"Fund not registered for distribution in {country}",
                "context": mention.context,
                "position": mention.position,
                "raw_text": mention.raw_text
            })
        else:
            # Check temporal validity
            if enable_temporal_validation and document_date:
                is_valid, severity, message = validate_temporal(
                    fund_name, country, registrations, document_date, enable_temporal_validation
                )
                
                if not is_valid or severity:
                    target = issues if not is_valid else warnings
                    target.append({
                        "severity": severity,
                        "country": country,
                        "message": message,
                        "context": mention.context,
                        "position": mention.position,
                        "raw_text": mention.raw_text
                    })
    
    # Generate summary
    summary = {
        "total_country_mentions": len(all_mentions),
        "distribution_claims": len(distribution_mentions),
        "unique_countries_mentioned": len(set(m.country for m in all_mentions)),
        "unique_distribution_countries": len(distribution_countries),
        "critical_issues": len([i for i in issues if i["severity"] == "CRITICAL"]),
        "warnings_count": len(warnings),
        "all_mentions": [
            {
                "country": m.country,
                "is_distribution_claim": m.is_distribution_claim,
                "context": m.context[:100] + "..." if len(m.context) > 100 else m.context,
                "position": m.position
            }
            for m in all_mentions
        ],
        "issues": issues,
        "warnings": warnings
    }
    
    return summary

