"""
Pydantic models for structured feature extraction
Defines the structure of extracted content features
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date


class ESGFeature(BaseModel):
    # Model li yrepresenti mention ESG: text, context, article SFDR, location, confidence
    """ESG-related mention"""
    text: str = Field(description="The actual ESG mention or keyword")
    context: str = Field(description="Surrounding context of the mention")
    sfdr_article: Optional[str] = Field(None, description="SFDR article if mentioned (Article 6, 8, or 9)")
    location: str = Field(description="Location in document (page/slide number)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")


class PerformanceFeature(BaseModel):
    # Model li yrepresenti mention ta3 performance (dates, percentage, is_past/is_forecast)
    """Performance data mention"""
    text: str = Field(description="The performance data text")
    date_range: Optional[str] = Field(None, description="Date range if present (e.g., '2020-2024')")
    percentage: Optional[float] = Field(None, description="Percentage value if present")
    is_past_performance: bool = Field(description="Whether this is past performance data")
    is_forecast: bool = Field(description="Whether this is a forecast/simulation")
    location: str = Field(description="Location in document (page/slide number)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")


class CountryFeature(BaseModel):
    # Model li yrepresenti mention ta3 country (name, context, location, confidence)
    """Country mention"""
    country_name: str = Field(description="Name of the country")
    context: str = Field(description="Context of the mention (e.g., 'available in', 'registered in')")
    location: str = Field(description="Location in document (page/slide number)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")


class CompanyFeature(BaseModel):
    # Model li yrepresenti mention ta3 company/issuer
    """Company/issuer mention"""
    company_name: str = Field(description="Name of the company/issuer")
    context: str = Field(description="Context of the mention")
    location: str = Field(description="Location in document (page/slide number)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")


class FinancialTermFeature(BaseModel):
    # Model li yrepresenti mention ta3 financial term (YtM, etc.)
    """Financial term mention"""
    term: str = Field(description="Financial term (e.g., 'YtM', 'Yield to Maturity')")
    full_text: str = Field(description="Full text where term appears")
    location: str = Field(description="Location in document (page/slide number)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")


class ContentFeatures(BaseModel):
    # Container model li yjma3 kol types mta3 features men document
    """Complete content features extracted from document"""
    esg_mentions: List[ESGFeature] = Field(default_factory=list, description="List of ESG mentions")
    performance_data: List[PerformanceFeature] = Field(default_factory=list, description="List of performance data")
    country_mentions: List[CountryFeature] = Field(default_factory=list, description="List of country mentions")
    company_mentions: List[CompanyFeature] = Field(default_factory=list, description="List of company/issuer mentions")
    financial_terms: List[FinancialTermFeature] = Field(default_factory=list, description="List of financial terms")
    
    # Keep example schema small to avoid large inline literals; expand only if needed.
    model_config = ConfigDict(json_schema_extra={})

