"""
Compliance Rules Models

Pydantic models for compliance validation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .enums import ClientType, FundType, ComplianceIssueType


class ComplianceIssue(BaseModel):
    """A single compliance issue found during validation"""
    
    issue_type: ComplianceIssueType = Field(description="Type of compliance issue")
    issue_category: str = Field(default="compliance", description="Category: 'source_date', 'numerical', 'esg', 'structure', 'registration', 'disclaimer', 'performance', 'cross_reference', 'compliance'")
    rule_reference: str = Field(description="Reference to rule in source document (e.g., 'Section 4.3')")
    location: str = Field(description="Location in document (slide/page)")
    slide_number: Optional[int] = Field(default=None, description="Slide number if applicable")
    page_number: Optional[int] = Field(default=None, description="Page number if applicable")
    table_index: Optional[int] = Field(default=None, description="Table index if applicable")
    chart_index: Optional[int] = Field(default=None, description="Chart index if applicable")
    severity: str = Field(default="error", description="'error', 'warning', or 'critical'")
    message: str = Field(description="Human-readable description")
    context: Optional[str] = Field(default=None, description="Relevant text context")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix")
    auto_fixable: bool = Field(default=False, description="Whether this issue can be auto-fixed")
    
    # Additional context
    client_type: Optional[ClientType] = Field(default=None, description="Client type if relevant")
    country: Optional[str] = Field(default=None, description="Country if relevant")
    fund_type: Optional[FundType] = Field(default=None, description="Fund type if relevant")
    
    # Extended data for specific issue types
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional structured data (e.g., numerical values, ESG excerpts, performance data)")


class ValidationResult(BaseModel):
    """Result of a full validation run"""
    status: str = Field(description="'compliant', 'non_compliant', 'warning'")
    issues: List[ComplianceIssue] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
