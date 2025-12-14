"""
Content Compliance Rules

Section 4 - Content Rules for following pages.
"""

from dataclasses import dataclass


@dataclass
class ContentRules:
    """Section 4 - Content Rules for following pages"""
    
    # Document cannot start with performance
    CANNOT_START_WITH_PERFORMANCE: bool = True
    MUST_START_WITH_FUND_PRESENTATION: bool = True
    
    # Morningstar rating requirements
    MORNINGSTAR_REQUIRES_DATE: bool = True
    MORNINGSTAR_REQUIRES_CATEGORY: bool = True
    
    # Portfolio lines
    PORTFOLIO_LINES_MUST_BE_IN_PROSPECTUS: bool = True
    
    # End of presentation
    MUST_INCLUDE_FUND_CHARACTERISTICS: bool = True
    
    # Data consistency
    DATA_MUST_MATCH_LEGAL_DOCS: bool = True  # KID, Prospectus, SFDR Annex
    
    # Validation responsibility
    MUST_INDICATE_VALIDATION_RESPONSIBLE: bool = True
    
    # Management team
    TEAM_MAY_CHANGE_DISCLAIMER_REQUIRED: bool = True
    TEAM_DISCLAIMER_PHRASES = [
        "L'équipe est susceptible de changer",
        "The team is subject to change",
        "Das Team kann sich ändern",
        "The management team may change"
    ]

