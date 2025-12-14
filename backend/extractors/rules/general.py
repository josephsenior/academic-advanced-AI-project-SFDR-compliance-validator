"""
General Compliance Rules

Section 1 - General Rules applicable to all documents.
"""

from dataclasses import dataclass


@dataclass
class GeneralRules:
    """Section 1 - General Rules"""
    
    # Disclaimer requirements
    RETAIL_REQUIRES_RETAIL_DISCLAIMERS: bool = True
    PROFESSIONAL_REQUIRES_PROFESSIONAL_DISCLAIMERS: bool = True
    
    # Source and date requirements
    ALL_DATA_CHARTS_REQUIRE_SOURCE_AND_DATE: bool = True
    SOURCE_MUST_BE_IN_FOOTNOTE: bool = True
    
    # SRI requirements
    SRI_MUST_BE_ON_SAME_SLIDE_AS_DISCLAIMER: bool = True
    
    # Glossary requirements for retail
    RETAIL_REQUIRES_GLOSSARY: bool = True
    GLOSSARY_TERMS_MUST_BE_IN_DOCUMENT: bool = True
    
    # Risk warning formatting
    RISK_WARNINGS_MUST_BE_BOLD: bool = True
    RISK_WARNINGS_SAME_FONT_AS_MAIN: bool = True
    RISK_WARNINGS_MUST_BE_VISIBLE: bool = True  # Not in footnotes
    
    # Opinion attenuation
    OPINIONS_MUST_BE_ATTENUATED: bool = True
    ATTENUATION_PHRASES = [
        "selon notre opinion",
        "selon nos analyses", 
        "le fonds a pour objectif de",
        "according to our opinion",
        "according to our analysis",
        "the fund aims to",
        "in our view",
        "we believe",
        "in unserer Einschätzung",
        "unserer Meinung nach"
    ]
    
    # Strategy must match legal docs
    STRATEGY_MUST_MATCH_LEGAL_DOCS: bool = True
    
    # Registration abroad compliance
    MARKETING_COUNTRIES_MUST_MATCH_REGISTRATION: bool = True
    
    # Internal limits prohibition
    INTERNAL_LIMITS_PROHIBITED: bool = True
    
    # Anglicisms in retail
    RETAIL_AVOID_ANGLICISMS: bool = True
    ANGLICISMS_MUST_BE_DEFINED: bool = True
    
    # Strategy vs Fund confusion
    NO_STRATEGY_FUND_CONFUSION: bool = True

