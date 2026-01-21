"""
Country Validator
"""
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType
from .base import BaseValidator
from .utils import infer_last_slide, infer_slide_containing_text

class CountryValidator(BaseValidator):
    """Validator for country registration and specific country rules (e.g., Germany)."""
    
    def __init__(self):
        """Initialize validator with registration parser."""
        self.registration_parser = None
        try:
            from backend.extractors.parsers.registration.registration_parser import RegistrationParser
            self.registration_parser = RegistrationParser()
        except Exception:
            pass  # Parser not available
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues = []
        issues.extend(self._validate_germany_specific_rules(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_slide_2_countries(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_country_registration_rules(extraction_result, metadata, client_type, fund_type))
        return issues

    def _validate_slide_2_countries(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """Validate that countries listed on Slide 2 match registration registry.
        
        Oddo BHF Requirement (Slide 2 / Section 3):
        - Must include marketing countries
        - Countries must match "Registration abroad of Funds" Excel file
        """
        issues: List[ComplianceIssue] = []
        
        if not self.registration_parser:
            return issues  # Parser not available
        
        # Get fund name for lookup
        fund_name = None
        if metadata:
            fund_name = metadata.get('fund_name') or metadata.get('title_information', {}).get('fund_name')
        
        if not fund_name:
            return issues  # Can't validate without fund name
        
        # Get Slide 2 (index 1)
        slides = extraction_result.get('slides', [])
        if len(slides) < 2:
            return issues  # Not enough slides
        
        slide_2 = slides[1]
        if not isinstance(slide_2, dict):
            slide_2 = {'content': str(slide_2)}
        
        slide_2_text = (slide_2.get('content', '') or slide_2.get('text', '') or '').lower()
        
        # Extract countries from Slide 2
        countries_on_slide_2 = set()
        country_entries = extraction_result.get('country_entries', [])
        
        # Look for countries mentioned specifically on Slide 2
        for entry in country_entries:
            if isinstance(entry, dict):
                # Check if this entry is from Slide 2
                if entry.get('slide_number') == 2 or entry.get('location', '').startswith('Slide 2'):
                    country = entry.get('country', '').strip()
                    if country:
                        countries_on_slide_2.add(country)
        
        # Also use keyword detection for common country mentions on Slide 2
        country_keywords = {
            'france': ['france', 'français', 'frankreich'],
            'germany': ['germany', 'deutschland', 'allemagne', 'german'],
            'belgium': ['belgium', 'belgien', 'belgique'],
            'switzerland': ['switzerland', 'suisse', 'schweiz', 'swiss'],
            'italy': ['italy', 'italia', 'italien'],
            'spain': ['spain', 'españa', 'spanien'],
            'netherlands': ['netherlands', 'pays-bas', 'niederlande'],
            'united kingdom': ['united kingdom', 'uk', 'england', 'british'],
            'united states': ['united states', 'usa', 'us', 'america'],
            'canada': ['canada', 'canadian'],
            'austria': ['austria', 'österreich'],
            'luxembourg': ['luxembourg', 'luxemburg'],
        }
        
        for country, keywords in country_keywords.items():
            for keyword in keywords:
                if keyword in slide_2_text:
                    countries_on_slide_2.add(country)
                    break
        
        # Validate each country on Slide 2
        for country in countries_on_slide_2:
            try:
                is_registered = self.registration_parser.is_registered(fund_name, country)
                
                if not is_registered:
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.UNREGISTERED_COUNTRY,
                        rule_reference="Rule 52 - Country Registration", 
                        location="Slide 2 - Fund Registration Countries list",
                        slide_number=2,
                        severity="error",
                        message=f"Slide 2 mentions '{country}' but fund '{fund_name}' is NOT registered for distribution in {country}.",
                        context=f"Unregistered country on Slide 2: {country}. Only authorized countries should be listed.",
                        suggestion=f"Remove '{country}' from Slide 2 OR register the fund in {country} before distribution",
                        client_type=client_type,
                        country=country,
                        fund_type=fund_type
                    ))
            except Exception:
                # Log but don't fail
                pass
        
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
                last_slide = infer_last_slide(extraction_result)
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.NAV_FORMAT_ISSUE,
                    rule_reference="Rule - Germany Specific (Indicative NAV)",
                    location=f"Slide {last_slide} - Fund Characteristics table, NAV row",
                    slide_number=last_slide,
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
                last_slide = infer_last_slide(extraction_result)
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_UNKNOWN_NAV_DISCLAIMER,
                    rule_reference="Rule - Germany Specific (Subscription Fees)",
                    location=f"Slide {last_slide} - General Characteristics / Fee section",
                    slide_number=last_slide,
                    severity="warning",
                    message="Subscription/Redemption fees mentioned without 'Unknown NAV' disclaimer (Germany rule).",
                    suggestion="Add disclaimer to Slide 6 Characteristics: 'Subscriptions and redemptions are processed at an unknown Net Asset Value.'",
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
                 last_slide = infer_last_slide(extraction_result)
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_GERMAN_SPECIFIC_DISCLAIMER,
                    rule_reference="Rule - Germany Specific (Inducements)",
                    location=f"Slide {last_slide} - Legal Disclaimers section (Germany)",
                    slide_number=last_slide,
                    severity="warning",
                    message="Document targets Germany but seems to miss the specific German disclaimer regarding rebates/inducements.",
                    suggestion=f"Add the standard German disclaimer to Slide {last_slide} regarding management fee rebates and inducements.",
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
                        slide_number=infer_slide_containing_text(extraction_result, [country]) or 1,
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
