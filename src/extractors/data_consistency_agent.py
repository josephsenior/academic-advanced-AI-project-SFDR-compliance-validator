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
from datetime import datetime, date
from dateutil import parser as date_parser


class SourceDateIssue(BaseModel):
    """Issue with missing or incomplete source/date information"""
    issue_type: str = Field(description="Type of issue: 'missing_source', 'missing_date', 'both_missing', 'invalid_date_format', 'date_too_old', 'date_inconsistent'")
    location: str = Field(description="Location in document (slide/page number, table index)")
    table_index: Optional[int] = Field(None, description="Table index if applicable")
    slide_number: Optional[int] = Field(None, description="Slide number if applicable")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    severity: str = Field(default="error", description="Severity: 'error' or 'warning'")
    message: str = Field(description="Human-readable description of the issue")


class NumericalInconsistency(BaseModel):
    """Inconsistency found when comparing numerical data with reference documents"""
    data_type: str = Field(description="Type of data: 'performance', 'table_entry', 'other'")
    location: str = Field(description="Location in document")
    document_value: float = Field(description="Value found in the document")
    reference_value: Optional[float] = Field(None, description="Value from reference document (Prospectus/KID/SFDR)")
    reference_source: Optional[str] = Field(None, description="Source of reference value")
    period: Optional[str] = Field(None, description="Time period (e.g., '1Y', 'YTD')")
    basis: Optional[str] = Field(None, description="Basis: 'net', 'gross', 'backtest', 'simulation'")
    label: Optional[str] = Field(None, description="Label/description of the data point")
    severity: str = Field(default="error", description="Severity: 'error' or 'warning'")
    message: str = Field(description="Human-readable description of the inconsistency")
    tolerance: Optional[float] = Field(None, description="Allowed tolerance for numerical differences (percentage)")


class CrossReferenceIssue(BaseModel):
    """Issue found when cross-referencing data between different parts of the document"""
    issue_type: str = Field(description="Type: 'performance_mismatch', 'duplicate_inconsistency'")
    location: str = Field(description="Location in document")
    value1: Optional[float] = Field(None, description="First value")
    value2: Optional[float] = Field(None, description="Second value")
    location1: Optional[str] = Field(None, description="Location of first value")
    location2: Optional[str] = Field(None, description="Location of second value")
    period: Optional[str] = Field(None, description="Time period if applicable")
    severity: str = Field(default="error", description="Severity: 'error' or 'warning'")
    message: str = Field(description="Human-readable description of the issue")


