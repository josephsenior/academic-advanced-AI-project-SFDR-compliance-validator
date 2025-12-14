"""
Content Validator
"""
import re
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType
from .base import BaseValidator

class ContentValidator(BaseValidator):
    """Validator for content, general, cover page, and backtest rules."""
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues = []
        issues.extend(self._validate_general_rules(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_cover_page_rules(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_slide_2_rules(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_content_rules(extraction_result, metadata, client_type, fund_type))
        issues.extend(self._validate_backtest_simulation_rules(extraction_result, metadata, client_type, fund_type))
        return issues

    def _validate_general_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
        # Check for Glossary (Retail only)
        # We need to know if it's a retail document.
        # Assuming we can determine client type from metadata or default to retail if unknown for safety.
        current_client_type = client_type or ClientType.RETAIL # Default to retail for safety/strictness
        if metadata and metadata.get('target_audience'):
            if 'professional' in metadata['target_audience'].lower():
                current_client_type = ClientType.PROFESSIONAL
        
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

        if current_client_type == ClientType.RETAIL:
            if "glossaire" not in all_text_lower and "glossary" not in all_text_lower:
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

        # FWW Fundstars Rule
        if "fww" in all_text_lower or "fundstars" in all_text_lower:
            fww_disclaimer = "http://fww.de/disclaimer"
            if fww_disclaimer not in all_text_lower:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_FWW_DISCLAIMER,
                    rule_reference="Glossary - FWW",
                    location="Footnotes",
                    severity="warning",
                    message="FWW/Fundstars mentioned but source link/disclaimer missing.",
                    suggestion="Add: '* Source: FWW Fundservices GmbH... http://fww.de/disclaimer/.'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
                
        # New Offer Rule
        if "new offer" in all_text_lower or "nouvelle offre" in all_text_lower:
            # Check for capital loss risk
            risk_keywords = ["risk of capital loss", "risque de perte en capital", "kapitalverlustrisiko"]
            has_risk = any(k in all_text_lower for k in risk_keywords)
            if not has_risk:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_NEW_OFFER_DISCLAIMER,
                    rule_reference="Glossary - New Offer",
                    location="Disclaimers",
                    severity="error",
                    message="New Offer/Strategy mentioned but 'risk of capital loss' warning missing.",
                    suggestion="Add specific risk warnings for new offers including capital loss risk.",
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
        issues: List[ComplianceIssue] = []
        
        # Get cover page text (Slide 1)
        cover_text = ""
        if 'slides' in extraction_result and len(extraction_result['slides']) > 0:
            slide_1 = extraction_result['slides'][0]
            if isinstance(slide_1, dict):
                cover_text = slide_1.get('content', '') or slide_1.get('text', '')
            elif isinstance(slide_1, str):
                cover_text = slide_1
        elif 'pages' in extraction_result and len(extraction_result['pages']) > 0:
            cover_text = extraction_result['pages'][0].get('content', '') or extraction_result['pages'][0].get('text', '')
        elif extraction_result.get('cover_page_text'):
            cover_text = extraction_result['cover_page_text']
        
        cover_text_lower = cover_text.lower() if cover_text else ""
        title_info = metadata.get('title_information', {}) if metadata else {}
        
        # Rule 1: Fund Name
        if not title_info.get('fund_name'):
            fund_name_in_text = bool(cover_text and (
                'fund' in cover_text_lower or 
                'fonds' in cover_text_lower or
                title_info.get('fund_name', '').lower() in cover_text_lower
            ))
            if not fund_name_in_text:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_FUND_NAME,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="error",
                    message="Fund Name is missing on the cover page.",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 2: Document Date
        if not title_info.get('date') and not title_info.get('document_date'):
            date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}'
            has_date_in_text = bool(re.search(date_pattern, cover_text, re.IGNORECASE)) if cover_text else False
            if not has_date_in_text:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_DATE,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="error",
                    message="Document Date is missing on the cover page.",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 3: Promotional Mention
        promotional_mentions = [
            "document promotionnel", "promotional document", "werbedokument",
            "à caractère promotionnel", "marketing document", "zu werbezwecken",
            "marketing communication", "communication marketing"
        ]
        if cover_text_lower:
            has_promotional = any(mention in cover_text_lower for mention in promotional_mentions)
            if not has_promotional:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_PROMOTIONAL_MENTION,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="error",
                    message="Cover page must include a promotional mention (e.g., 'Document promotionnel', 'Marketing communication').",
                    suggestion="Add a phrase like 'Document promotionnel' or 'Marketing communication' to the cover page",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 4: Target Audience
        target_audience_phrases = [
            "client professionnel", "professional client", "professioneller kunde",
            "client de détail", "retail client", "privatanleger",
            "investisseur professionnel", "professional investor", "professioneller anleger",
            "investisseur de détail", "retail investor", "privatanleger"
        ]
        if cover_text_lower:
            has_target_audience = any(phrase in cover_text_lower for phrase in target_audience_phrases)
            has_target_audience_metadata = bool(metadata and metadata.get('target_audience'))
            if not has_target_audience and not has_target_audience_metadata:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_TARGET_AUDIENCE,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="warning",
                    message="Target audience (Professional/Retail) should be indicated on the cover page.",
                    suggestion="Add target audience indication (e.g., 'Professional Client' or 'Retail Client')",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 5: Premarketing Warning
        premarketing_phrases = [
            "document de pré-marketing", "pre-marketing document", "vormarketing-dokument",
            "documento de pre-marketing", "pré-marketing", "pre-marketing", "vormarketing"
        ]
        is_premarketing = any(phrase in cover_text_lower for phrase in premarketing_phrases) if cover_text_lower else False
        
        if is_premarketing:
            premarketing_warning_phrases = [
                "document de pré-marketing", "pre-marketing document", "vormarketing-dokument"
            ]
            has_warning = any(phrase in cover_text_lower for phrase in premarketing_warning_phrases)
            if not has_warning:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_PREMARKETING_WARNING,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="error",
                    message="Premarketing document must include a clear premarketing warning on the cover page.",
                    suggestion="Add explicit premarketing warning (e.g., 'Document de pré-marketing')",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 6: Do-Not-Disclose Notice
        do_not_disclose_phrases = [
            "ne pas diffuser", "do not disclose", "nicht weitergeben",
            "confidentiel", "confidential", "vertraulich",
            "ne pas communiquer", "do not communicate", "nicht kommunizieren"
        ]
        if cover_text_lower:
            has_do_not_disclose = any(phrase in cover_text_lower for phrase in do_not_disclose_phrases)
            is_confidential = bool(metadata and metadata.get('is_confidential', False))
            if is_confidential and not has_do_not_disclose:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_DO_NOT_DISCLOSE,
                    rule_reference="Section 2",
                    location="Slide 1",
                    severity="error",
                    message="Confidential document must include a 'Do Not Disclose' notice on the cover page.",
                    suggestion="Add confidentiality notice (e.g., 'Ne pas diffuser', 'Do not disclose', 'Confidentiel')",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        return issues

    def _validate_slide_2_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
        risk_indicators = extraction_result.get('risk_indicators', {})
        
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
                suggestion="Add recommended investment horizon/holding period",
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
        issues: List[ComplianceIssue] = []
        
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
        
        # Rule 1: Morningstar Rating Date and Category
        if "morningstar" in all_text_lower:
            date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{4}'
            
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
                        message="Morningstar rating mentioned but no date found nearby. Ratings must be dated.",
                        suggestion="Add date to Morningstar rating (e.g., 'Morningstar Rating as of [date]')",
                        client_type=client_type,
                        fund_type=fund_type
                    ))
                    break
            
            category_keywords = ['category', 'catégorie', 'kategorie', 'sector', 'secteur']
            morningstar_indices = [m.start() for m in re.finditer("morningstar", all_text_lower)]
            category_near_morningstar = False
            for idx in morningstar_indices:
                context_start = max(0, idx - 200)
                context_end = min(len(all_text_lower), idx + 200)
                context = all_text_lower[context_start:context_end]
                if any(keyword in context for keyword in category_keywords):
                    category_near_morningstar = True
                    break
            
            if not category_near_morningstar:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MORNINGSTAR_MISSING_CATEGORY,
                    rule_reference="Section 4",
                    location="Content",
                    severity="warning",
                    message="Morningstar rating mentioned but category not found nearby. Ratings must include category.",
                    suggestion="Add Morningstar category (e.g., 'Morningstar Category: [category]')",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 2: Portfolio Lines Validation
        portfolio_mentions = extraction_result.get('top_holdings', []) or extraction_result.get('portfolio_breakdown', [])
        if portfolio_mentions and metadata:
            has_prospectus = metadata.get('has_prospectus', False) or metadata.get('prospectus_path')
            if has_prospectus:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.PORTFOLIO_LINES_NOT_IN_PROSPECTUS,
                    rule_reference="Section 4",
                    location="Portfolio Section",
                    severity="warning",
                    message="Portfolio lines shown. Please verify they match the prospectus.",
                    context="Portfolio holdings detected - validation against prospectus recommended",
                    suggestion="Verify all portfolio lines match the official prospectus",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 3: Data Mismatch with Legal Documents
        if metadata and (metadata.get('has_prospectus') or metadata.get('reference_data')):
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.DATA_MISMATCH_WITH_LEGAL_DOCS,
                rule_reference="Section 4",
                location="Document-wide",
                severity="info",
                message="Please verify all data matches legal documents (Prospectus, KID, SFDR Annex).",
                context="Reference documents available - manual verification recommended",
                suggestion="Compare all performance data, fees, and fund characteristics with legal documents",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule 4: Fund Characteristics
        characteristics_keywords = [
            "fund characteristics", "caractéristiques du fonds", "fondskennzeichen",
            "investment objective", "objectif d'investissement", "anlageziel",
            "investment policy", "politique d'investissement", "anlagepolitik"
        ]
        has_characteristics = any(keyword in all_text_lower for keyword in characteristics_keywords)
        if not has_characteristics:
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_FUND_CHARACTERISTICS,
                rule_reference="Section 4",
                location="Content",
                severity="warning",
                message="Fund characteristics section is missing. Should include investment objective and policy.",
                suggestion="Add a 'Fund Characteristics' section with investment objective and policy",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule 5: Team Change Disclaimer
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
                    message="Management team mentioned, but disclaimer 'The team is subject to change' is missing.",
                    suggestion="Add disclaimer: 'The management team is subject to change'",
                    client_type=client_type,
                    fund_type=fund_type
                ))

        # Rule: Opinion/Forecast Attenuation
        opinion_keywords = ["we believe", "nous croyons", "wir glauben", "forecast", "prévision", "prognose", "outlook", "perspective", "ausblick", "anticipate", "anticiper", "erwarten"]
        has_opinion = any(keyword in all_text_lower for keyword in opinion_keywords)
        
        if has_opinion:
            disclaimers_found = extraction_result.get('disclaimers', [])
            disclaimer_texts = []
            for d in disclaimers_found:
                if isinstance(d, str):
                    disclaimer_texts.append(d.lower())
                elif isinstance(d, dict):
                    disclaimer_texts.append(d.get('text', '').lower())
            full_disclaimer_text = " ".join(disclaimer_texts)

            liability_keywords = ["contractually liable", "contractuellement responsable", "vertraglich haftbar", "subject to change", "sujette à modification", "änderungen vorbehalten"]
            has_disclaimer = any(k in full_disclaimer_text for k in liability_keywords)
            
            if not has_disclaimer:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.OPINION_NOT_ATTENUATED,
                    rule_reference="Glossary - Opinion",
                    location="Disclaimers",
                    severity="warning",
                    message="Opinions/Forecasts detected but 'not contractually liable' validation disclaimer is missing.",
                    suggestion="Add disclaimer: 'Opinions... are subject to change... and [Management Company] shall not be held contractually liable'",
                    client_type=client_type,
                    fund_type=fund_type
                ))

        return issues

    def _validate_backtest_simulation_rules(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
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
        
        disclaimers_found = extraction_result.get('disclaimers', [])
        disclaimer_texts = []
        for d in disclaimers_found:
            if isinstance(d, str):
                disclaimer_texts.append(d.lower())
            elif isinstance(d, dict):
                disclaimer_texts.append(d.get('text', '').lower())
        full_disclaimer_text = " ".join(disclaimer_texts)
        
        backtest_keywords = [
            "back-tested", "backtested", "données arrière", "historique reconstruit",
            "back test", "back-test", "backtest", "performance rétrospective",
            "simulations des performances passées", "simulations of past performances"
        ]
        
        simulation_keywords = [
            "simulation", "simulé", "forward-looking", "future performance",
            "projection", "prévision", "simulation de performance future",
            "simulation of future performance", "projection de performance"
        ]
        
        has_backtest = any(keyword in all_text_lower for keyword in backtest_keywords)
        has_simulation = any(keyword in all_text_lower for keyword in simulation_keywords)
        
        if has_backtest and client_type == ClientType.RETAIL:
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.BACKTEST_FOR_RETAIL,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="error",
                message="Backtest performance should not be shown to retail clients. Backtest data is only allowed for professional clients.",
                context="Backtest performance detected in retail document",
                suggestion="Remove backtest performance data or restrict document to professional clients only",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        if has_backtest:
            backtest_disclaimer_phrases = [
                "simulations of past performances",
                "simulations des performances passées",
                "simulations are the result of estimates",
                "simulations sont le résultat d'estimations",
                "do not in any case constitute a promised return",
                "ne sauraient constituer en aucune manière une promesse de rendement",
                "only have an indicative value",
                "n'ont qu'une valeur indicative"
            ]
            
            has_backtest_disclaimer = any(phrase in full_disclaimer_text for phrase in backtest_disclaimer_phrases)
            
            if not has_backtest_disclaimer:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.BACKTEST_MISSING_DISCLAIMER,
                    rule_reference="Section 4.3",
                    location="Disclaimers",
                    severity="error",
                    message="Backtest performance shown but required disclaimer is missing. Backtest data must include a disclaimer stating it is simulated and not a promised return.",
                    context="Backtest performance detected without proper disclaimer",
                    suggestion="Add backtest disclaimer: 'The figures refer to simulations of past performances. These simulations only have an indicative value and do not in any case constitute a promised return.'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        if has_simulation:
            simulation_disclaimer_phrases = [
                "simulation presented does not constitute a forecast",
                "simulation présentée ne constitue pas une prévision",
                "does not constitute a forecast of the future performance",
                "ne constitue pas une prévision de la performance future",
                "solely designed to illustrate",
                "conçue uniquement pour illustrer",
                "valeur peut s'écarter à la hausse ou à la baisse"
            ]
            
            has_simulation_disclaimer = any(phrase in full_disclaimer_text for phrase in simulation_disclaimer_phrases)
            
            if not has_simulation_disclaimer:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.SIMULATION_MISSING_DISCLAIMER,
                    rule_reference="Section 4.3",
                    location="Disclaimers",
                    severity="error",
                    message="Future performance simulation shown but required disclaimer is missing. Simulations must include a disclaimer stating they do not constitute a forecast.",
                    context="Simulation detected without proper disclaimer",
                    suggestion="Add simulation disclaimer: 'The simulation presented does not constitute a forecast of the future performance of your investments. It is solely designed to illustrate the mechanisms of your investment over the investment period. The value of your investment may deviate upwards or downwards from what is displayed.'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        return issues
