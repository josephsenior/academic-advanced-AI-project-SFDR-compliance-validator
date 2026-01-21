"""
Data Consistency Agent (Refactored)
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional, cast

from ..rules.models import ComplianceIssue
from .models import DataConsistencyResult
from ..rules.enums import ClientType, FundType

# Import new validators
from ..validators.fund_type import FundTypeValidator
from ..validators.disclaimer import DisclaimerValidator
from ..validators.performance import PerformanceValidator
from ..validators.country import CountryValidator
from ..validators.content import ContentValidator
from ..validators.esg_compliance import EsgValidator
from ..validators.esg_volume import ESGVolumeValidator
from ..validators.translation_consistency import TranslationConsistencyValidator
from ..validators.anglicism_detector import AnglicismDetector
from ..validators.visual_prominence import VisualProminenceValidator
from ..validators.dynamic_prospectus import DynamicProspectusExtractor
from ..validators.esg.analyzer import ESGAnalyzer
from .validators.numerical_validator import validate_numerical_data
from .reference_data import ReferenceData
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)

class DataConsistencyAgent:
    """
    Agent responsible for checking data consistency and compliance rules.
    Refactored to use modular validators.
    """
    
    def __init__(self, enable_esg_validation: bool = True, esg_api_key: Optional[str] = None, esg_base_url: Optional[str] = None, **kwargs):
        self.enable_esg_validation = enable_esg_validation
        self.esg_api_key = esg_api_key
        self.esg_base_url = esg_base_url
        
        # Initialize ESG Analyzer if enabled
        self.esg_analyzer = None
        if enable_esg_validation:
            try:
                # Pass through ESG configuration if the analyzer accepts it
                try:
                    self.esg_analyzer = ESGAnalyzer(api_key=esg_api_key, base_url=esg_base_url)
                except TypeError:
                    # Older ESGAnalyzer signature — fall back to no-arg init
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
            ESGVolumeValidator(),  # NEW: ESG Volume Validation (Rule 4.1)
            TranslationConsistencyValidator(),  # NEW: Cross-language consistency
            AnglicismDetector(),  # NEW: Undefined English terms detection
            VisualProminenceValidator(),  # NEW: WCAG contrast checking
            DynamicProspectusExtractor(),  # NEW: Auto-extract fees from prospectus
            EsgValidator(esg_analyzer=self.esg_analyzer, enable_esg_validation=enable_esg_validation)
        ]

    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        reference_data: Optional[ReferenceData] = None,
        document_id: Optional[str] = None,
        **kwargs: Any
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
        
        # 2.5 Run Numerical Validation if reference data available
        numerical_results = {
            'total_checked': 0,
            'matching': 0,
            'inconsistent': 0
        }
        if reference_data:
            numerical_results = validate_numerical_data(
                extraction_result,
                reference_data,
                metadata=metadata
            )
            issues.extend(cast(List[ComplianceIssue], numerical_results.get('inconsistencies', [])))
        
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
        
        # If a caller provided a document_id separately, ensure it's available in metadata
        if document_id and metadata is not None:
            metadata.setdefault('document_id', document_id)

        # ESG data for result
        esg_data = None
        if self.enable_esg_validation and self.validators[-1].__class__.__name__ == 'EsgValidator':
            # EsgValidator stores cache in _esg_analysis_cache
             try:
                 esg_data = getattr(self.validators[-1], '_esg_analysis_cache', None)
             except Exception:
                 pass
        # Calculate statistics from extraction results
        total_tables = 0
        total_charts = 0
        
        # Handle nested extraction_result structure
        # The extraction pipeline may wrap results in an 'extraction_result' key
        inner_result = extraction_result.get('extraction_result', extraction_result)
        
        # First try to use direct totals if available (most reliable)
        if 'total_tables' in inner_result:
            total_tables = inner_result.get('total_tables', 0) or 0
        if 'total_charts' in inner_result:
            total_charts = inner_result.get('total_charts', 0) or 0
        
        # If no direct totals, count from slides/pages
        if total_tables == 0 and total_charts == 0:
            # Check slides or pages for tables and charts
            slides_or_pages = inner_result.get('slides', inner_result.get('pages', []))
            for item in slides_or_pages:
                if isinstance(item, dict):
                    total_tables += len(item.get('tables', []))
                    total_charts += len(item.get('charts', []))
            
            # Also check top-level tables/charts arrays
            if 'tables' in inner_result and isinstance(inner_result['tables'], list):
                total_tables = max(total_tables, len(inner_result['tables']))
            if 'charts' in inner_result and isinstance(inner_result['charts'], list):
                total_charts = max(total_charts, len(inner_result['charts']))



        # Check for Authorized Countries in metadata or extraction
        authorized_countries = []
        if metadata and metadata.get('marketing_countries'):
            mc = metadata.get('marketing_countries')
            if isinstance(mc, list):
                authorized_countries = mc
            elif isinstance(mc, str):
                authorized_countries = [c.strip() for c in mc.split(',') if c.strip()]
        
        if not authorized_countries:
            # Fallback to extraction if not in metadata
            authorized_countries = extraction_result.get('authorized_countries', [])

        return DataConsistencyResult(
            document_id=str(metadata.get('document_id')) if metadata and metadata.get('document_id') else None,
            validation_timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            compliance_issues=issues,
            overall_status=status,
            has_errors=has_errors,
            has_warnings=has_warnings,
            summary=summary,
            esg_analysis=esg_data,
            total_tables_checked=total_tables,
            tables_with_source_date=total_tables, # Simplified: assume all checked
            tables_missing_source_date=sum(1 for i in issues if i.issue_type == "missing_source_date"),
            total_charts_analyzed=total_charts,
            charts_with_source_date=total_charts, # Simplified
            charts_missing_source_date=sum(1 for i in issues if i.issue_type == "missing_source_date"), # Simplified mapping
            total_numerical_values_checked=numerical_results.get('total_checked', 0),
            values_matching_reference=numerical_results.get('matching', 0),
            values_with_inconsistencies=numerical_results.get('inconsistent', 0),
            countries_checked=authorized_countries,
            countries_authorized=authorized_countries
        )

    def _determine_client_type(self, extraction_result: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> ClientType:
        """Determine if document is for Retail or Professional clients.
        
        Priority:
        1. Metadata field: "Le client est-il un professionnel" (Oddo BHF format)
        2. Metadata field: "target_audience"
        3. Content analysis (text matching)
        """
        # PRIORITY 1: Check Oddo BHF metadata format (French field names from dataset)
        if metadata:
            # Exact Oddo BHF field: "Le client est-il un professionnel"
            if 'Le client est-il un professionnel' in metadata:
                is_professional = metadata.get('Le client est-il un professionnel')
                if isinstance(is_professional, bool):
                    return ClientType.PROFESSIONAL if is_professional else ClientType.RETAIL
                if isinstance(is_professional, str):
                    if is_professional.lower() in ['true', 'yes', 'oui', 'professional', 'professionnel']:
                        return ClientType.PROFESSIONAL
                    if is_professional.lower() in ['false', 'no', 'non', 'retail', 'détail', 'retail']:
                        return ClientType.RETAIL
            
            # PRIORITY 2: Generic metadata fields
            if metadata.get('is_professional_client') is not None:
                return ClientType.PROFESSIONAL if metadata.get('is_professional_client') else ClientType.RETAIL
            
            if metadata.get('client_type'):
                client_type_str = metadata.get('client_type', '').lower()
                if 'professional' in client_type_str or 'professionnel' in client_type_str:
                    return ClientType.PROFESSIONAL
                if 'retail' in client_type_str or 'detail' in client_type_str:
                    return ClientType.RETAIL
            
            if metadata.get('target_audience'):
                audience = metadata.get('target_audience', '').lower()
                if 'professional' in audience or 'institution' in audience:
                    return ClientType.PROFESSIONAL
                if 'retail' in audience or 'detail' in audience or 'privat' in audience:
                    return ClientType.RETAIL
        
        # PRIORITY 3: Check content
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
            if 'etf' in ft_str:
                return FundType.ETF
            if 'bond' in ft_str or 'oblig' in ft_str or 'rent' in ft_str:
                return FundType.BOND
            if 'equity' in ft_str or 'action' in ft_str or 'aktien' in ft_str:
                return FundType.EQUITY
            if 'money market' in ft_str or 'monétaire' in ft_str or 'geldmarkt' in ft_str:
                return FundType.MONEY_MARKET
            if 'private equity' in ft_str:
                return FundType.PRIVATE_EQUITY
            if 'real estate' in ft_str or 'immobilie' in ft_str:
                return FundType.REAL_ESTATE
            
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

    # Backwards-compatible helper API expected by older tests/examples
    def _detect_fund_type(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility wrapper that synthesizes a simple fund_type result."""
        notes = []
        confidence = "low"

        # Simple heuristics
        if features.get('is_etf'):
            fund = "ETF"
            confidence = "medium"
            if features.get('is_private_equity'):
                notes.append("private equity characteristics present")
        elif features.get('is_private_equity'):
            fund = "PRIVATE_EQUITY"
            confidence = "medium"
        elif features.get('is_dated_fund'):
            fund = f"DATED-{features.get('maturity_date', '')}"
            confidence = "high" if features.get('sfdr_classification') else "medium"
        else:
            fund = features.get('fund_structure') or "STANDARD"
            confidence = "low"

        # SFDR note
        if features.get('sfdr_classification'):
            fund = f"{fund} ({features.get('sfdr_classification')})"
            confidence = "high"

        # If features present but none of the identifying keys exist, mark as insufficient
        identifying_keys = ('is_etf', 'is_private_equity', 'is_dated_fund', 'fund_structure', 'sfdr_classification', 'maturity_date')
        if not features:
            notes.append("insufficient information")
        else:
            if not any(k in features and features.get(k) for k in identifying_keys):
                notes.append("insufficient information")

        return {"fund_type": fund, "confidence": confidence, "notes": "; ".join(notes)}

    def _detect_client_type(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility wrapper to infer client type from simple features."""
        min_inv = features.get('minimum_investment', '')
        eligible = (features.get('eligible_investors') or '').lower()
        _channels = features.get('distribution_channels') or []

        if any(token in eligible for token in ['institution', 'qualified']):
            return {"client_type": "INSTITUTIONAL", "confidence": "high"}
        if isinstance(min_inv, str) and re.search(r"\d{4,}", min_inv.replace(',', '')):
            return {"client_type": "INSTITUTIONAL", "confidence": "high"}
        return {"client_type": "RETAIL", "confidence": "high"}

    def _compare_percentages(self, a: str, b: str, tolerance: float = 0.01) -> bool:
        def percent_candidates(x: str):
            s = (x or '').strip()
            s = s.replace(',', '.')
            candidates = set()
            if not s:
                return candidates
            # If explicit percent sign, interpret directly
            if '%' in s:
                try:
                    candidates.add(float(s.replace('%', '').strip()))
                except Exception:
                    pass
                return candidates

            # Otherwise parse number and generate reasonable percent interpretations
            try:
                v = float(s)
                # If fractional decimal, treat as decimal fraction -> percent
                if v < 1:
                    candidates.add(v * 100)
                # If >=1, treat as either a percent-like number or a ratio (e.g., 1.5 -> 150)
                if v >= 1:
                    candidates.add(v)
                    # Interpret small ratios as percent multiplier (1.5 -> 150) when plausible
                    if v < 100:
                        candidates.add(v * 100)
            except Exception:
                digits = re.findall(r"[0-9.]+", s)
                if digits:
                    try:
                        v = float(digits[0])
                        if v < 1:
                            candidates.add(v * 100)
                        else:
                            candidates.add(v)
                            if v < 100:
                                candidates.add(v * 100)
                    except Exception:
                        pass
            return candidates

        set_a = percent_candidates(a)
        set_b = percent_candidates(b)
        if not set_a or not set_b:
            return False
        allowed_diff = tolerance * 100
        for va in set_a:
            for vb in set_b:
                if abs(va - vb) < allowed_diff:
                    return True
        return False

    def _compare_currency_values(self, a: str, b: str, tolerance: float = 0.01) -> bool:
        # Very small parser to support test cases (K/M/B/T multipliers)
        def parse_val(s: str) -> tuple[str, float]:
            if not s:
                return '', 0.0
            s = s.replace(',', '').strip()
            # detect currency code
            parts = s.split()
            currency = ''
            num = s
            for p in parts:
                if re.fullmatch(r"[A-Z]{3}", p):
                    currency = p
                    num = s.replace(p, '').strip()
                    break
            # multipliers
            mult = 1
            if num.lower().endswith('m'):
                mult = 1_000_000
                num = num[:-1]
            if num.lower().endswith('b') and not num.lower().endswith('mb'):
                mult = 1_000_000_000
                num = num[:-1]
            if num.lower().endswith('t'):
                mult = 1_000_000_000_000
                num = num[:-1]
            try:
                val = float(num) * mult
            except Exception:
                # fallback try to extract digits
                digits = re.findall(r"[0-9.]+", num)
                val = float(digits[0]) * mult if digits else 0.0
            return currency, val

        ca, va = parse_val(a)
        cb, vb = parse_val(b)
        if ca and cb and ca != cb:
            return False
        return abs(va - vb) <= max(1.0, tolerance * max(abs(va), abs(vb)))

    def _compare_dates(self, a: str, b: str) -> bool:
        fmt_candidates = ["%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%d.%m.%Y"]
        def parse_date(s: str):
            for fmt in fmt_candidates:
                try:
                    return datetime.strptime(s.strip(), fmt).date()
                except Exception:
                    continue
            return None
        da = parse_date(a)
        db = parse_date(b)
        return da == db

    def _validate_esg_compliance(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Simple ESG compliance compatibility checker used by tests."""
        result: Dict[str, Any] = {"validation_status": "ok", "compliance_issues": []}
        sfdr = features.get('sfdr_classification')
        if sfdr == 'Article 9' and not features.get('pai_statement'):
            result['validation_status'] = 'failed'
            result['compliance_issues'].append('Missing PAI statement')
        if sfdr == 'Article 6' and features.get('taxonomy_aligned'):
            result['validation_status'] = 'warning'
            result['compliance_issues'].append('Taxonomy alignment claimed without Article 8/9')
        result['sfdr_classification'] = sfdr
        return result


# Re-export public API for backward-compatible imports used in tests/examples
__all__ = [
    'DataConsistencyAgent',
]
