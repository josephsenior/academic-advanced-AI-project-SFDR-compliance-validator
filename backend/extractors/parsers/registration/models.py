"""
Registration Parser Models

Pydantic models for registration data.
"""

from pydantic import BaseModel, Field
from typing import Set, Dict, Optional


class CountryMention(BaseModel):
    """Represents a detected country mention with context"""
    country: str = Field(description="Standardized country name")
    raw_text: str = Field(description="Original text matched")
    context: str = Field(description="Surrounding text for context")
    position: int = Field(description="Character position in document")
    is_distribution_claim: bool = Field(description="Whether this is a distribution/availability claim")
    confidence: float = Field(default=1.0, description="Detection confidence (0-1)")
    location: Optional[str] = Field(None, description="Document location (slide, section)")


class FundRegistration(BaseModel):
    """Represents fund registration information with temporal data"""
    fund_name: str
    share_class: Optional[str] = None
    isin: Optional[str] = None
    registered_countries: Set[str] = Field(default_factory=set)
    registration_details: Dict[str, str] = Field(default_factory=dict)
    registration_dates: Dict[str, Optional[str]] = Field(default_factory=dict)
    expiry_dates: Dict[str, Optional[str]] = Field(default_factory=dict)

