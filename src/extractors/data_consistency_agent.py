"""
Data Consistency Agent

Verifies that numerical data, sources, and charts match official documents (Prospectus, KID, SFDR).
Based on: Word rules ('All data, charts, and figures must include source and date').

Tasks:
- Check that each chart includes source + date
- Validate numbers against the prospectus or SFDR annex
- Flag inconsistencies
"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from pathlib import Path
import re
import logging
from datetime import datetime, date
from dateutil import parser as date_parser

from src.extractors.compliance_rules import (
    ComplianceIssue,
    ComplianceIssueType,
    PerformanceRules,
    ClientType,
    FundType,
    GeneralRules
)

# Import ESG analysis components
try:
    from src.extractors.esg_compliance_agent import ESGAnalyzer, ESGLevel, ESGMentions, ESGViolation
    ESG_AVAILABLE = True
except ImportError:
    ESG_AVAILABLE = False
    logger.warning("⚠️ ESG Compliance Agent not available")

# Import utility modules
try:
    from src.utils.reference_data_manager import ReferenceDataManager
    from src.utils.metrics import get_metrics_collector
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    logger.warning("⚠️ Utility modules (reference_data_manager, metrics) not available")

# Setup logger
logger = logging.getLogger(__name__)




class DataConsistencyResult(BaseModel):
    """Complete result of data consistency validation"""
    document_id: Optional[str] = Field(None, description="Document identifier")
    validation_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
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
    disclaimer_validation: Optional[Dict[str, Any]] = Field(None, description="Disclaimer validation results if enabled")
    
    # ESG validation results (optional enrichment data)
    esg_analysis: Optional[Dict[str, Any]] = Field(None, description="ESG/SFDR analysis metadata if ESG validation is enabled")
    
    # Overall status
    has_errors: bool = Field(default=False)
    has_warnings: bool = Field(default=False)
    overall_status: str = Field(default="unknown", description="'pass', 'warning', 'error', 'critical'")
    
    # Summary messages
    summary: List[str] = Field(default_factory=list)


class ReferenceData(BaseModel):
    """Reference data from official documents (Prospectus, KID, SFDR)"""
    fund_name: Optional[str] = None
    isin: Optional[str] = None
    
    # Performance data by period and basis
    performance_data: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Nested dict: {period: {basis: value}}, e.g., {'1Y': {'net': 10.5}}"
    )
    
    # Table data (keyed by label/description)
    table_data: Dict[str, float] = Field(
        default_factory=dict,
        description="Key-value pairs of table entries from reference documents"
    )
    
    # Metadata
    reference_date: Optional[str] = None
    source_document: Optional[str] = Field(None, description="e.g., 'Prospectus', 'KID', 'SFDR Annex'")


class DataConsistencyAgent:
    """
    Agent that verifies data consistency in marketing documents.
    
    Validates:
    1. All charts/tables have source + date
    2. Numerical data matches reference documents (Prospectus, KID, SFDR)
    3. Flags inconsistencies for review
    """
    
    def __init__(
        self,
        reference_data: Optional[ReferenceData] = None,
        max_date_age_days: int = 365,
        enable_cross_reference: bool = True,
        enable_date_validation: bool = True,
        enable_disclaimer_validation: bool = False,
        disclaimer_validator: Optional[Any] = None,
        enable_esg_validation: bool = False,
        esg_api_key: Optional[str] = None,
        esg_base_url: Optional[str] = None
    ):
        """
        Initialize the Data Consistency Agent.
        
        Args:
            reference_data: Optional reference data from official documents.
                          If None, numerical validation will be skipped.
            max_date_age_days: Maximum age in days for source dates (default: 365)
            enable_cross_reference: Enable cross-reference validation (default: True)
            enable_date_validation: Enable date format and recency validation (default: True)
            enable_disclaimer_validation: Enable disclaimer validation (default: False)
            disclaimer_validator: Optional DisclaimerValidator instance
            enable_esg_validation: Enable ESG/SFDR compliance validation (default: False)
            esg_api_key: OpenAI API key for ESG validation (required if enable_esg_validation=True)
            esg_base_url: OpenAI API base URL for ESG validation (required if enable_esg_validation=True)
        """
        self.reference_data = reference_data
        self.default_tolerance = 0.01  # 1% tolerance for numerical comparisons
        self.max_date_age_days = max_date_age_days
        self.enable_cross_reference = enable_cross_reference
        self.enable_date_validation = enable_date_validation
        self.enable_disclaimer_validation = enable_disclaimer_validation
        self.disclaimer_validator = disclaimer_validator
        self.enable_esg_validation = enable_esg_validation and ESG_AVAILABLE
        
        # Initialize utility modules
        self.ref_manager = ReferenceDataManager() if UTILS_AVAILABLE else None
        self.metrics = get_metrics_collector() if UTILS_AVAILABLE else None
        
        # Initialize ESG Analyzer (integrated directly, no separate agent)
        self.esg_analyzer = None
        
        if self.enable_esg_validation:
            if not esg_api_key or not esg_base_url:
                raise ValueError("ESG validation enabled but esg_api_key or esg_base_url not provided")
            
            try:
                self.esg_analyzer = ESGAnalyzer(
                    api_key=esg_api_key,
                    base_url=esg_base_url
                )
                logger.info("✅ ESG Analyzer initialized successfully (integrated mode)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ESG Analyzer: {e}")
                self.esg_analyzer = None
                self.enable_esg_validation = False
    
    def _create_source_date_issue(
        self,
        issue_type_str: str,
        location: str,
        message: str,
        table_index: Optional[int] = None,
        slide_number: Optional[int] = None,
        page_number: Optional[int] = None,
        severity: str = "error",
        client_type: Optional[ClientType] = None,
        fund_type: Optional[FundType] = None
    ) -> ComplianceIssue:
        """Helper to create source/date ComplianceIssue"""
        # Map old issue type strings to new enum values
        issue_type_map = {
            "missing_source": ComplianceIssueType.MISSING_SOURCE,
            "missing_date": ComplianceIssueType.MISSING_DATE_INFO,
            "both_missing": ComplianceIssueType.BOTH_MISSING,
            "date_too_old": ComplianceIssueType.DATE_TOO_OLD,
            "invalid_date_format": ComplianceIssueType.INVALID_DATE_FORMAT,
            "date_inconsistent": ComplianceIssueType.DATE_INCONSISTENT,
        }
        
        issue_type = issue_type_map.get(issue_type_str, ComplianceIssueType.MISSING_SOURCE_DATE)
        
        # Extract slide number from location if not provided
        if slide_number is None and "slide" in location.lower():
            match = re.search(r'slide\s+(\d+)', location, re.IGNORECASE)
            if match:
                slide_number = int(match.group(1))
        
        return ComplianceIssue(
            issue_type=issue_type,
            issue_category="source_date",
            rule_reference="Section 1 - Source and Date Requirements",
            location=location,
            slide_number=slide_number,
            page_number=page_number,
            table_index=table_index,
            severity=severity,
            message=message,
            context=None,
            suggestion="Add source and date information to this table/chart",
            client_type=client_type,
            fund_type=fund_type
        )
    
    def _create_numerical_issue(
        self,
        location: str,
        message: str,
        document_value: float,
        reference_value: Optional[float] = None,
        reference_source: Optional[str] = None,
        period: Optional[str] = None,
        basis: Optional[str] = None,
        label: Optional[str] = None,
        tolerance: Optional[float] = None,
        severity: str = "error",
        client_type: Optional[ClientType] = None,
        fund_type: Optional[FundType] = None
    ) -> ComplianceIssue:
        """Helper to create numerical validation ComplianceIssue"""
        # Extract slide number from location
        slide_number = None
        if "slide" in location.lower():
            match = re.search(r'slide\s+(\d+)', location, re.IGNORECASE)
            if match:
                slide_number = int(match.group(1))
        
        # Build context string
        context_parts = []
        if label:
            context_parts.append(f"Label: {label}")
        if period:
            context_parts.append(f"Period: {period}")
        if basis:
            context_parts.append(f"Basis: {basis}")
        context_parts.append(f"Document value: {document_value}")
        if reference_value is not None:
            context_parts.append(f"Reference value: {reference_value}")
            diff = abs(document_value - reference_value)
            context_parts.append(f"Difference: {diff}")
        
        context = " | ".join(context_parts)
        
        # Build suggestion
        if reference_value is not None:
            suggestion = f"Update value to match reference: {reference_value}"
        else:
            suggestion = "Verify this value against official reference documents (Prospectus, KID, SFDR)"
        
        # Build details dict
        details = {
            "document_value": document_value,
            "reference_value": reference_value,
            "reference_source": reference_source,
            "period": period,
            "basis": basis,
            "label": label,
            "tolerance": tolerance
        }
        
        return ComplianceIssue(
            issue_type=ComplianceIssueType.NUMERICAL_MISMATCH,
            issue_category="numerical",
            rule_reference="Section 1 - Numerical Consistency",
            location=location,
            slide_number=slide_number,
            severity=severity,
            message=message,
            context=context,
            suggestion=suggestion,
            client_type=client_type,
            fund_type=fund_type,
            details=details
        )
    
    def _create_cross_reference_issue(
        self,
        issue_type_str: str,
        location: str,
        message: str,
        value1: Optional[float] = None,
        value2: Optional[float] = None,
        location1: Optional[str] = None,
        location2: Optional[str] = None,
        period: Optional[str] = None,
        severity: str = "error",
        client_type: Optional[ClientType] = None,
        fund_type: Optional[FundType] = None
    ) -> ComplianceIssue:
        """Helper to create cross-reference ComplianceIssue"""
        issue_type_map = {
            "performance_mismatch": ComplianceIssueType.PERFORMANCE_MISMATCH,
            "duplicate_inconsistency": ComplianceIssueType.DUPLICATE_INCONSISTENCY,
        }
        
        issue_type = issue_type_map.get(issue_type_str, ComplianceIssueType.PERFORMANCE_MISMATCH)
        
        # Extract slide number
        slide_number = None
        if "slide" in location.lower():
            match = re.search(r'slide\s+(\d+)', location, re.IGNORECASE)
            if match:
                slide_number = int(match.group(1))
        
        # Build context
        context_parts = []
        if value1 is not None:
            context_parts.append(f"Value 1: {value1} at {location1 or 'unknown'}")
        if value2 is not None:
            context_parts.append(f"Value 2: {value2} at {location2 or 'unknown'}")
        if period:
            context_parts.append(f"Period: {period}")
        if value1 is not None and value2 is not None:
            diff = abs(value1 - value2)
            context_parts.append(f"Difference: {diff}")
        
        context = " | ".join(context_parts) if context_parts else None
        
        # Build details
        details = {
            "value1": value1,
            "value2": value2,
            "location1": location1,
            "location2": location2,
            "period": period
        }
        
        return ComplianceIssue(
            issue_type=issue_type,
            issue_category="cross_reference",
            rule_reference="Section 1 - Cross-Reference Consistency",
            location=location,
            slide_number=slide_number,
            severity=severity,
            message=message,
            context=context,
            suggestion="Verify these values match across all references in the document",
            client_type=client_type,
            fund_type=fund_type,
            details=details
        )
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> DataConsistencyResult:
        """
        Perform complete data consistency validation on extraction results.
        
        Args:
            extraction_result: Output from DocumentExtractor.extract()
            metadata: Optional metadata dict (for document identification)
            document_id: Optional document identifier
            
        Returns:
            DataConsistencyResult with all validation findings
        """
        result = DataConsistencyResult(document_id=document_id)
        
        # Load reference data if available
        if self.ref_manager and metadata:
            fund_name = metadata.get('fund_name') or metadata.get('fund_full_name')
            if fund_name:
                try:
                    loaded_ref_data = self.ref_manager.load_reference_data_for_fund(fund_name)
                    if loaded_ref_data:
                        # Convert dict to ReferenceData object if needed
                        if isinstance(loaded_ref_data, dict) and not isinstance(loaded_ref_data, ReferenceData):
                            # Check if it's the metadata format (has 'prospectus', 'kid', 'sfdr' keys)
                            if 'prospectus' in loaded_ref_data or 'kid' in loaded_ref_data:
                                # This is metadata about reference docs, not actual performance data
                                # Skip setting reference_data as we don't have the actual data yet
                                logger.info(f"📄 Reference documents available for fund: {fund_name}")
                            else:
                                # Try to convert to ReferenceData object
                                self.reference_data = ReferenceData(**loaded_ref_data)
                                logger.info(f"✅ Loaded reference data for fund: {fund_name}")
                        else:
                            self.reference_data = loaded_ref_data
                            logger.info(f"✅ Loaded reference data for fund: {fund_name}")
                except Exception as e:
                    logger.warning(f"Could not load reference data for {fund_name}: {e}")
        
        # Step 1: Validate source and date for all tables/charts
        source_date_result = self._validate_source_and_date(extraction_result, metadata)
        result.compliance_issues.extend(source_date_result['issues'])
        result.total_tables_checked = source_date_result['total_tables']
        result.tables_with_source_date = source_date_result['tables_with_source_date']
        result.tables_missing_source_date = source_date_result['tables_missing_source_date']
        
        # Also validate charts (from chart analyzer)
        charts = extraction_result.get('charts', [])
        if charts:
            chart_validation = self._validate_charts(charts, metadata)
            result.compliance_issues.extend(chart_validation['issues'])
            result.total_charts_analyzed += chart_validation['total_charts']
            result.charts_with_source_date += chart_validation['charts_with_source_date']
            result.charts_missing_source_date += chart_validation['charts_missing_source_date']
            result.total_tables_checked += chart_validation['total_charts']
            result.tables_with_source_date += chart_validation['charts_with_source_date']
            result.tables_missing_source_date += chart_validation['charts_missing_source_date']
        
        # Step 2: Validate numerical data against reference documents
        if self.reference_data:
            numerical_result = self._validate_numerical_data(extraction_result, metadata)
            result.compliance_issues.extend(numerical_result['issues'])
            result.total_numerical_values_checked = numerical_result['total_checked']
            result.values_matching_reference = numerical_result['matching']
            result.values_with_inconsistencies = numerical_result['inconsistent']
        else:
            result.summary.append("Reference data not provided; numerical validation skipped")
        
        # Step 3: Cross-reference validation (performance in text vs tables)
        if self.enable_cross_reference:
            cross_ref_result = self._validate_cross_references(extraction_result)
            result.compliance_issues.extend(cross_ref_result['issues'])
            if cross_ref_result['issues']:
                result.summary.append(f"Cross-reference validation found {len(cross_ref_result['issues'])} issue(s)")
        
        # Step 4: Disclaimer validation (if enabled)
        if self.enable_disclaimer_validation and self.disclaimer_validator and metadata:
            try:
                disclaimer_result = self.disclaimer_validator.validate(extraction_result, metadata, document_id)
                result.disclaimer_validation = disclaimer_result.model_dump()
                if disclaimer_result.has_errors:
                    result.has_errors = True
                    result.summary.append(f"Disclaimer validation found {disclaimer_result.total_missing} missing disclaimer(s)")
                if disclaimer_result.has_warnings:
                    result.has_warnings = True
            except Exception as e:
                result.summary.append(f"Disclaimer validation failed: {str(e)}")
        
        # Step 5: Validate compliance rules (Performance, ESG, etc.)
        # Reset ESG cache before validation
        self._esg_analysis_cache = None
        compliance_issues = self._validate_compliance_rules(extraction_result, metadata)
        result.compliance_issues = compliance_issues
        
        # Step 5.5: Attach ESG enrichment data if available (populated during compliance validation)
        if self._esg_analysis_cache:
            result.esg_analysis = self._esg_analysis_cache
            logger.info(f"✅ ESG analysis data included in unified output")
        else:
            logger.debug(f"ℹ️ No ESG enrichment data available (ESG validation may not be enabled)")
        
        # Step 6: Determine overall status
        result.has_errors = bool(
            any(issue.severity == "error" for issue in result.compliance_issues) or
            (result.disclaimer_validation and result.disclaimer_validation.get('has_errors', False))
        )
        result.has_warnings = bool(
            any(issue.severity == "warning" for issue in result.compliance_issues) or
            (result.disclaimer_validation and result.disclaimer_validation.get('has_warnings', False))
        )
        
        # Check for critical issues
        has_critical = any(issue.severity == "critical" for issue in result.compliance_issues)
        
        if has_critical or result.has_errors:
            result.overall_status = "critical" if has_critical else "error"
        elif result.has_warnings:
            result.overall_status = "warning"
        else:
            result.overall_status = "pass"
        
        # Step 7: Log validation metrics
        if self.metrics:
            document_type = metadata.get('document_type', 'unknown') if metadata else 'unknown'
            fund_name = metadata.get('fund_name') or metadata.get('fund_full_name') if metadata else None
            # Build error message from issues if validation failed
            error_message = None
            if result.overall_status != "pass" and result.compliance_issues:
                critical_issues = [i for i in result.compliance_issues if i.severity == 'critical']
                if critical_issues:
                    error_message = f"{len(critical_issues)} critical issue(s) found"
                else:
                    error_message = f"{len(result.compliance_issues)} issue(s) found"
            
            self.metrics.log_validation(
                validation_type="data_consistency",
                status="passed" if result.overall_status == "pass" else "failed",
                document_type=document_type,
                fund_name=fund_name,
                error_message=error_message,
                severity=result.overall_status
            )
        
        # Step 8: Generate summary
        result.summary.extend(self._generate_summary(result))
        
        return result
    
    def _validate_source_and_date(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[ClientType] = None,
        fund_type: Optional[FundType] = None
    ) -> Dict[str, Any]:
        """
        Validate that all tables/charts have source and date information.
        
        Returns:
            Dict with validation results containing ComplianceIssue objects
        """
        issues: List[ComplianceIssue] = []
        tables = extraction_result.get('tables', [])
        table_sources = extraction_result.get('table_sources', [])
        
        # Create a map of slide/page -> table sources for quick lookup
        source_map: Dict[Tuple[Optional[int], Optional[int]], Dict[str, Any]] = {}
        for source in table_sources:
            slide = source.get('slide_number')
            page = source.get('page_number')
            key = (slide, page)
            source_map[key] = source
        
        total_tables = len(tables)
        tables_with_source_date = 0
        
        for table in tables:
            slide_num = table.get('slide_number')
            page_num = table.get('page_number')
            table_idx = table.get('table_index', 0)
            
            location_key = (slide_num, page_num)
            source_info = source_map.get(location_key)
            
            location_str = self._format_location(slide_num, page_num, table_idx)
            
            if not source_info:
                # No source information found for this table
                issues.append(self._create_source_date_issue(
                    issue_type_str="both_missing",
                    location=location_str,
                    message=f"Table at {location_str} is missing both source and date information",
                    table_index=table_idx,
                    slide_number=slide_num,
                    page_number=page_num,
                    severity="error"
                ))
            else:
                source_name = source_info.get('source_name')
                source_date = source_info.get('source_date')
                
                has_source = bool(source_name and source_name.strip())
                has_date = bool(source_date and source_date.strip())
                
                if has_source and has_date:
                    # Additional date validation if enabled
                    if self.enable_date_validation:
                        date_validation = self._validate_date_format_and_recency(
                            source_date, source_info, location_str, slide_num, page_num, table_idx, metadata
                        )
                        if date_validation:
                            issues.extend(date_validation)
                        else:
                            tables_with_source_date += 1
                    else:
                        tables_with_source_date += 1
                elif not has_source and not has_date:
                    issues.append(self._create_source_date_issue(
                        issue_type_str="both_missing",
                        location=location_str,
                        message=f"Table at {location_str} is missing both source and date",
                        table_index=table_idx,
                        slide_number=slide_num,
                        page_number=page_num,
                        severity="error"
                    ))
                elif not has_source:
                    issues.append(self._create_source_date_issue(
                        issue_type_str="missing_source",
                        location=location_str,
                        message=f"Table at {location_str} has date '{source_date}' but is missing source name",
                        table_index=table_idx,
                        slide_number=slide_num,
                        page_number=page_num,
                        severity="error"
                    ))
                elif not has_date:
                    issues.append(self._create_source_date_issue(
                        issue_type_str="missing_date",
                        location=location_str,
                        message=f"Table at {location_str} has source '{source_name}' but is missing date",
                        table_index=table_idx,
                        slide_number=slide_num,
                        page_number=page_num,
                        severity="error"
                    ))
        
        # Also check performance sections for source/date
        performance_sections = extraction_result.get('performance_sections', [])
        for section in performance_sections:
            slide_num = section.get('slide_number')
            page_num = section.get('page_number')
            location_key = (slide_num, page_num)
            
            if location_key not in source_map:
                location_str = self._format_location(slide_num, page_num, None)
                issues.append(self._create_source_date_issue(
                    issue_type_str="both_missing",
                    location=location_str,
                    message=f"Performance section at {location_str} may need source and date verification",
                    slide_number=slide_num,
                    page_number=page_num,
                    severity="warning"
                ))
        
        return {
            'issues': issues,
            'total_tables': total_tables,
            'tables_with_source_date': tables_with_source_date,
            'tables_missing_source_date': total_tables - tables_with_source_date
        }
    
    def _validate_numerical_data(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate numerical data against reference documents.
        
        Returns:
            Dict with validation results
        """
        inconsistencies: List[ComplianceIssue] = []
        total_checked = 0
        matching = 0
        
        if not self.reference_data:
            return {
                'inconsistencies': [],
                'total_checked': 0,
                'matching': 0,
                'inconsistent': 0
            }
        
        # Validate performance sections
        performance_sections = extraction_result.get('performance_sections', [])
        for section in performance_sections:
            entries = section.get('entries', [])
            slide_num = section.get('slide_number')
            page_num = section.get('page_number')
            location_str = self._format_location(slide_num, page_num, None)
            
            for entry in entries:
                value = entry.get('value')
                period = entry.get('period')
                basis = entry.get('basis')
                
                if value is None:
                    continue
                
                total_checked += 1
                
                # Look up reference value
                ref_value = self._get_reference_performance(period, basis)
                
                if ref_value is None:
                    # No reference data available for this period/basis
                    inconsistencies.append(self._create_numerical_issue(
                        location=location_str,
                        message=f"Performance value {value}% ({period}, {basis}) at {location_str} cannot be validated - no reference data available",
                        document_value=value,
                        reference_value=None,
                        reference_source=self.reference_data.source_document,
                        period=period,
                        basis=basis,
                        severity="warning"
                    ))
                else:
                    # Compare values with tolerance
                    if self._values_match(value, ref_value, self.default_tolerance):
                        matching += 1
                    else:
                        diff = abs(value - ref_value)
                        diff_pct = (diff / abs(ref_value) * 100) if ref_value != 0 else float('inf')
                        inconsistencies.append(self._create_numerical_issue(
                            location=location_str,
                            message=f"Performance mismatch at {location_str}: document shows {value}% but reference shows {ref_value}% (difference: {diff_pct:.2f}%)",
                            document_value=value,
                            reference_value=ref_value,
                            reference_source=self.reference_data.source_document,
                            period=period,
                            basis=basis,
                            tolerance=self.default_tolerance,
                            severity="error"
                        ))
        
        # Validate performance table entries
        table_entries = extraction_result.get('performance_table_entries', [])
        for entry in table_entries:
            value = entry.get('value')
            label = entry.get('label')
            column = entry.get('column')
            slide_num = entry.get('slide_number')
            table_idx = entry.get('table_index')
            location_str = self._format_location(slide_num, None, table_idx)
            
            if value is None:
                continue
            
            total_checked += 1
            
            # Try to match against reference table data
            ref_value = self._get_reference_table_value(label, column)
            
            if ref_value is None:
                # Try to infer period from column name
                period = self._infer_period_from_column(column)
                if period:
                    # Try performance lookup
                    ref_value = self._get_reference_performance(period, None)
            
            if ref_value is None:
                inconsistencies.append(self._create_numerical_issue(
                        location=location_str,
                        message=f"Table entry '{label}' = {value}% at {location_str} cannot be validated - no reference data available",
                        document_value=value,
                        reference_value=None,
                        reference_source=self.reference_data.source_document,
                        label=label,
                        severity="warning"
                    ))
            else:
                if self._values_match(value, ref_value, self.default_tolerance):
                    matching += 1
                else:
                    diff = abs(value - ref_value)
                    diff_pct = (diff / abs(ref_value) * 100) if ref_value != 0 else float('inf')
                    inconsistencies.append(self._create_numerical_issue(
                        location=location_str,
                        message=f"Table entry mismatch at {location_str}: '{label}' shows {value}% but reference shows {ref_value}% (difference: {diff_pct:.2f}%)",
                        document_value=value,
                        reference_value=ref_value,
                        reference_source=self.reference_data.source_document,
                        label=label,
                        tolerance=self.default_tolerance,
                        severity="error"
                    ))
        
        return {
            'inconsistencies': inconsistencies,
            'total_checked': total_checked,
            'matching': matching,
            'inconsistent': len(inconsistencies)
        }
    
    def _get_reference_performance(self, period: Optional[str], basis: Optional[str]) -> Optional[float]:
        """Get reference performance value for given period and basis."""
        if not self.reference_data or not period:
            return None
        
        period_lower = period.lower() if period else None
        basis_lower = basis.lower() if basis else None
        
        # Handle both ReferenceData object and dict
        performance_data = None
        if isinstance(self.reference_data, ReferenceData):
            performance_data = self.reference_data.performance_data
        elif isinstance(self.reference_data, dict):
            performance_data = self.reference_data.get('performance_data', {})
        
        if not performance_data:
            return None
        
        # Try exact match first
        if period_lower in performance_data:
            period_data = performance_data[period_lower]
            if basis_lower and basis_lower in period_data:
                return period_data[basis_lower]
            # Try 'net' as default
            if 'net' in period_data:
                return period_data['net']
            # Return first available value
            if period_data:
                return list(period_data.values())[0]
        
        # Try fuzzy matching for period
        for ref_period, period_data in performance_data.items():
            if self._periods_match(period_lower, ref_period):
                if basis_lower and basis_lower in period_data:
                    return period_data[basis_lower]
                if 'net' in period_data:
                    return period_data['net']
                if period_data:
                    return list(period_data.values())[0]
        
        return None
    
    def _get_reference_table_value(self, label: Optional[str], column: Optional[str]) -> Optional[float]:
        """Get reference table value for given label and column."""
        if not self.reference_data or not label:
            return None
        
        label_lower = label.lower().strip()
        
        # Try exact match
        if label_lower in self.reference_data.table_data:
            return self.reference_data.table_data[label_lower]
        
        # Try fuzzy matching
        for ref_label, value in self.reference_data.table_data.items():
            if label_lower in ref_label.lower() or ref_label.lower() in label_lower:
                return value
        
        return None
    
    def _periods_match(self, period1: Optional[str], period2: Optional[str]) -> bool:
        """Check if two period strings refer to the same period."""
        if not period1 or not period2:
            return False
        
        p1 = period1.lower().strip()
        p2 = period2.lower().strip()
        
        if p1 == p2:
            return True
        
        # Normalize common variations
        period_mappings = {
            '1y': ['1 year', '1yr', 'one year', '12 months'],
            '3y': ['3 years', '3yrs', 'three years', '36 months'],
            '5y': ['5 years', '5yrs', 'five years', '60 months'],
            'ytd': ['year to date', 'year-to-date'],
        }
        
        for key, variations in period_mappings.items():
            if p1 == key and p2 in variations:
                return True
            if p2 == key and p1 in variations:
                return True
        
        return False
    
    def _infer_period_from_column(self, column: Optional[str]) -> Optional[str]:
        """Infer period from column name (e.g., '1Y', 'YTD')."""
        if not column:
            return None
        
        column_lower = column.lower().strip()
        period_patterns = {
            '1y': r'\b1y\b|\b1\s*year\b|\b12\s*months\b',
            '3y': r'\b3y\b|\b3\s*years\b|\b36\s*months\b',
            '5y': r'\b5y\b|\b5\s*years\b|\b60\s*months\b',
            'ytd': r'\byt[d]\b|\byear\s*to\s*date\b',
        }
        
        for period, pattern in period_patterns.items():
            if re.search(pattern, column_lower):
                return period
        
        return None
    
    def _values_match(self, value1: float, value2: float, tolerance: float) -> bool:
        """Check if two values match within tolerance."""
        if value1 == value2:
            return True
        
        if value2 == 0:
            return abs(value1) < tolerance
        
        diff = abs(value1 - value2)
        relative_diff = diff / abs(value2)
        return relative_diff <= tolerance
    
    def _format_location(
        self,
        slide_number: Optional[int],
        page_number: Optional[int],
        table_index: Optional[int]
    ) -> str:
        """Format location string for reporting."""
        parts = []
        if slide_number is not None:
            parts.append(f"slide {slide_number}")
        if page_number is not None:
            parts.append(f"page {page_number}")
        if table_index is not None:
            parts.append(f"table {table_index}")
        
        if not parts:
            return "unknown location"
        
        return ", ".join(parts)
    
    def _validate_date_format_and_recency(
        self,
        source_date: str,
        source_info: Dict[str, Any],
        location_str: str,
        slide_num: Optional[int],
        page_num: Optional[int],
        table_idx: Optional[int],
        metadata: Optional[Dict[str, Any]]
    ) -> List[ComplianceIssue]:
        """
        Validate date format and check if date is too old or inconsistent with document date.
        
        Returns:
            List of ComplianceIssue objects (empty if no issues)
        """
        issues: List[ComplianceIssue] = []
        
        # Try to parse the date
        parsed_date = None
        try:
            # Try common date formats
            date_str = source_date.strip()
            # Remove common prefixes
            date_str = re.sub(r'^(source|date|as of|as at)[:\s]+', '', date_str, flags=re.IGNORECASE)
            date_str = date_str.strip()
            
            # Try parsing with dateutil (handles many formats)
            parsed_date = date_parser.parse(date_str, dayfirst=True, yearfirst=False)
        except (ValueError, TypeError, AttributeError):
            issues.append(self._create_source_date_issue(
                issue_type_str="invalid_date_format",
                location=location_str,
                message=f"Table at {location_str} has invalid date format: '{source_date}'",
                table_index=table_idx,
                slide_number=slide_num,
                page_number=page_num,
                severity="error"
            ))
            return issues
        
        if parsed_date is None:
            return issues
        
        # Check if date is too old
        today = datetime.now().date()
        date_only = parsed_date.date() if hasattr(parsed_date, 'date') else parsed_date
        
        if isinstance(date_only, datetime):
            date_only = date_only.date()
        
        days_old = (today - date_only).days
        
        if days_old > self.max_date_age_days:
            issues.append(self._create_source_date_issue(
                issue_type_str="date_too_old",
                location=location_str,
                message=f"Table at {location_str} has source date {date_only} which is {days_old} days old (max: {self.max_date_age_days} days)",
                table_index=table_idx,
                slide_number=slide_num,
                page_number=page_num,
                severity="warning"
            ))
        
        # Check consistency with document date from metadata
        if metadata:
            doc_date_str = None
            title_info = metadata.get('title_information', {})
            if isinstance(title_info, dict):
                doc_date_str = title_info.get('document_date') or title_info.get('date')
            
            if not doc_date_str:
                # Try metadata directly
                doc_date_str = metadata.get('document_date') or metadata.get('date')
            
            if doc_date_str:
                try:
                    doc_date = date_parser.parse(str(doc_date_str), dayfirst=True, yearfirst=False)
                    doc_date_only = doc_date.date() if hasattr(doc_date, 'date') else doc_date
                    
                    if isinstance(doc_date_only, datetime):
                        doc_date_only = doc_date_only.date()
                    
                    # Source date should not be significantly after document date
                    if date_only > doc_date_only:
                        days_diff = (date_only - doc_date_only).days
                        if days_diff > 30:  # Allow 30 days tolerance
                            issues.append(self._create_source_date_issue(
                                issue_type_str="date_inconsistent",
                                location=location_str,
                                message=f"Table at {location_str} has source date {date_only} which is {days_diff} days after document date {doc_date_only}",
                                table_index=table_idx,
                                slide_number=slide_num,
                                page_number=page_num,
                                severity="warning"
                            ))
                except (ValueError, TypeError, AttributeError):
                    # Document date parsing failed, skip consistency check
                    pass
        
        return issues
    
    def _validate_cross_references(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-reference validation: Check if performance data in text matches table data.
        
        Returns:
            Dict with validation results
        """
        issues: List[ComplianceIssue] = []
        
        # Build a map of performance values from tables by period and basis
        table_performance_map: Dict[Tuple[Optional[str], Optional[str]], List[Dict[str, Any]]] = {}
        
        table_entries = extraction_result.get('performance_table_entries', [])
        for entry in table_entries:
            period = self._infer_period_from_column(entry.get('column'))
            # Try to infer basis from label
            basis = None
            label_lower = (entry.get('label') or '').lower()
            if 'net' in label_lower:
                basis = 'net'
            elif 'gross' in label_lower:
                basis = 'gross'
            
            key = (period, basis)
            if key not in table_performance_map:
                table_performance_map[key] = []
            table_performance_map[key].append(entry)
        
        # Compare with performance sections (text-based performance data)
        performance_sections = extraction_result.get('performance_sections', [])
        for section in performance_sections:
            entries = section.get('entries', [])
            slide_num = section.get('slide_number')
            page_num = section.get('page_number')
            location_str = self._format_location(slide_num, page_num, None)
            
            for entry in entries:
                value = entry.get('value')
                period = entry.get('period')
                basis = entry.get('basis')
                
                if value is None:
                    continue
                
                # Look for matching table entries
                key = (period, basis)
                matching_table_entries = table_performance_map.get(key, [])
                
                # Also try without basis (more lenient matching)
                if not matching_table_entries:
                    key_no_basis = (period, None)
                    matching_table_entries = table_performance_map.get(key_no_basis, [])
                
                if matching_table_entries:
                    # Check if any table entry matches
                    found_match = False
                    for table_entry in matching_table_entries:
                        table_value = table_entry.get('value')
                        if table_value is not None:
                            if self._values_match(value, table_value, self.default_tolerance):
                                found_match = True
                                break
                    
                    if not found_match:
                        # Found mismatch
                        table_entry = matching_table_entries[0]
                        table_location = self._format_location(
                            table_entry.get('slide_number'),
                            None,
                            table_entry.get('table_index')
                        )
                        
                        issues.append(self._create_cross_reference_issue(
                            issue_type_str="performance_mismatch",
                            location=location_str,
                            message=f"Performance mismatch: text shows {value}% ({period}, {basis}) at {location_str}, but table shows {table_entry.get('value')}% at {table_location}",
                            value1=value,
                            value2=table_entry.get('value'),
                            location1=location_str,
                            location2=table_location,
                            period=period,
                            severity="error"
                        ))
        
        # Check for duplicate values with different periods (potential copy-paste errors)
        # Group performance entries by value and check if they have different periods
        value_period_map: Dict[float, List[Dict[str, Any]]] = {}
        for section in performance_sections:
            for entry in section.get('entries', []):
                value = entry.get('value')
                period = entry.get('period')
                if value is not None and period:
                    if value not in value_period_map:
                        value_period_map[value] = []
                    value_period_map[value].append({
                        'value': value,
                        'period': period,
                        'basis': entry.get('basis'),
                        'location': self._format_location(
                            section.get('slide_number'),
                            section.get('page_number'),
                            None
                        )
                    })
        
        # Flag suspicious duplicates (same value, different periods)
        for value, entries in value_period_map.items():
            if len(entries) > 1:
                periods = [e['period'] for e in entries]
                if len(set(periods)) > 1:
                    # Same value appears with different periods - potential error
                    locations = [e['location'] for e in entries]
                    issues.append(self._create_cross_reference_issue(
                        issue_type_str="duplicate_inconsistency",
                        location=", ".join(locations),
                        message=f"Suspicious duplicate: value {value}% appears with different periods ({', '.join(set(periods))}) at {', '.join(locations)}",
                        value1=value,
                        value2=value,
                        location1=locations[0],
                        location2=locations[1] if len(locations) > 1 else None,
                        period=", ".join(set(periods)),
                        severity="warning"
                    ))
        
        return {
            'issues': issues
        }
    
    def _validate_charts(
        self,
        charts: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate charts extracted by chart analyzer.
        
        Returns:
            Dict with validation results
        """
        issues: List[SourceDateIssue] = []
        total_charts = len(charts)
        charts_with_source_date = 0
        
        for chart in charts:
            slide_num = chart.get('slide_number')
            location_str = self._format_location(slide_num, None, None)
            source_info = chart.get('source_date_info', {})
            
            has_source = source_info.get('has_source', False)
            has_date = source_info.get('has_date', False)
            
            if has_source and has_date:
                # Validate date format if enabled
                if self.enable_date_validation:
                    date_text = source_info.get('date_text')
                    if date_text:
                        date_validation = self._validate_date_format_and_recency(
                            date_text, source_info, location_str, slide_num, None, None, metadata
                        )
                        if date_validation:
                            issues.extend(date_validation)
                        else:
                            charts_with_source_date += 1
                    else:
                        charts_with_source_date += 1
                else:
                    charts_with_source_date += 1
            elif not has_source and not has_date:
                issues.append(self._create_source_date_issue(
                    issue_type_str="both_missing",
                    location=f"Chart at {location_str}",
                    message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} is missing both source and date information",
                    slide_number=slide_num,
                    severity="error"
                ))
            elif not has_source:
                issues.append(self._create_source_date_issue(
                    issue_type_str="missing_source",
                    location=f"Chart at {location_str}",
                    message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} has date but is missing source name",
                    slide_number=slide_num,
                    severity="error"
                ))
            elif not has_date:
                issues.append(self._create_source_date_issue(
                    issue_type_str="missing_date",
                    location=f"Chart at {location_str}",
                    message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} has source but is missing date",
                    slide_number=slide_num,
                    severity="error"
                ))
        
        return {
            'issues': issues,
            'total_charts': total_charts,
            'charts_with_source_date': charts_with_source_date,
            'charts_missing_source_date': total_charts - charts_with_source_date
        }
    
    def _validate_compliance_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ComplianceIssue]:
        """
        Validate compliance rules (Performance, ESG, Disclaimers, etc.).
        
        Returns:
            List of ComplianceIssue objects
        """
        # Determine client type and fund type from metadata for context
        from .compliance_rules import ClientType, FundType
        
        client_type = None
        fund_type = FundType.STANDARD  # Default
        
        if metadata:
            # Determine client type
            is_professional = metadata.get('is_professional_client', False)
            client_type = ClientType.PROFESSIONAL if is_professional else ClientType.RETAIL
            
            # Determine fund type from metadata or fund name
            fund_name = ""
            title_info = metadata.get('title_information', {})
            fund_name = (title_info.get('fund_name') or metadata.get('fund_name') or "").lower()
            
            # Check for specific fund types
            if "fcpr" in fund_name or "fpci" in fund_name or "private equity" in fund_name:
                fund_type = FundType.PRIVATE_EQUITY
            elif "etf" in fund_name or "exchange traded" in fund_name:
                fund_type = FundType.ETF
            elif "daté" in fund_name or "dated" in fund_name or "échéance" in fund_name:
                fund_type = FundType.DATED
            else:
                fund_type = FundType.STANDARD
        
        issues: List[ComplianceIssue] = []
        
        # Phase 1: Performance Rules
        issues.extend(self._validate_performance_rules(extraction_result, metadata, client_type, fund_type))
        
        # Phase 2: Cover Page and Slide 2 Rules
        issues.extend(self._validate_cover_page_rules(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_slide_2_rules(extraction_result, metadata, client_type, fund_type))
        
        # Phase 3: Disclaimer Rules
        issues.extend(self._validate_disclaimer_rules(extraction_result, metadata, client_type, fund_type))
        
        # Phase 4: ESG and Securities Rules
        issues.extend(self._validate_esg_rules(extraction_result, metadata, client_type, fund_type))
        
        # Phase 5: Fund Type Specific Rules
        issues.extend(self._validate_fund_type_rules(extraction_result, metadata, client_type, fund_type))
        
        # Phase 6: Content Rules
        issues.extend(self._validate_content_rules(extraction_result, metadata, client_type, fund_type))
        
        # Phase 7: Country Registration Rules
        issues.extend(self._validate_country_registration_rules(extraction_result, metadata, client_type, fund_type))
        
        # Phase 8: General Rules
        issues.extend(self._validate_general_rules(extraction_result, metadata, client_type, fund_type))
        
        return issues

    def _validate_fund_type_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate rules specific to certain fund types (Dated, PE, ETF).
        """
        issues: List[ComplianceIssue] = []
        
        # Determine fund type from metadata or title
        fund_name = ""
        if metadata:
            title_info = metadata.get('title_information', {})
            fund_name = (title_info.get('fund_name') or metadata.get('fund_name') or "").lower()
        
        # Check for Private Equity (FCPR, FPCI)
        if "fcpr" in fund_name or "fpci" in fund_name:
             disclaimers_found = extraction_result.get('disclaimers', [])
             disclaimer_texts = []
             for d in disclaimers_found:
                if isinstance(d, str):
                    disclaimer_texts.append(d.lower())
                elif isinstance(d, dict):
                    disclaimer_texts.append(d.get('text', '').lower())
             full_disclaimer_text = " ".join(disclaimer_texts)
             
             if "liquidité" not in full_disclaimer_text and "liquidity" not in full_disclaimer_text:
                  issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_STANDARD_DISCLAIMER,
                    rule_reference="Section 4.1",
                    location="Disclaimers",
                    severity="error",
                    message="Private Equity fund detected, but warning about 'Liquidity Risk' is missing."
                ))

        return issues

    def _validate_esg_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate ESG and securities mention rules.
        
        Rules:
        - If securities are mentioned, must include disclaimer "Not a recommendation".
        - ESG claims must be consistent.
        - ESG/SFDR compliance validation (Article 6/8/9 rules) if ESG validation is enabled.
        """
        issues: List[ComplianceIssue] = []
        
        # ============================================================================
        # PART 1: Securities Disclaimer Validation (existing logic)
        # ============================================================================
        has_holdings = bool(extraction_result.get('top_holdings') or extraction_result.get('portfolio_breakdown'))
        
        if has_holdings:
            disclaimers_found = extraction_result.get('disclaimers', [])
            disclaimer_texts = []
            for d in disclaimers_found:
                if isinstance(d, str):
                    disclaimer_texts.append(d.lower())
                elif isinstance(d, dict):
                    disclaimer_texts.append(d.get('text', '').lower())
            full_disclaimer_text = " ".join(disclaimer_texts)
            
            if "recommandation" not in full_disclaimer_text and "recommendation" not in full_disclaimer_text:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.INVESTMENT_RECOMMENDATION,
                    rule_reference="Section 4.2",
                    location="Disclaimers",
                    severity="warning",
                    message="Specific securities are mentioned, but disclaimer stating 'This is not a recommendation to buy or sell' is missing.",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # ============================================================================
        # PART 2: ESG/SFDR Compliance Validation (Integrated ESG Analysis)
        # ============================================================================
        if self.enable_esg_validation and self.esg_analyzer:
            try:
                esg_issues = self._validate_esg_compliance_integrated(
                    extraction_result=extraction_result,
                    metadata=metadata,
                    client_type=client_type,
                    fund_type=fund_type
                )
                issues.extend(esg_issues)
            except Exception as e:
                logger.error(f"❌ ESG compliance validation failed: {e}")
                # Don't fail the entire validation, just log the error
        
        return issues
    
    def _validate_esg_compliance_integrated(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Integrated ESG/SFDR compliance validation using already-extracted data.
        
        This method validates:
        - Article 8 funds: ESG content must be < 10% of total text
        - Article 6 funds: ESG content forbidden (0 commercial mentions)
        - Article 9 funds: Engaging criteria must be met
        - ESG keywords tracking and location analysis
        
        ✅ OPTIMIZED: Uses already-extracted data, no redundant document loading
        
        Returns:
            List of ComplianceIssue objects for detected violations
        """
        issues: List[ComplianceIssue] = []
        
        try:
            # ============================================================================
            # Extract fund metadata from already-extracted data
            # ============================================================================
            fund_name = "Unknown Fund"
            sfdr_article = None
            document_type = "marketing"
            
            if metadata:
                title_info = metadata.get('title_information', {})
                fund_name = title_info.get('fund_name') or metadata.get('fund_name') or fund_name
                sfdr_article = metadata.get('sfdr_article')
                document_type = metadata.get('document_type', 'marketing')
                
                # Try to detect from metadata if available
                if not sfdr_article:
                    esg_approach = metadata.get('esg_approach', '').lower()
                    if 'article 9' in esg_approach or 'engaging' in esg_approach:
                        sfdr_article = 9
                    elif 'article 8' in esg_approach or 'reduced' in esg_approach:
                        sfdr_article = 8
                    elif 'article 6' in esg_approach or 'none' in esg_approach or 'limited' in esg_approach:
                        sfdr_article = 6
            
            # ============================================================================
            # Build text and slides from already-extracted data (NO re-loading)
            # ============================================================================
            full_text_parts = []
            slides_data = []
            
            # Try multiple sources for slide data
            all_slides = []
            
            # Method 1: Check extraction_result['slides'] directly
            if 'slides' in extraction_result and extraction_result['slides']:
                all_slides = extraction_result['slides']
                logger.info(f"Using extraction_result['slides']: {len(all_slides)} slides")
            
            # Method 2: Check structure.slides
            elif 'structure' in extraction_result and 'slides' in extraction_result['structure']:
                all_slides = extraction_result['structure']['slides']
                logger.info(f"Using structure.slides: {len(all_slides)} slides")
            
            # Method 3: Fallback to text field
            elif 'text' in extraction_result and extraction_result['text']:
                full_text = extraction_result['text']
                slides_data = [{'slide_number': 1, 'text': full_text, 'title': 'Document'}]
                logger.info(f"Using extraction_result['text']: {len(full_text)} characters")
            
            # Extract text from slides
            if all_slides and not full_text_parts:
                for i, slide in enumerate(all_slides, 1):
                    if isinstance(slide, dict):
                        slide_num = slide.get('slide_number', i)
                        title = slide.get('title', '')
                        
                        # Build slide text from various possible formats
                        slide_text = title + "\n"
                        
                        # Check for content field (list of items)
                        if 'content' in slide:
                            content_items = slide['content']
                            for item in content_items:
                                if isinstance(item, dict):
                                    slide_text += item.get('text', '') + "\n"
                                else:
                                    slide_text += str(item) + "\n"
                        
                        # Check for text field directly
                        elif 'text' in slide:
                            slide_text += slide['text'] + "\n"
                        
                        # Check for summary field
                        elif 'summary' in slide:
                            slide_text += slide['summary'] + "\n"
                        
                        full_text_parts.append(slide_text)
                        slides_data.append({
                            'slide_number': slide_num,
                            'text': slide_text,
                            'title': title
                        })
                    elif isinstance(slide, str):
                        # Slide is just a string
                        full_text_parts.append(slide)
                        slides_data.append({
                            'slide_number': i,
                            'text': slide,
                            'title': ''
                        })
            
            if not slides_data:
                full_text = ""
            else:
                full_text = "\n".join(full_text_parts)
            
            if not full_text.strip():
                logger.warning("⚠️ No text content found in extraction_result")
                return issues
            
            logger.info(f"🔍 ESG Validation (Integrated): Fund={fund_name}, Article={sfdr_article}")
            logger.info(f"📄 Analyzing {len(full_text)} characters across {len(slides_data)} slides")
            
            # ============================================================================
            # Run ESG Analysis with already-extracted data (OPTIMIZED)
            # ✅ ENHANCEMENT: No redundant document loading, uses extraction_result
            # ============================================================================
            max_retries = 2
            esg_level = None
            esg_mentions = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # Parallel LLM calls for ESG level and mentions
                    from concurrent.futures import ThreadPoolExecutor
                    
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        future_level = executor.submit(
                            self.esg_analyzer.detect_esg_level_v2,
                            fund_name, full_text, sfdr_article
                        )
                        future_mentions = executor.submit(
                            self.esg_analyzer.analyze_esg_mentions_v2,
                            full_text, document_type, slides_data
                        )
                        
                        esg_level = future_level.result()
                        esg_mentions = future_mentions.result()
                    
                    break  # Success
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ ESG analysis attempt {attempt+1} failed, retrying: {e}")
                        import time
                        time.sleep(1)
                    else:
                        logger.error(f"❌ ESG analysis failed after {max_retries} attempts: {e}")
            
            # Handle validation failure with synthetic issue
            if not esg_level or not esg_mentions:
                issues.append(
                    ComplianceIssue(
                        issue_type=ComplianceIssueType.ESG_LEVEL_MISMATCH,
                        severity="medium",
                        description=f"ESG validation could not be completed: {str(last_error)}",
                        location="ESG Analyzer",
                        details={"error": str(last_error), "fallback": "validation_failure"}
                    )
                )
                return issues
            
            logger.info(f"📊 ESG Level Detected: {esg_level.level.upper()} (Article {esg_level.sfdr_article or 'Unknown'})")
            logger.info(f"📈 ESG Analysis: {esg_mentions.esg_percentage}% ESG content, {esg_mentions.commercial_esg_mentions} commercial mentions")
            logger.info(f"🔍 Keywords found: {', '.join(esg_mentions.esg_keywords_found[:10])}")
            
            # Store ESG analysis metadata for output enrichment
            self._esg_analysis_cache = {
                "esg_level": {
                    "level": esg_level.level,
                    "sfdr_article": esg_level.sfdr_article,
                    "exclusion_percentage": esg_level.exclusion_percentage,
                    "portfolio_coverage": esg_level.portfolio_coverage,
                    "description": esg_level.description
                },
                "esg_mentions": {
                    "esg_percentage": esg_mentions.esg_percentage,
                    "total_text_length": esg_mentions.total_text_length,
                    "esg_text_length": esg_mentions.esg_text_length,
                    "commercial_esg_mentions": esg_mentions.commercial_esg_mentions,
                    "mandatory_regulatory_mentions": esg_mentions.mandatory_regulatory_mentions,
                    "keywords_found": esg_mentions.esg_keywords_found,
                    "keywords_by_slide": esg_mentions.esg_keywords_by_slide
                },
                "analysis_timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # ============================================================================
            # Generate ComplianceIssue objects based on ESG analysis results
            # ============================================================================
            
            # Rule 1: Article 6 (None) - ESG content forbidden
            if esg_level.level == "none" or esg_level.sfdr_article == 6:
                if esg_mentions.commercial_esg_mentions > 0:
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.ESG_FORBIDDEN_ARTICLE6,
                        rule_reference="SFDR Article 6",
                        location="Document-wide",
                        severity="critical",
                        message=f"Article 6 (non-ESG): {esg_mentions.commercial_esg_mentions} commercial ESG mentions detected",
                        context=f"ESG Level: {esg_level.level}, ESG%: {esg_mentions.esg_percentage}%, Keywords: {', '.join(esg_mentions.esg_keywords_found[:5])}",
                        suggestion="Remove all commercial ESG mentions from Article 6 fund materials",
                        client_type=client_type,
                        fund_type=fund_type,
                        details={
                            "esg_percentage": esg_mentions.esg_percentage,
                            "commercial_mentions": esg_mentions.commercial_esg_mentions,
                            "keywords_found": esg_mentions.esg_keywords_found,
                            "sample_sentences": esg_mentions.esg_sentences[:3]
                        }
                    ))
            
            # Rule 2: Article 8 (Reduced) - ESG content must be < 10%
            if esg_level.level == "reduced" or esg_level.sfdr_article == 8:
                if esg_mentions.esg_percentage > 10.0:
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.ESG_OVERMENTIONED_ARTICLE8,
                        rule_reference="SFDR Article 8",
                        location="Document-wide",
                        severity="high",
                        message=f"Article 8 fund: ESG content exceeds 10% limit ({esg_mentions.esg_percentage}%)",
                        context=f"ESG Level: {esg_level.level}, Commercial mentions: {esg_mentions.commercial_esg_mentions}",
                        suggestion="Reduce ESG content to below 10% of total document text",
                        client_type=client_type,
                        fund_type=fund_type,
                        details={
                            "esg_percentage": esg_mentions.esg_percentage,
                            "limit": 10.0,
                            "excess": round(esg_mentions.esg_percentage - 10.0, 2)
                        }
                    ))
            
            # Rule 3: Article 9 (Engaging) - Must meet engaging criteria
            if esg_level.level == "engaging" or esg_level.sfdr_article == 9:
                criteria_issues = []
                if (esg_level.exclusion_percentage or 0) < 20:
                    criteria_issues.append(f"exclusion_percentage={esg_level.exclusion_percentage}% (required: >= 20%)")
                if (esg_level.portfolio_coverage or 0) < 90:
                    criteria_issues.append(f"portfolio_coverage={esg_level.portfolio_coverage}% (required: >= 90%)")
                
                if criteria_issues:
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.ENGAGING_CRITERIA_NOT_MET,
                        rule_reference="SFDR Article 9",
                        location="Document-wide",
                        severity="high",
                        message=f"Article 9 (engaging) fund does not meet criteria: {', '.join(criteria_issues)}",
                        context=f"ESG Level: {esg_level.level}, Description: {esg_level.description}",
                        suggestion="Verify fund classification or ensure exclusion percentage >= 20% and portfolio coverage >= 90%",
                        client_type=client_type,
                        fund_type=fund_type,
                        details={
                            "exclusion_percentage": esg_level.exclusion_percentage,
                            "portfolio_coverage": esg_level.portfolio_coverage,
                            "required_exclusion": 20.0,
                            "required_coverage": 90.0
                        }
                    ))
            
            # Rule 4: Check for ESG level mismatch with metadata
            if metadata and metadata.get('sfdr_article') and metadata.get('sfdr_article') != esg_level.sfdr_article:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.SFDR_ARTICLE_INCONSISTENCY,
                    rule_reference="SFDR Disclosure",
                    location="Document metadata",
                    severity="medium",
                    message=f"SFDR article mismatch: metadata indicates Article {metadata.get('sfdr_article')}, but content suggests Article {esg_level.sfdr_article or 'Unknown'}",
                    context=f"Detected ESG level: {esg_level.level}, Description: {esg_level.description}",
                    suggestion="Verify SFDR classification and ensure document content aligns with declared article",
                    client_type=client_type,
                    fund_type=fund_type,
                    details={
                        "metadata_article": metadata.get('sfdr_article'),
                        "detected_article": esg_level.sfdr_article,
                        "detected_level": esg_level.level
                    }
                ))
            
            # Rule 5: Keyword overuse detection (if ESG mentions are excessive in specific locations)
            if esg_mentions.esg_keywords_by_slide and esg_level.level != "engaging":
                # Find slides with same keyword appearing >10 times
                for keyword, slide_nums in esg_mentions.esg_keywords_by_slide.items():
                    if len(slide_nums) > 10:  # Same keyword appears in >10 slides
                        issues.append(ComplianceIssue(
                            issue_type=ComplianceIssueType.ESG_KEYWORD_OVERUSE,
                            rule_reference="Best Practices",
                            location=f"Keyword '{keyword}' appears in {len(slide_nums)} slides",
                            severity="low",
                            message=f"ESG keyword '{keyword}' appears excessively across {len(slide_nums)} slides",
                            context=f"Slides: {', '.join(map(str, slide_nums[:10]))}{'...' if len(slide_nums) > 10 else ''}",
                            suggestion=f"Consider reducing repetition of ESG keyword '{keyword}' for {esg_level.level} fund classification",
                            client_type=client_type,
                            fund_type=fund_type,
                            details={
                                "keyword": keyword,
                                "slide_count": len(slide_nums),
                                "slides": slide_nums
                            }
                        ))
            
            logger.info(f"✅ ESG Validation Complete: {len(issues)} issue(s) found")
            
        except ImportError as e:
            logger.error(f"❌ ESG Analyzer import failed: {e}")
        except Exception as e:
            logger.error(f"❌ ESG compliance validation error: {e}")
            import traceback
            traceback.print_exc()
        
        return issues

    def _validate_disclaimer_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate disclaimer rules.
        
        Rules:
        - General disclaimer must be present.
        - Risk of capital loss must be mentioned.
        - Past performance warning must be present (if performance is shown).
        """
        issues: List[ComplianceIssue] = []
        
        # We need to check for the presence of specific phrases in the document.
        # Ideally, we would have a 'disclaimers' section in extraction_result.
        
        disclaimers_found = extraction_result.get('disclaimers', [])
        # Flatten list if it's a list of strings, or extract text if it's a list of dicts
        disclaimer_texts = []
        for d in disclaimers_found:
            if isinstance(d, str):
                disclaimer_texts.append(d.lower())
            elif isinstance(d, dict):
                disclaimer_texts.append(d.get('text', '').lower())
        
        full_disclaimer_text = " ".join(disclaimer_texts)
        
        # Check for Capital Loss warning
        if "perte en capital" not in full_disclaimer_text and "capital loss" not in full_disclaimer_text:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_STANDARD_DISCLAIMER,
                rule_reference="Section 1",
                location="Disclaimers",
                severity="error",
                message="Warning about 'Risk of Capital Loss' (Risque de perte en capital) is missing.",
                context="No capital loss warning found in disclaimers",
                suggestion="Add warning: 'Capital is not guaranteed and you may not get back the amount you invested'",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        # Check for Past Performance warning if performance is shown
        has_performance = bool(extraction_result.get('performance_sections') or extraction_result.get('performance_table_entries'))
        if has_performance:
            if "performances passées" not in full_disclaimer_text and "past performance" not in full_disclaimer_text:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_PERFORMANCE_DISCLAIMER,
                    rule_reference="Section 4.3",
                    location="Disclaimers",
                    severity="error",
                    message="Warning that 'Past performance is not a reliable indicator of future results' is missing.",
                    context="Performance data shown without past performance disclaimer",
                    suggestion="Add disclaimer: 'Past performance is not a reliable indicator of future results'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        return issues

    def _validate_cover_page_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate cover page (Slide 1) rules.
        
        Rules:
        - Must contain Fund Name
        - Must contain Management Company Name
        - Must contain Document Date
        """
        issues: List[ComplianceIssue] = []
        
        # We need text content of Slide 1. 
        # Assuming extraction_result has 'slides' or we can infer from other data.
        # If we don't have raw text, we might be limited.
        # Let's assume we can check metadata or specific extracted fields.
        
        # Check if we have title information which usually comes from Slide 1
        title_info = metadata.get('title_information', {}) if metadata else {}
        
        if not title_info.get('fund_name'):
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_FUND_NAME,
                rule_reference="Section 2",
                location="Slide 1",
                severity="error",
                message="Fund Name is missing on the cover page."
            ))
            
        # Check for Management Company Name (often hard to detect without full text, but let's check metadata)
        # If we can't check it reliably, we might skip or warn.
        
        # Check for Promotional Mention
        promotional_mentions = [
            "document promotionnel", "promotional document", "werbedokument",
            "à caractère promotionnel", "marketing document", "zu werbezwecken"
        ]
        # We need text content of Slide 1. Assuming we can search in a 'text' field of slide 1 if available,
        # or just search in the whole document if we can't pinpoint slide 1 text easily, 
        # but the rule is specific to cover page.
        # For now, let's assume we have a 'cover_page_text' in metadata or extraction result.
        cover_text = extraction_result.get('cover_page_text', '').lower()
        
        if cover_text:
            if not any(mention in cover_text for mention in promotional_mentions):
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_PROMOTIONAL_MENTION,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="error",
                    message="Cover page must include a promotional mention (e.g., 'Document promotionnel', 'Marketing communication')."
                ))

        # Check for Promotional Mention
        promotional_mentions = [
            "document promotionnel", "promotional document", "werbedokument",
            "à caractère promotionnel", "marketing document", "zu werbezwecken"
        ]
        # We need text content of Slide 1. Assuming we can search in a 'text' field of slide 1 if available,
        # or just search in the whole document if we can't pinpoint slide 1 text easily, 
        # but the rule is specific to cover page.
        # For now, let's assume we have a 'cover_page_text' in metadata or extraction result.
        cover_text = extraction_result.get('cover_page_text', '').lower()
        
        # If cover_page_text is not explicitly available, try to infer from first page of text content if available
        if not cover_text and 'pages' in extraction_result and len(extraction_result['pages']) > 0:
             cover_text = extraction_result['pages'][0].get('content', '').lower()

        if cover_text:
            if not any(mention in cover_text for mention in promotional_mentions):
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_PROMOTIONAL_MENTION,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="error",
                    message="Cover page must include a promotional mention (e.g., 'Document promotionnel', 'Marketing communication')."
                ))

        if not title_info.get('date') and not title_info.get('document_date'):
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_DATE,
                rule_reference="Section 2",
                location="Slide 1",
                severity="error",
                message="Document Date is missing on the cover page."
            ))
            
        return issues

    def _validate_slide_2_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate Slide 2 rules.
        
        Rules:
        - Must contain Risk Scale (SRI)
        - Must contain Investment Horizon
        """
        issues: List[ComplianceIssue] = []
        
        # We need to check if specific terms appear on Slide 2.
        # This requires access to the text of Slide 2.
        # If extraction_result doesn't provide per-slide text, we might need to rely on 'tables' or 'charts' on slide 2
        # or hope that 'metadata' contains extracted risk info.
        
        # Let's check if we have risk indicators extracted
        risk_indicators = extraction_result.get('risk_indicators', {})
        
        # If we have risk indicators, we can check if they were found on Slide 2 (if location info is preserved)
        # Or just check if they exist at all, as they are required.
        
        if not risk_indicators.get('sri') and not risk_indicators.get('risk_scale'):
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_RISK_PROFILE,
                rule_reference="Section 3",
                location="Slide 2",
                slide_number=2,
                severity="error",
                message="Risk Scale (SRI) is missing. It is usually required on Slide 2.",
                context="No SRI (Synthetic Risk Indicator) found",
                suggestion="Add SRI scale (typically 1-7 risk scale) on slide 2",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        if not risk_indicators.get('investment_horizon'):
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_RISK_PROFILE,
                rule_reference="Section 3",
                location="Slide 2",
                slide_number=2,
                severity="warning",
                message="Investment Horizon is missing. It is usually required on Slide 2.",
                context="No investment horizon/recommended holding period found",
                suggestion="Add recommended investment horizon (e.g., '5 years minimum') on slide 2",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        return issues

    def _validate_performance_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate performance display rules.
        
        Rules:
        - 10Y history required (or since inception if < 10Y)
        - 5Y history required (or since inception if < 5Y)
        - Reference index must be shown
        - Past performance warning must be present
        - Performance cannot be the main focus (not on cover page)
        - Benchmark comparison required
        - Net performance for retail
        """
        issues: List[ComplianceIssue] = []
        
        # Check if performance is on the cover page (Slide 1)
        performance_sections = extraction_result.get('performance_sections', [])
        for section in performance_sections:
            slide_num = section.get('slide_number')
            if slide_num == 1:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.PERFORMANCE_STARTS_DOCUMENT,
                    rule_reference="Section 4.3",
                    location="Slide 1",
                    slide_number=1,
                    severity="error",
                    message="Performance data should not be displayed on the cover page (Slide 1). It must not be the main focus.",
                    context="Performance found on first slide",
                    suggestion="Move performance data to later slides (typically slide 3 or later)",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Check for required performance history (5Y, 10Y)
        periods_found = set()
        for section in performance_sections:
            for entry in section.get('entries', []):
                if entry.get('period'):
                    periods_found.add(entry.get('period').lower())
        
        for entry in extraction_result.get('performance_table_entries', []):
            column = entry.get('column')
            if column:
                period = self._infer_period_from_column(column)
                if period:
                    periods_found.add(period.lower())
        
        has_5y = any('5y' in p or '5 year' in p for p in periods_found)
        has_10y = any('10y' in p or '10 year' in p for p in periods_found)
        
        if not has_5y:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.INSUFFICIENT_PERFORMANCE_HISTORY,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="5-year performance history not found. Required if the fund is older than 5 years.",
                context="Missing 5-year performance history",
                suggestion="Add 5-year performance data if fund is older than 5 years",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        if not has_10y:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.INSUFFICIENT_PERFORMANCE_HISTORY,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="10-year performance history not found. Required if the fund is older than 10 years.",
                context="Missing 10-year performance history",
                suggestion="Add 10-year performance data if fund is older than 10 years",
                client_type=client_type,
                fund_type=fund_type
            ))

        # Check for Benchmark Comparison
        # We check if any performance table or section mentions a benchmark/index
        has_benchmark = False
        
        # Check table labels
        for entry in extraction_result.get('performance_table_entries', []):
            label = (entry.get('label') or '').lower()
            if 'benchmark' in label or 'index' in label or 'indice' in label or 'vergleichsindex' in label:
                has_benchmark = True
                break
        
        # Check section text if not found in tables
        if not has_benchmark:
            for section in performance_sections:
                # We don't have raw text of section here easily, but we can check entries if they have labels
                # Or we can check if we have a 'benchmark_name' in metadata
                pass

        if metadata and metadata.get('benchmark_name'):
            has_benchmark = True

        if not has_benchmark and (performance_sections or extraction_result.get('performance_table_entries')):
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_BENCHMARK_COMPARISON,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="Performance is shown but no benchmark comparison detected. Performance must be compared to the official benchmark.",
                context="No benchmark found in performance data",
                suggestion="Add benchmark comparison alongside fund performance",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Check for Net Performance indication (for retail clients)
        if client_type == ClientType.RETAIL and (performance_sections or extraction_result.get('performance_table_entries')):
            has_net_indication = False
            
            # Check table labels/columns
            for entry in extraction_result.get('performance_table_entries', []):
                label = (entry.get('label') or '').lower()
                column = (entry.get('column') or '').lower()
                if 'net' in label or 'net' in column or 'nette' in label or 'nette' in column:
                    has_net_indication = True
                    break
            
            # Check text content
            if not has_net_indication:
                all_text = ""
                if 'pages' in extraction_result:
                    for page in extraction_result['pages']:
                        all_text += " " + page.get('content', '')
                if "net performance" in all_text.lower() or "performance nette" in all_text.lower() or "net of fees" in all_text.lower():
                    has_net_indication = True

            if not has_net_indication:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_NET_PERFORMANCE_INDICATION,
                    rule_reference="Section 4.3",
                    location="Performance Section",
                    severity="warning",
                    message="Retail performance must be displayed Net of fees. No 'Net' indication found.",
                    context="Performance shown without 'Net' indication",
                    suggestion="Add 'Net of fees' or 'Net' indication to all performance figures",
                    client_type=client_type,
                    fund_type=fund_type
                ))

        return issues

    def _validate_content_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate content rules (Section 4).
        """
        issues: List[ComplianceIssue] = []
        
        # Check for Morningstar Rating Date
        # We need to scan text for "Morningstar" and check if a date is nearby.
        # This is a heuristic check.
        
        # Flatten all text content for searching
        all_text = ""
        if 'pages' in extraction_result:
            for page in extraction_result['pages']:
                all_text += " " + page.get('content', '')
        
        all_text_lower = all_text.lower()
        
        if "morningstar" in all_text_lower:
            # Check if there is a date associated with Morningstar
            # Simple check: is there a date pattern near "morningstar"?
            # Or just check if any date is present in the same block/sentence.
            # For now, we'll check if the rule is violated by looking for specific missing patterns if we could parse it better.
            # But let's just check if we can find a date in the whole text if Morningstar is mentioned, 
            # or better, check if the specific Morningstar date rule is met.
            
            # Let's assume if Morningstar is mentioned, we need a date.
            # We can check if we extracted a 'morningstar_date' in metadata (if we had such extractor).
            # Since we don't, we'll do a text search for date patterns near "morningstar".
            
            # Regex for date (simple)
            date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}'
            
            # Find all indices of "morningstar"
            for match in re.finditer("morningstar", all_text_lower):
                start = max(0, match.start() - 100)
                end = min(len(all_text_lower), match.end() + 100)
                context = all_text_lower[start:end]
                
                if not re.search(date_pattern, context):
                     issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.MORNINGSTAR_MISSING_DATE,
                        rule_reference="Section 4",
                        location="Content",
                        severity="warning",
                        message="Morningstar rating mentioned but no date found nearby. Ratings must be dated."
                    ))
                    # Only report once
                     break

        # Check for Team Change Disclaimer
        # Required if team is mentioned? Or always? Rule says "TEAM_MAY_CHANGE_DISCLAIMER_REQUIRED: bool = True"
        # Let's check if "team" or "équipe" is mentioned.
        if "team" in all_text_lower or "équipe" in all_text_lower or "management" in all_text_lower:
            disclaimers_found = extraction_result.get('disclaimers', [])
            disclaimer_texts = [d if isinstance(d, str) else d.get('text', '') for d in disclaimers_found]
            full_disclaimer_text = " ".join(disclaimer_texts).lower()
            
            team_change_phrases = [
                "l'équipe est susceptible de changer", "team is subject to change",
                "das team kann sich ändern", "management team may change",
                "équipe de gestion peut changer", "team may change"
            ]
            
            if not any(phrase in full_disclaimer_text for phrase in team_change_phrases):
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_TEAM_CHANGE_DISCLAIMER,
                    rule_reference="Section 4",
                    location="Disclaimers",
                    severity="warning",
                    message="Management team mentioned, but disclaimer 'The team is subject to change' is missing."
                ))

        return issues

    def _validate_general_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate general rules (Section 1).
        """
        issues: List[ComplianceIssue] = []
        
        # Check for Glossary (Retail only)
        # We need to know if it's a retail document.
        # Assuming we can determine client type from metadata or default to retail if unknown for safety.
        client_type = ClientType.RETAIL # Default to retail for safety/strictness
        if metadata and metadata.get('target_audience'):
            if 'professional' in metadata['target_audience'].lower():
                client_type = ClientType.PROFESSIONAL
        
        if client_type == ClientType.RETAIL:
            # Check for glossary
            # Look for "Glossary" or "Glossaire" section header or content
            all_text = ""
            if 'pages' in extraction_result:
                for page in extraction_result['pages']:
                    all_text += " " + page.get('content', '')
            
            if "glossaire" not in all_text.lower() and "glossary" not in all_text.lower():
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_GLOSSARY,
                    rule_reference="Section 1",
                    location="General",
                    severity="warning",
                    message="Retail document requires a Glossary.",
                    context="No glossary found in document",
                    suggestion="Add a glossary section explaining technical terms used in the document",
                    client_type=client_type,
                    fund_type=fund_type
                ))

        return issues
    
    def _validate_country_registration_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate country registration rules.
        
        Checks if countries mentioned in the document are registered for distribution.
        """
        issues: List[ComplianceIssue] = []
        
        # Get countries mentioned in document
        countries_detected = extraction_result.get('structure', {}).get('countries_detected', [])
        country_entries = extraction_result.get('country_entries', [])
        
        if not countries_detected and not country_entries:
            return issues
        
        # Try to get fund name from metadata
        fund_name = None
        if metadata:
            fund_name = metadata.get('fund_name') or metadata.get('title_information', {}).get('fund_name')
        
        if not fund_name:
            # Can't validate without fund name
            return issues
        
        # Load registration parser
        try:
            from .registration_parser import RegistrationParser
            
            # Initialize with default dataset path
            parser = RegistrationParser()
            
            # Get all mentioned countries
            all_countries = set(countries_detected) if countries_detected else set()
            
            # Also check country_entries for more detailed country mentions
            for entry in country_entries:
                if isinstance(entry, dict):
                    country = entry.get('country')
                    if country:
                        all_countries.add(country)
            
            # Validate each country
            for country in all_countries:
                is_registered = parser.is_registered(fund_name, country)
                
                if not is_registered:
                    # Find where this country was mentioned for better location info
                    location = "Document"
                    context_snippet = ""
                    
                    for entry in country_entries:
                        if isinstance(entry, dict) and entry.get('country') == country:
                            heading = entry.get('heading', '')
                            snippet = entry.get('snippet', '')
                            if heading:
                                location = f"{heading}"
                            context_snippet = snippet[:200] if snippet else ""
                            break
                    
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.UNREGISTERED_COUNTRY,
                        rule_reference="Country Registration",
                        location=location,
                        severity="error",
                        message=f"Document mentions '{country}' but fund '{fund_name}' is not registered for distribution in this country.",
                        context=f"Country mentioned: {country}. {context_snippet[:100] if context_snippet else ''}",
                        suggestion=f"Either remove country mention or register the fund in {country} before distribution",
                        client_type=client_type,
                        country=country,
                        fund_type=fund_type
                    ))
        
        except ImportError:
            # Registration parser not available
            pass
        except Exception as e:
            # Log error but don't fail validation
            print(f"Warning: Country registration validation failed: {e}")
        
        return issues

    def _generate_summary(self, result: DataConsistencyResult) -> List[str]:
        """Generate human-readable summary of validation results."""
        summary = []
        
        # Group issues by category
        issues_by_category = {}
        for issue in result.compliance_issues:
            category = issue.issue_category
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)
        
        # Source/Date summary
        if result.total_tables_checked > 0:
            summary.append(
                f"Source/Date Validation: {result.tables_with_source_date}/{result.total_tables_checked} "
                f"tables have complete source and date information"
            )
            if result.tables_missing_source_date > 0:
                summary.append(
                    f"WARNING: {result.tables_missing_source_date} table(s) missing source/date information"
                )
            if 'source_date' in issues_by_category:
                error_count = sum(1 for issue in issues_by_category['source_date'] if issue.severity == "error")
                warning_count = len(issues_by_category['source_date']) - error_count
                if error_count > 0:
                    summary.append(f"ERROR: {error_count} source/date error(s) found")
                if warning_count > 0:
                    summary.append(f"WARNING: {warning_count} source/date warning(s) found")
        
        # Numerical validation summary
        if result.total_numerical_values_checked > 0:
            summary.append(
                f"Numerical Validation: {result.values_matching_reference}/{result.total_numerical_values_checked} "
                f"values match reference documents"
            )
            if result.values_with_inconsistencies > 0:
                summary.append(
                    f"WARNING: {result.values_with_inconsistencies} value(s) have inconsistencies"
                )
            if 'numerical' in issues_by_category:
                error_count = sum(1 for issue in issues_by_category['numerical'] if issue.severity == "error")
                warning_count = len(issues_by_category['numerical']) - error_count
                if error_count > 0:
                    summary.append(f"ERROR: {error_count} numerical inconsistency/ies")
                if warning_count > 0:
                    summary.append(f"WARNING: {warning_count} numerical warning(s)")
        
        # Cross-reference validation summary
        if 'cross_reference' in issues_by_category:
            error_count = sum(1 for issue in issues_by_category['cross_reference'] if issue.severity == "error")
            warning_count = len(issues_by_category['cross_reference']) - error_count
            if error_count > 0:
                summary.append(f"ERROR: {error_count} cross-reference error(s) found")
            if warning_count > 0:
                summary.append(f"WARNING: {warning_count} cross-reference warning(s) found")
        
        # ESG validation summary
        if 'esg' in issues_by_category:
            critical_count = sum(1 for issue in issues_by_category['esg'] if issue.severity == "critical")
            error_count = sum(1 for issue in issues_by_category['esg'] if issue.severity == "error")
            warning_count = len(issues_by_category['esg']) - critical_count - error_count
            if critical_count > 0:
                summary.append(f"CRITICAL: {critical_count} ESG compliance issue(s)")
            if error_count > 0:
                summary.append(f"ERROR: {error_count} ESG error(s)")
            if warning_count > 0:
                summary.append(f"WARNING: {warning_count} ESG warning(s)")
        
        # Other compliance issues
        other_categories = [cat for cat in issues_by_category if cat not in ['source_date', 'numerical', 'cross_reference', 'esg']]
        if other_categories:
            for category in other_categories:
                issues = issues_by_category[category]
                critical_count = sum(1 for issue in issues if issue.severity == "critical")
                error_count = sum(1 for issue in issues if issue.severity == "error")
                warning_count = len(issues) - critical_count - error_count
                if critical_count > 0:
                    summary.append(f"CRITICAL: {critical_count} {category} issue(s)")
                if error_count > 0:
                    summary.append(f"ERROR: {error_count} {category} error(s)")
                if warning_count > 0:
                    summary.append(f"WARNING: {warning_count} {category} warning(s)")

        # Overall status
        if result.overall_status == "pass":
            summary.append("PASS: All validations passed")
        elif result.overall_status == "warning":
            summary.append("WARNING: Validation completed with warnings")
        elif result.overall_status == "critical":
            summary.append("CRITICAL: Validation found critical compliance violations")
        elif result.overall_status == "error":
            summary.append("ERROR: Validation found errors that require attention")
        
        return summary


def create_reference_data_from_dict(data: Dict[str, Any]) -> ReferenceData:
    """
    Helper function to create ReferenceData from a dictionary.
    
    Example:
        data = {
            'fund_name': 'ODDO BHF Algo Trend US',
            'isin': 'FR0012345678',
            'performance_data': {
                '1Y': {'net': 10.5, 'gross': 12.0},
                '3Y': {'net': 8.2}
            },
            'table_data': {
                'fund': 10.5,
                'benchmark': 8.0
            },
            'reference_date': '2025-08-31',
            'source_document': 'Prospectus'
        }
    """
    return ReferenceData(**data)

