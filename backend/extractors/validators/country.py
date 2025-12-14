"""
Country Validator
"""
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType, FundType
from .base import BaseValidator

class CountryValidator(BaseValidator):
    """Validator for country registration and specific country rules (e.g., Germany)."""
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues = []
        issues.extend(self._validate_germany_specific_rules(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_country_registration_rules(extraction_result, metadata, client_type, fund_type))
        return issues

    def _validate_germany_specific_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
        # Check if Germany is relevant for this document
        countries_detected = set(extraction_result.get('structure', {}).get('countries_detected', []))
        country_entries = extraction_result.get('country_entries', [])
        for entry in country_entries:
            if isinstance(entry, dict) and entry.get('country'):
                countries_detected.add(entry.get('country').lower())
        
        is_german_language = metadata and metadata.get('language') == 'de'
        is_germany_target = 'germany' in countries_detected or 'allemagne' in countries_detected or 'deutschland' in countries_detected
        
        if not (is_german_language or is_germany_target):
            return issues
            
        # Get text content
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
        
        # Get disclaimers
        disclaimers_found = extraction_result.get('disclaimers', [])
        disclaimer_texts = []
        for d in disclaimers_found:
            if isinstance(d, str):
                disclaimer_texts.append(d.lower())
            elif isinstance(d, dict):
                disclaimer_texts.append(d.get('text', '').lower())
        full_disclaimer_text = " ".join(disclaimer_texts)
        
        # Rule 1: NAV Format (Must be indicative)
        nav_keywords = ["net asset value", "nettoinventarwert", "valeur nette d'inventaire", " nav "]
        has_nav = any(keyword in all_text_lower for keyword in nav_keywords)
        
        if has_nav:
            indicative_keywords = ["indicative", "indikativ", "estimation", "schätzung"]
            has_indicative_disclaimer = any(keyword in full_disclaimer_text for keyword in indicative_keywords)
            
            if not has_indicative_disclaimer:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.NAV_FORMAT_ISSUE,
                    rule_reference="Germany Specific",
                    location="Content",
                    severity="warning",
                    message="NAV is mentioned but not labeled as 'indicative' or with a disclaimer stating it is for indicative purposes only (Germany rule).",
                    suggestion="Ensure NAV is labeled as 'indicative' or add disclaimer: 'The Net Asset Value is provided for indicative purposes only.'",
                    client_type=client_type,
                    fund_type=fund_type
                ))

        # Rule 2: Subscription/Redemption Fees (Unknown NAV disclaimer)
        fee_keywords = [
            "subscription fee", "ausgabeaufschlag", "frais de souscription",
            "redemption fee", "rücknahmeabschlag", "frais de rachat",
            "entry charge", "exit charge"
        ]
        has_fees = any(keyword in all_text_lower for keyword in fee_keywords)
        
        if has_fees:
            unknown_nav_keywords = [
                "unknown net asset value", "unbekannten inventarwert", "valeur inconnue",
                "unknown nav", "unbekanntem niw", "unknown price", "unbekanntem preis"
            ]
            has_unknown_nav_disclaimer = any(keyword in full_disclaimer_text for keyword in unknown_nav_keywords)
            
            if not has_unknown_nav_disclaimer:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_UNKNOWN_NAV_DISCLAIMER,
                    rule_reference="Germany Specific",
                    location="Fees Section",
                    severity="warning",
                    message="Subscription/Redemption fees mentioned without 'Unknown NAV' disclaimer (Germany rule).",
                    suggestion="Add disclaimer: 'Subscriptions and redemptions are processed at an unknown Net Asset Value.'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
                
        # Rule 3: German Specific Disclaimer (Rebates/Compensation)
        if is_germany_target:
            # Check if the standard long German disclaimer is present (checking a unique substring)
            german_disclaimer_substrings = [
                "receives any rebates on the management fee", 
                "erhält rückvergütungen aus der verwaltungsvergütung",
                "performs services for an investment product",
                "erbringt dienstleistungen für ein anlageprodukt"
            ]
            
            has_german_disclaimer = any(sub in full_disclaimer_text for sub in german_disclaimer_substrings)
            
            if not has_german_disclaimer:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_GERMAN_SPECIFIC_DISCLAIMER,
                    rule_reference="Germany Specific",
                    location="Disclaimers",
                    severity="warning",
                    message="Document targets Germany but seems to miss the specific German disclaimer regarding rebates/inducements.",
                    suggestion="Add the standard German disclaimer regarding management fee rebates and inducements.",
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
            from backend.extractors.parsers.registration.registration_parser import RegistrationParser
            
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
