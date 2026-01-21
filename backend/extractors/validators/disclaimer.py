"""
Disclaimer Validator
"""
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType
from .base import BaseValidator
from .utils import infer_last_slide, infer_performance_slide


class DisclaimerValidator(BaseValidator):
    """Validator for disclaimer rules using glossary_disclaimers.json as source of truth."""
    
    def __init__(self):
        """Initialize validator with glossary manager."""
        self.glossary_manager = None
        try:
            from backend.extractors.utils.glossary_manager import GlossaryManager
            self.glossary_manager = GlossaryManager()
        except Exception as e:
            print(f"Warning: Could not initialize glossary manager: {e}")
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
        # Get document text
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
        
        # Determine language and client type
        language = metadata.get('language', 'ENGLISH').upper() if metadata else 'ENGLISH'
        is_professional = client_type == ClientType.PROFESSIONAL
        client_type_str = "professional" if is_professional else "non_professional"
        
        # Get required disclaimers from glossary
        if self.glossary_manager:
            required_disclaimers = self.glossary_manager.get_required_disclaimers(
                language=language,
                client_type=client_type_str
            )
            
            # Verify each required disclaimer is present
            for disclaimer_type, disclaimer_text in required_disclaimers.items():
                found, similarity = self.glossary_manager.verify_disclaimer_presence(
                    all_text,
                    disclaimer_type,
                    language=language,
                    client_type=client_type_str,
                    min_similarity=0.7
                )
                
                if not found:
                    # Determine severity based on disclaimer type
                    severity = "critical" if any(critical in disclaimer_type.lower() for critical in ['capital', 'performance', 'standard', 'obam']) else "warning"
                    
                    # Create more granular location based on disclaimer type
                    if 'capital' in disclaimer_type.lower():
                        location = "Slide 2 - Risk Factors & Disclaimer box"
                        rule_ref = "Rule 39 - Capital Loss Disclosure"
                    elif 'performance' in disclaimer_type.lower():
                        perf_slide = infer_performance_slide(extraction_result) or 4
                        location = f"Slide {perf_slide} - Performance table footer"
                        rule_ref = "Rule 45 - Past Performance Disclaimer"
                    elif 'obam' in disclaimer_type.lower():
                        location = "Slide 1 - Cover Page / Key Information"
                        rule_ref = "Rule 27 - Management Company Disclosure"
                    else:
                        location = "Slide 2 - Standard Disclaimer section"
                        rule_ref = f"Rule - {disclaimer_type} Disclaimer"
                    
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.MISSING_RETAIL_DISCLAIMER if not is_professional else ComplianceIssueType.MISSING_PROFESSIONAL_DISCLAIMER,
                        rule_reference=rule_ref,
                        location=location,
                        slide_number=int(location.split()[1]) if 'Slide' in location else 2,
                        severity=severity,
                        message=f"Required disclaimer '{disclaimer_type}' not found in document.",
                        context=f"The mandatory {disclaimer_type} disclosure is missing from the document content. This is a regulatory requirement.",
                        suggestion=f"Add the following text to {location}: '{disclaimer_text[:100]}...'",
                        client_type=client_type,
                        fund_type=fund_type
                    ))
        
        # Legacy fallback checks (if glossary not available)
        disclaimers_found = extraction_result.get('disclaimers', [])
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
                rule_reference="Rule 39 - Capital Loss Disclosure",
                location="Slide 2 - Risk Factors & Disclaimer box",
                slide_number=2,
                severity="error",
                message="Warning about 'Risk of Capital Loss' (Risque de perte en capital) is missing. It is mandatory on Slide 2.",
                context="No capital loss warning found in disclaimers or risk factors section",
                suggestion="Add warning on Slide 2 Risk Factors: 'Capital is not guaranteed and you may not get back the amount you invested'",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        # Check for Past Performance warning if performance is shown
        has_performance = bool(extraction_result.get('performance_sections') or extraction_result.get('performance_table_entries'))
        if has_performance:
            if "performances passées" not in full_disclaimer_text and "past performance" not in full_disclaimer_text:
                 perf_slide = infer_performance_slide(extraction_result) or infer_last_slide(extraction_result) or 3
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_PERFORMANCE_DISCLAIMER,
                    rule_reference="Rule 45 - Past Performance Disclaimer",
                    location=f"Slide {perf_slide} - Performance table footer or disclaimer section",
                    slide_number=perf_slide,
                    severity="error",
                    message="Warning that 'Past performance is not a reliable indicator of future results' is missing.",
                    context=f"Performance data shown on Slide {perf_slide} without past performance disclaimer",
                    suggestion=f"Add disclaimer below performance table on Slide {perf_slide}: 'Past performance is not a reliable indicator of future results. The value of the investment may fall as well as rise'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        return issues
