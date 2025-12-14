"""
Data Consistency Agent (Refactored)
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..rules.models import ComplianceIssue, ValidationResult
from .models import DataConsistencyResult
from ..rules.enums import ComplianceIssueType, ClientType, FundType

# Import new validators
from ..validators.fund_type import FundTypeValidator
from ..validators.disclaimer import DisclaimerValidator
from ..validators.performance import PerformanceValidator
from ..validators.country import CountryValidator
from ..validators.content import ContentValidator
from ..validators.esg_compliance import EsgValidator
from ..validators.esg.analyzer import ESGAnalyzer

logger = logging.getLogger(__name__)

class DataConsistencyAgent:
    """
    Agent responsible for checking data consistency and compliance rules.
    Refactored to use modular validators.
    """
    
    def __init__(self, enable_esg_validation: bool = True):
        self.enable_esg_validation = enable_esg_validation
        
        # Initialize ESG Analyzer if enabled
        self.esg_analyzer = None
        if enable_esg_validation:
            try:
                self.esg_analyzer = ESGAnalyzer()
                logger.info("[OK] ESG Analyzer initialized for DataConsistencyAgent")
            except Exception as e:
                logger.error(f"[FAIL] Failed to initialize ESG Analyzer: {e}")
                
        # Initialize Validators
        self.validators = [
            FundTypeValidator(),
            DisclaimerValidator(),
            PerformanceValidator(),
            CountryValidator(),
            ContentValidator(),
            EsgValidator(esg_analyzer=self.esg_analyzer, enable_esg_validation=enable_esg_validation)
        ]

    def validate(
        self, 
        extraction_result: Dict[str, Any], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataConsistencyResult:
        """
        Main validation entry point. Check all rules.
        """
        issues: List[ComplianceIssue] = []
        
        # 1. Determine Client Type and Fund Type
        client_type = self._determine_client_type(extraction_result, metadata)
        fund_type = self._determine_fund_type(extraction_result, metadata)
        
        logger.info(f"Starting validation for Client: {client_type}, Fund: {fund_type}")
        
        # 2. Run all validators
        for validator in self.validators:
            try:
                validator_issues = validator.validate(
                    extraction_result, 
                    metadata, 
                    client_type=client_type, 
                    fund_type=fund_type
                )
                issues.extend(validator_issues)
            except Exception as e:
                logger.error(f"Error in validator {validator.__class__.__name__}: {e}")
                # We don't stop everything if one validator fails
        
        # 3. Aggregate results
        # Calculate status based on max severity
        status = "compliant"
        has_errors = False
        has_warnings = False
        max_severity = 0
        
        for issue in issues:
            if issue.severity == "critical":
                max_severity = max(max_severity, 4)
                has_errors = True
            elif issue.severity == "error":
                max_severity = max(max_severity, 3)
                has_errors = True
            elif issue.severity == "warning":
                max_severity = max(max_severity, 2)
                has_warnings = True
            elif issue.severity == "info":
                max_severity = max(max_severity, 1)
                
        if max_severity >= 3:
            status = "non_compliant"
        elif max_severity == 2:
            status = "warning"
            
        # Get simplified summary
        summary = [f"Found {len(issues)} issues."]
        
        # ESG data for result
        esg_data = None
        if self.enable_esg_validation and self.validators[-1].__class__.__name__ == 'EsgValidator':
            # EsgValidator stores cache in _esg_analysis_cache
             try:
                 esg_data = getattr(self.validators[-1], '_esg_analysis_cache', None)
             except:
                 pass

        return DataConsistencyResult(
            document_id=metadata.get('document_id') if metadata else None,
            validation_timestamp=datetime.utcnow().isoformat() + "Z",
            compliance_issues=issues,
            overall_status=status,
            has_errors=has_errors,
            has_warnings=has_warnings,
            summary=summary,
            esg_analysis=esg_data,
            # Fill other fields with defaults or calculate if possible
            total_tables_checked=0, # Metrics not yet migrated to new structure completely
            tables_with_source_date=0,
            tables_missing_source_date=0,
            countries_checked=[],
            countries_authorized=[]
        )
    
    def _determine_client_type(self, extraction_result: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> ClientType:
        """Determine if document is for Retail or Professional clients."""
        # Check metadata first
        if metadata and metadata.get('target_audience'):
            audience = metadata.get('target_audience', '').lower()
            if 'professional' in audience or 'institution' in audience:
                return ClientType.PROFESSIONAL
            if 'retail' in audience or 'detail' in audience or 'privat' in audience:
                return ClientType.RETAIL
        
        # Check content
        all_text = ""
        if 'pages' in extraction_result:
            for page in extraction_result['pages']:
                all_text += " " + page.get('content', '')
        elif 'slides' in extraction_result:
            for slide in extraction_result['slides']:
                if isinstance(slide, dict):
                    all_text += " " + (slide.get('content', '') or slide.get('text', ''))
                elif isinstance(slide, str):
                    all_text += " " + slide
        
        all_text_lower = all_text.lower()
        
        if 'professional client' in all_text_lower or 'client professionnel' in all_text_lower or 'professioneller kunde' in all_text_lower:
            return ClientType.PROFESSIONAL
        
        if 'retail client' in all_text_lower or 'client de détail' in all_text_lower or 'privatanleger' in all_text_lower:
            return ClientType.RETAIL
            
        # Default to Retail (strictest)
        return ClientType.RETAIL

    def _determine_fund_type(self, extraction_result: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> FundType:
        """Determine fund type (Equity, Bond, ETF, etc.)."""
        # Check metadata
        if metadata and metadata.get('fund_type'):
            ft_str = metadata.get('fund_type', '').lower()
            if 'etf' in ft_str: return FundType.ETF
            if 'bond' in ft_str or 'oblig' in ft_str or 'rent' in ft_str: return FundType.BOND
            if 'equity' in ft_str or 'action' in ft_str or 'aktien' in ft_str: return FundType.EQUITY
            if 'money market' in ft_str or 'monétaire' in ft_str or 'geldmarkt' in ft_str: return FundType.MONEY_MARKET
            if 'private equity' in ft_str: return FundType.PRIVATE_EQUITY
            if 'real estate' in ft_str or 'immobilie' in ft_str: return FundType.REAL_ESTATE
            
        # Check content
        all_text = ""
        if 'pages' in extraction_result:
            for page in extraction_result['pages']:
                all_text += " " + page.get('content', '')
        elif 'slides' in extraction_result:
            for slide in extraction_result['slides']:
                if isinstance(slide, dict):
                    all_text += " " + (slide.get('content', '') or slide.get('text', ''))
                elif isinstance(slide, str):
                    all_text += " " + slide
        
        all_text_lower = all_text.lower()
        
        if 'etf' in all_text_lower or 'exchange traded fund' in all_text_lower:
            return FundType.ETF
        if 'private equity' in all_text_lower:
            return FundType.PRIVATE_EQUITY
        if 'money market' in all_text_lower or 'marché monétaire' in all_text_lower or 'geldmarkt' in all_text_lower:
            return FundType.MONEY_MARKET
            
        return FundType.STANDARD