class DataConsistencyResult(BaseModel):
    """Complete result of data consistency validation"""
    document_id: Optional[str] = Field(None, description="Document identifier")
    validation_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    # Source/Date validation results
    source_date_issues: List[SourceDateIssue] = Field(default_factory=list)
    total_tables_checked: int = Field(default=0)
    tables_with_source_date: int = Field(default=0)
    tables_missing_source_date: int = Field(default=0)
    
    # Numerical validation results
    numerical_inconsistencies: List[NumericalInconsistency] = Field(default_factory=list)
    total_numerical_values_checked: int = Field(default=0)
    values_matching_reference: int = Field(default=0)
    values_with_inconsistencies: int = Field(default=0)
    
    # Cross-reference validation results
    cross_reference_issues: List[CrossReferenceIssue] = Field(default_factory=list)
    
    # Disclaimer validation results (optional)
    disclaimer_validation: Optional[Dict[str, Any]] = Field(None, description="Disclaimer validation results if enabled")
    
    # Overall status
    has_errors: bool = Field(default=False)
    has_warnings: bool = Field(default=False)
    overall_status: str = Field(default="unknown", description="'pass', 'warning', 'error'")
    
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
        disclaimer_validator: Optional[Any] = None
    ):
        """
        Initialize the Data Consistency Agent.
        
        Args:
            reference_data: Optional reference data from official documents.
                          If None, numerical validation will be skipped.
            max_date_age_days: Maximum age in days for source dates (default: 365)
            enable_cross_reference: Enable cross-reference validation (default: True)
            enable_date_validation: Enable date format and recency validation (default: True)
        """
        self.reference_data = reference_data
        self.default_tolerance = 0.01  # 1% tolerance for numerical comparisons
        self.max_date_age_days = max_date_age_days
        self.enable_cross_reference = enable_cross_reference
        self.enable_date_validation = enable_date_validation
        self.enable_disclaimer_validation = enable_disclaimer_validation
        self.disclaimer_validator = disclaimer_validator
    
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
        
        # Step 1: Validate source and date for all tables/charts
        source_date_result = self._validate_source_and_date(extraction_result, metadata)
        result.source_date_issues = source_date_result['issues']
        result.total_tables_checked = source_date_result['total_tables']
        result.tables_with_source_date = source_date_result['tables_with_source_date']
        result.tables_missing_source_date = source_date_result['tables_missing_source_date']
        
        # Also validate charts (from chart analyzer)
        charts = extraction_result.get('charts', [])
        if charts:
            chart_validation = self._validate_charts(charts, metadata)
            result.source_date_issues.extend(chart_validation['issues'])
            result.total_tables_checked += chart_validation['total_charts']
            result.tables_with_source_date += chart_validation['charts_with_source_date']
            result.tables_missing_source_date += chart_validation['charts_missing_source_date']
        
        # Step 2: Validate numerical data against reference documents
        if self.reference_data:
            numerical_result = self._validate_numerical_data(extraction_result, metadata)
            result.numerical_inconsistencies = numerical_result['inconsistencies']
            result.total_numerical_values_checked = numerical_result['total_checked']
            result.values_matching_reference = numerical_result['matching']
            result.values_with_inconsistencies = numerical_result['inconsistent']
        else:
            result.summary.append("Reference data not provided; numerical validation skipped")
        
        # Step 3: Cross-reference validation (performance in text vs tables)
        if self.enable_cross_reference:
            cross_ref_result = self._validate_cross_references(extraction_result)
            result.cross_reference_issues = cross_ref_result['issues']
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
        
        # Step 5: Determine overall status
        result.has_errors = (
            any(issue.severity == "error" for issue in result.source_date_issues) or
            any(inc.severity == "error" for inc in result.numerical_inconsistencies) or
            any(issue.severity == "error" for issue in result.cross_reference_issues) or
            (result.disclaimer_validation and result.disclaimer_validation.get('has_errors', False))
        )
        result.has_warnings = (
            any(issue.severity == "warning" for issue in result.source_date_issues) or
            any(inc.severity == "warning" for inc in result.numerical_inconsistencies) or
            any(issue.severity == "warning" for issue in result.cross_reference_issues) or
            (result.disclaimer_validation and result.disclaimer_validation.get('has_warnings', False))
        )
        
        if result.has_errors:
            result.overall_status = "error"
        elif result.has_warnings:
            result.overall_status = "warning"
        else:
            result.overall_status = "pass"
        
        # Step 6: Generate summary
        result.summary.extend(self._generate_summary(result))
        
        return result
    
    def _validate_source_and_date(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate that all tables/charts have source and date information.
        
        Returns:
            Dict with validation results
        """
        issues: List[SourceDateIssue] = []
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
                issues.append(SourceDateIssue(
                    issue_type="both_missing",
                    location=location_str,
                    table_index=table_idx,
                    slide_number=slide_num,
                    page_number=page_num,
                    severity="error",
                    message=f"Table at {location_str} is missing both source and date information"
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
                    issues.append(SourceDateIssue(
                        issue_type="both_missing",
                        location=location_str,
                        table_index=table_idx,
                        slide_number=slide_num,
                        page_number=page_num,
                        severity="error",
                        message=f"Table at {location_str} is missing both source and date"
                    ))
                elif not has_source:
                    issues.append(SourceDateIssue(
                        issue_type="missing_source",
                        location=location_str,
                        table_index=table_idx,
                        slide_number=slide_num,
                        page_number=page_num,
                        severity="error",
                        message=f"Table at {location_str} has date '{source_date}' but is missing source name"
                    ))
                elif not has_date:
                    issues.append(SourceDateIssue(
                        issue_type="missing_date",
                        location=location_str,
                        table_index=table_idx,
                        slide_number=slide_num,
                        page_number=page_num,
                        severity="error",
                        message=f"Table at {location_str} has source '{source_name}' but is missing date"
                    ))
        
        # Also check performance sections for source/date
        performance_sections = extraction_result.get('performance_sections', [])
        for section in performance_sections:
            slide_num = section.get('slide_number')
            page_num = section.get('page_number')
            location_key = (slide_num, page_num)
            
            if location_key not in source_map:
                location_str = self._format_location(slide_num, page_num, None)
                issues.append(SourceDateIssue(
                    issue_type="both_missing",
                    location=location_str,
                    slide_number=slide_num,
                    page_number=page_num,
                    severity="warning",
                    message=f"Performance section at {location_str} may need source and date verification"
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
        inconsistencies: List[NumericalInconsistency] = []
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
                    inconsistencies.append(NumericalInconsistency(
                        data_type="performance",
                        location=location_str,
                        document_value=value,
                        reference_value=None,
                        reference_source=self.reference_data.source_document,
                        period=period,
                        basis=basis,
                        severity="warning",
                        message=f"Performance value {value}% ({period}, {basis}) at {location_str} cannot be validated - no reference data available"
                    ))
                else:
                    # Compare values with tolerance
                    if self._values_match(value, ref_value, self.default_tolerance):
                        matching += 1
                    else:
                        diff = abs(value - ref_value)
                        diff_pct = (diff / abs(ref_value) * 100) if ref_value != 0 else float('inf')
                        inconsistencies.append(NumericalInconsistency(
                            data_type="performance",
                            location=location_str,
                            document_value=value,
                            reference_value=ref_value,
                            reference_source=self.reference_data.source_document,
                            period=period,
                            basis=basis,
                            severity="error",
                            message=f"Performance mismatch at {location_str}: document shows {value}% but reference shows {ref_value}% (difference: {diff_pct:.2f}%)",
                            tolerance=self.default_tolerance
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
                inconsistencies.append(NumericalInconsistency(
                    data_type="table_entry",
                    location=location_str,
                    document_value=value,
                    reference_value=None,
                    reference_source=self.reference_data.source_document,
                    label=label,
                    severity="warning",
                    message=f"Table entry '{label}' = {value}% at {location_str} cannot be validated - no reference data available"
                ))
            else:
                if self._values_match(value, ref_value, self.default_tolerance):
                    matching += 1
                else:
                    diff = abs(value - ref_value)
                    diff_pct = (diff / abs(ref_value) * 100) if ref_value != 0 else float('inf')
                    inconsistencies.append(NumericalInconsistency(
                        data_type="table_entry",
                        location=location_str,
                        document_value=value,
                        reference_value=ref_value,
                        reference_source=self.reference_data.source_document,
                        label=label,
                        severity="error",
                        message=f"Table entry mismatch at {location_str}: '{label}' shows {value}% but reference shows {ref_value}% (difference: {diff_pct:.2f}%)",
                        tolerance=self.default_tolerance
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
        
        # Try exact match first
        if period_lower in self.reference_data.performance_data:
            period_data = self.reference_data.performance_data[period_lower]
            if basis_lower and basis_lower in period_data:
                return period_data[basis_lower]
            # Try 'net' as default
            if 'net' in period_data:
                return period_data['net']
            # Return first available value
            if period_data:
                return list(period_data.values())[0]
        
        # Try fuzzy matching for period
        for ref_period, period_data in self.reference_data.performance_data.items():
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
    ) -> List[SourceDateIssue]:
        """
        Validate date format and check if date is too old or inconsistent with document date.
        
        Returns:
            List of SourceDateIssue objects (empty if no issues)
        """
        issues: List[SourceDateIssue] = []
        
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
            issues.append(SourceDateIssue(
                issue_type="invalid_date_format",
                location=location_str,
                table_index=table_idx,
                slide_number=slide_num,
                page_number=page_num,
                severity="error",
                message=f"Table at {location_str} has invalid date format: '{source_date}'"
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
            issues.append(SourceDateIssue(
                issue_type="date_too_old",
                location=location_str,
                table_index=table_idx,
                slide_number=slide_num,
                page_number=page_num,
                severity="warning",
                message=f"Table at {location_str} has source date {date_only} which is {days_old} days old (max: {self.max_date_age_days} days)"
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
                            issues.append(SourceDateIssue(
                                issue_type="date_inconsistent",
                                location=location_str,
                                table_index=table_idx,
                                slide_number=slide_num,
                                page_number=page_num,
                                severity="warning",
                                message=f"Table at {location_str} has source date {date_only} which is {days_diff} days after document date {doc_date_only}"
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
        issues: List[CrossReferenceIssue] = []
        
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
                        
                        issues.append(CrossReferenceIssue(
                            issue_type="performance_mismatch",
                            location=location_str,
                            value1=value,
                            value2=table_entry.get('value'),
                            location1=location_str,
                            location2=table_location,
                            period=period,
                            severity="error",
                            message=f"Performance mismatch: text shows {value}% ({period}, {basis}) at {location_str}, but table shows {table_entry.get('value')}% at {table_location}"
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
                    issues.append(CrossReferenceIssue(
                        issue_type="duplicate_inconsistency",
                        location=", ".join(locations),
                        value1=value,
                        value2=value,
                        location1=locations[0],
                        location2=locations[1] if len(locations) > 1 else None,
                        period=", ".join(set(periods)),
                        severity="warning",
                        message=f"Suspicious duplicate: value {value}% appears with different periods ({', '.join(set(periods))}) at {', '.join(locations)}"
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
                issues.append(SourceDateIssue(
                    issue_type="both_missing",
                    location=f"Chart at {location_str}",
                    slide_number=slide_num,
                    severity="error",
                    message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} is missing both source and date information"
                ))
            elif not has_source:
                issues.append(SourceDateIssue(
                    issue_type="missing_source",
                    location=f"Chart at {location_str}",
                    slide_number=slide_num,
                    severity="error",
                    message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} has date but is missing source name"
                ))
            elif not has_date:
                issues.append(SourceDateIssue(
                    issue_type="missing_date",
                    location=f"Chart at {location_str}",
                    slide_number=slide_num,
                    severity="error",
                    message=f"Chart '{chart.get('chart_title', 'Untitled')}' at {location_str} has source but is missing date"
                ))
        
        return {
            'issues': issues,
            'total_charts': total_charts,
            'charts_with_source_date': charts_with_source_date,
            'charts_missing_source_date': total_charts - charts_with_source_date
        }
    
    def _generate_summary(self, result: DataConsistencyResult) -> List[str]:
        """Generate human-readable summary of validation results."""
        summary = []
        
        # Source/Date summary
        if result.total_tables_checked > 0:
            summary.append(
                f"Source/Date Validation: {result.tables_with_source_date}/{result.total_tables_checked} "
                f"tables have complete source and date information"
            )
            if result.tables_missing_source_date > 0:
                summary.append(
                    f"⚠️  {result.tables_missing_source_date} table(s) missing source/date information"
                )
        
        # Numerical validation summary
        if result.total_numerical_values_checked > 0:
            summary.append(
                f"Numerical Validation: {result.values_matching_reference}/{result.total_numerical_values_checked} "
                f"values match reference documents"
            )
            if result.values_with_inconsistencies > 0:
                summary.append(
                    f"⚠️  {result.values_with_inconsistencies} value(s) have inconsistencies"
                )
        
        # Cross-reference validation summary
        if result.cross_reference_issues:
            error_count = sum(1 for issue in result.cross_reference_issues if issue.severity == "error")
            warning_count = len(result.cross_reference_issues) - error_count
            if error_count > 0:
                summary.append(f"❌ {error_count} cross-reference error(s) found")
            if warning_count > 0:
                summary.append(f"⚠️  {warning_count} cross-reference warning(s) found")
        
        # Overall status
        if result.overall_status == "pass":
            summary.append("✅ All validations passed")
        elif result.overall_status == "warning":
            summary.append("⚠️  Validation completed with warnings")
        elif result.overall_status == "error":
            summary.append("❌ Validation found errors that require attention")
        
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

