"""
Slide 2 Compliance Rules

Section 3 - Slide 2 Rules (after cover page).
"""

from dataclasses import dataclass


@dataclass
class Slide2Rules:
    """Section 3 - Slide 2 Rules (after cover page)"""
    
    # Required elements
    MUST_INCLUDE_STANDARD_DISCLAIMER: bool = True
    MUST_ADAPT_FUND_NAME_IN_DISCLAIMER: bool = True
    MUST_ADAPT_ELIGIBLE_CLIENTS: bool = True
    
    # Risk profile
    MUST_INCLUDE_COMPLETE_RISK_PROFILE: bool = True
    RISK_PROFILE_MUST_MATCH_PROSPECTUS: bool = True
    
    # Marketing countries
    MUST_INCLUDE_MARKETING_COUNTRIES: bool = True
    COUNTRIES_MUST_MATCH_REGISTRATION_ABROAD: bool = True

