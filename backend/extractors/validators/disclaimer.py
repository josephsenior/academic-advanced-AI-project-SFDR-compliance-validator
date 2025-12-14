"""
Disclaimer Validator
"""
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType
from .base import BaseValidator

class DisclaimerValidator(BaseValidator):
    """Validator for disclaimer rules."""
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
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
