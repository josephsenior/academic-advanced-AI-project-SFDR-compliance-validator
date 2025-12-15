"""
Data models for data consistency validation
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from ..rules import ComplianceIssue


class DataConsistencyResult(BaseModel):
    """Complete result of data consistency validation"""
    document_id: Optional[str] = Field(None, description="Document identifier")
    validation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
    
    # Unified compliance issues array (includes all types: source/date, numerical, cross-reference, compliance)
    compliance_issues: List[ComplianceIssue] = Field(default_factory=list, description="All validation issues unified")
    
    # Summary statistics
    total_tables_checked: int = Field(default=0, description="Total tables/charts checked for source/date")
    tables_with_source_date: int = Field(default=0, description="Tables with complete source/date")
    tables_missing_source_date: int = Field(default=0, description="Tables missing source/date")
    total_numerical_values_checked: int = Field(default=0, description="Total numerical values validated against reference")
    values_matching_reference: int = Field(default=0, description="Values matching reference documents")
    values_with_inconsistencies: int = Field(default=0, description="Values with inconsistencies")
    total_charts_analyzed: int = Field(default=0, description="Total charts analyzed")
    charts_with_source_date: int = Field(default=0, description="Charts with source/date")
    charts_missing_source_date: int = Field(default=0, description="Charts missing source/date")
    countries_checked: List[str] = Field(default_factory=list, description="Countries checked for registration")
    countries_authorized: List[str] = Field(default_factory=list, description="Countries authorized for distribution")
    countries_unauthorized: List[str] = Field(default_factory=list, description="Countries mentioned but not authorized")
    
    # Disclaimer validation results (optional)
    disclaimer_validation: Optional[Dict[str, Any]] = Field(default=None, description="Disclaimer validation results if enabled")
    
    # ESG validation results (optional enrichment data)
    esg_analysis: Optional[Dict[str, Any]] = Field(default=None, description="ESG/SFDR analysis metadata if ESG validation is enabled")
    
    # Overall status
    has_errors: bool = Field(default=False)
    has_warnings: bool = Field(default=False)
    overall_status: str = Field(default="unknown", description="'pass', 'warning', 'error', 'critical'")
    
    # Summary messages
    summary: List[str] = Field(default_factory=list)

    # Legacy/compatibility fields used by older code/tests
    source_date_issues: List[Any] = Field(default_factory=list)
    numerical_inconsistencies: List[Any] = Field(default_factory=list)
    cross_reference_issues: List[Any] = Field(default_factory=list)

    @property
    def issues(self) -> List[ComplianceIssue]:
        return self.compliance_issues

    @property
    def violations(self) -> List[ComplianceIssue]:
        return self.compliance_issues

    @property
    def numerical_issues(self) -> List[Any]:
        """Backward-compatible alias used in some tests/examples."""
        return self.numerical_inconsistencies

    @property
    def cross_references(self) -> List[Any]:
        """Backward-compatible alias for cross-reference issues."""
        return self.cross_reference_issues

