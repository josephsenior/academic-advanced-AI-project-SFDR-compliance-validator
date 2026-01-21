"""
Content Validator
"""
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType
from .base import BaseValidator
from .utils import infer_last_slide, infer_glossary_slide, infer_performance_slide, infer_slide_containing_text
from .visual_formatting import verify_pptx_formatting

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
        issues.extend(self._validate_visual_formatting(extraction_result, metadata, client_type, fund_type))
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
                 glossary_slide = infer_glossary_slide(extraction_result)
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_GLOSSARY,
                    rule_reference="Rule 8 - Retail Glossary",
                    location=f"Slide {glossary_slide} - Retail Glossary section",
                    slide_number=glossary_slide,
                    severity="warning",
                    message="Retail document requires a Glossary. It should typically be on the last slide.",
                    context="No glossary found in document. Retail clients need term definitions.",
                    suggestion="Add a glossary section explaining technical terms (e.g., SRI, ISIN, prospectus) used in the document",
                    client_type=client_type,
                    fund_type=fund_type
                ))

        # FWW Fundstars Rule
        if "fww" in all_text_lower or "fundstars" in all_text_lower:
            fww_disclaimer = "http://fww.de/disclaimer"
            if fww_disclaimer not in all_text_lower:
                 last_slide = infer_last_slide(extraction_result)
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_FWW_DISCLAIMER,
                    rule_reference="Glossary - FWW Source Attribution",
                    location=f"Slide {last_slide} - Data sources & attribution footnote",
                    slide_number=last_slide,
                    severity="warning",
                    message="FWW/Fundstars mentioned but source link/disclaimer missing.",
                    context="FWW data used without proper source attribution and liability disclaimer",
                    suggestion="Add FWW source footnote: '* Source: FWW Fundservices GmbH, http://fww.de/disclaimer/'  ",
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
                    rule_reference="Glossary - New Offer Risk Disclosure",
                    location="Slide 2 - Risk Factors & Key Information section",
                    slide_number=2,
                    severity="error",
                    message="New Offer/Strategy mentioned but 'risk of capital loss' warning missing.",
                    context="New offer/strategy detected without mandatory capital loss risk warning",
                    suggestion="Add specific risk warnings on Slide 2 Risk Factors: 'This is a new investment offering. Your capital is at risk and you may not recover your initial investment.'",
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
                    rule_reference="Rule 27 - Cover Page Fund Name",
                    location="Slide 1 - Cover Page Title",
                    slide_number=1,
                    severity="error",
                    message="Fund Name is missing on the cover page.",
                    context="Fund name/identification required on cover page for document clarity",
                    suggestion="Add fund name prominently in the cover page title area (e.g., '[Fund Name] - Investment Presentation')",
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
                    rule_reference="Rule 28 - Document Date",
                    location="Slide 1 - Cover Page Subtitle/Footer",
                    slide_number=1,
                    severity="error",
                    message="Document Date is missing on the cover page (Month and Year required).",
                    context="Cover page must show when document was published for compliance and recency tracking",
                    suggestion="Add date to Slide 1 (e.g., 'March 2024' or 'As of March 2024')",
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
                    rule_reference="Rule 29 - Promotional Document Disclosure",
                    location="Slide 1 - Cover Page Header or Subtitle",
                    slide_number=1,
                    severity="error",
                    message="Cover page must include the mention 'Document promotionnel' or 'Marketing communication'.",
                    context="Regulatory requirement to disclose promotional nature of marketing documents",
                    suggestion="Add to cover page header or subtitle: 'This is a Marketing Communication / Document Promotionnel'",
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
                    rule_reference="Rule 30 - Target Audience Disclosure",
                    location="Slide 1 - Cover Page Disclaimer area",
                    slide_number=1,
                    severity="warning",
                    message="Target audience (Professional/Retail) must be indicated on the cover page.",
                    context="Document audience must be clearly identified to ensure proper distribution",
                    suggestion="Add target audience to Slide 1 (e.g., '*** STRICTLY CONFIDENTIAL - FOR PROFESSIONAL CLIENTS ONLY ***')",
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
                    rule_reference="Rules 31-34 - Premarketing Warning",
                    location="Slide 1 - Cover Page Top in Red/Bold box",
                    slide_number=1,
                    severity="error",
                    message="Premarketing document must include a specific premarketing warning on the cover page in red and bold.",
                    context="Pre-marketing documents require prominent regulatory warning before fund approval",
                    suggestion="Add prominent red/bold warning box at top of Slide 1: 'VEUILLEZ NOTER QUE LE FONDS N'A PAS ENCORE ÉTÉ AGRÉÉ PAR L'AUTORITÉ DE RÉGULATION COMPÉTENTE.'",
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
                    rule_reference="Rule 35 - Confidentiality Notice",
                    location="Slide 1 - Cover Page Confidentiality Banner (Header or Top)",
                    slide_number=1,
                    severity="error",
                    message="Confidential/Professional document must include a 'Do Not Disclose' notice on the cover page.",
                    context="Professional documents require confidentiality disclaimer to control distribution",
                    suggestion="Add confidentiality banner at top of Slide 1: '*** STRICTLY CONFIDENTIAL *** Do not disclose or distribute to third parties without authorization'",
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
                rule_reference="Rule 40 - Risk Scale (SRI)",
                location="Slide 2 - Risk Profile / Key Information section",
                slide_number=2,
                severity="error",
                message="Risk Scale (SRI) is missing. It is mandatory on Slide 2.",
                context="No SRI (Synthetic Risk Indicator) found. Essential for investor risk awareness.",
                suggestion="Add SRI scale graphic on Slide 2 Risk section (typically 1-7 scale with fund position marked)",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        if not risk_indicators.get('investment_horizon'):
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_RISK_PROFILE,
                rule_reference="Rule 40 - Recommended Holding Period",
                location="Slide 2 - Risk Profile / Key Information box",
                slide_number=2,
                severity="warning",
                message="Investment Horizon is missing. It is required on Slide 2.",
                context="No investment horizon/recommended holding period found. Required for investor suitability.",
                suggestion="Add recommended holding period to Slide 2 Key Info (e.g., 'Recommended investment horizon: 5+ years')",
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
                    # Find which slide contains this match
                    slide_num = infer_slide_containing_text(extraction_result, ['morningstar']) or 3
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.MORNINGSTAR_MISSING_DATE,
                        rule_reference="Rule 47 - Morningstar Rating Date",
                        location=f"Slide {slide_num} - Morningstar rating box or table cell",
                        slide_number=slide_num,
                        severity="warning",
                        message="Morningstar rating mentioned but no date found nearby. Ratings must be dated.",
                        context="Morningstar rating requires current date for rating validity and recency",
                        suggestion="Add date to Morningstar rating box: 'Morningstar Rating as of [Month YYYY]'",
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
                slide_num = infer_slide_containing_text(extraction_result, ['morningstar']) or 3
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MORNINGSTAR_MISSING_CATEGORY,
                    rule_reference="Rule 48 - Morningstar Category Disclosure",
                    location=f"Slide {slide_num} - Morningstar rating label or caption",
                    slide_number=slide_num,
                    severity="warning",
                    message="Morningstar rating mentioned but category not found nearby. Ratings must include category.",
                    context="Morningstar ratings require category context for comparison and interpretation",
                    suggestion="Add category label near rating: 'Morningstar Category: [Equity/Bond/Mixed/etc.]' or below rating box",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 2: Portfolio Lines Validation
        portfolio_mentions = extraction_result.get('top_holdings', []) or extraction_result.get('portfolio_breakdown', [])
        if portfolio_mentions and metadata:
            has_prospectus = metadata.get('has_prospectus', False) or metadata.get('prospectus_path')
            if has_prospectus:
                portfolio_slide = infer_slide_containing_text(extraction_result, ['portfolio', 'holdings', 'top 10', 'positions', 'breakdown', 'allocation']) or 3
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.PORTFOLIO_LINES_NOT_IN_PROSPECTUS,
                    rule_reference="Rule 49 - Portfolio Content Verification",
                    location=f"Slide {portfolio_slide} - Portfolio table or holdings list",
                    slide_number=portfolio_slide,
                    severity="warning",
                    message="Portfolio lines shown. Please verify they match the prospectus.",
                    context=f"Portfolio holdings detected on Slide {portfolio_slide} - validation against prospectus recommended",
                    suggestion="Compare portfolio holdings table with official prospectus document to ensure accuracy and alignment",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule 3: Data Mismatch with Legal Documents
        if metadata and (metadata.get('has_prospectus') or metadata.get('reference_data')):
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.DATA_MISMATCH_WITH_LEGAL_DOCS,
                rule_reference="Rule 51 - Data Consistency Check",
                location="Slides 1-3 - Key Information & Fund Facts sections",
                slide_number=2,
                severity="info",
                message="Please verify all data matches legal documents (Prospectus, KID, SFDR Annex).",
                context="Reference documents available - manual verification recommended for all fund facts, fees, and characteristics",
                suggestion="Cross-reference: (1) Fund name/ISIN (Slide 1), (2) Risk profile/SRI (Slide 2), (3) Performance data (Slides 3-4) against official prospectus",
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
            last_slide = infer_last_slide(extraction_result)
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_FUND_CHARACTERISTICS,
                rule_reference="Rule 50 - Fund Characteristics Disclosure",
                location=f"Slide {last_slide} - Fund Characteristics table",
                slide_number=last_slide,
                severity="warning",
                message="Fund characteristics section is missing. Should include investment objective and policy.",
                context="Fund characteristics needed for investor understanding of fund's strategy and constraints",
                suggestion="Add appendix slide or section with: Fund Objective, Investment Policy, Asset Classes, Max/Min allocations, Geographic focus",
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
                last_slide = infer_last_slide(extraction_result)
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_TEAM_CHANGE_DISCLAIMER,
                    rule_reference="Rule 53 - Team Change Disclaimer",
                    location=f"Slide {last_slide} - Legal Disclaimers section",
                    slide_number=last_slide,
                    severity="warning",
                    message="Management team mentioned, but disclaimer 'The team is subject to change' is missing.",
                    context="When team members are named/identified, disclaimer required to protect against liability if personnel changes occur",
                    suggestion="Add disclaimer in footer or appendix: 'The management team is subject to change. Changes will be communicated to investors.'",
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
                 last_slide = infer_last_slide(extraction_result)
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.OPINION_NOT_ATTENUATED,
                    rule_reference="Rules 13, 78 - Opinion Liability Disclaimer",
                    location=f"Slide {last_slide} - Opinions & Forecasts disclaimer",
                    slide_number=last_slide,
                    severity="warning",
                    message="Opinions/Forecasts detected but 'not contractually liable' validation disclaimer is missing.",
                    context="Opinions and forecasts require liability attenuation to limit company exposure and manage investor expectations",
                    suggestion="Add to disclaimers: 'Opinions expressed... are subject to change without notice. [Company] shall not be held contractually liable for any statement in this document.'",
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
            perf_slide = infer_performance_slide(extraction_result) or 4
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.BACKTEST_FOR_RETAIL,
                rule_reference="Rule 127 - Backtest Restrictions",
                location=f"Slide {perf_slide} - Performance graph or table",
                slide_number=perf_slide,
                severity="error",
                message="Backtest performance should not be shown to retail clients. Backtest data is only allowed for professional clients.",
                context="Backtest performance (simulated historical data) detected in retail document - compliance violation",
                suggestion="Either (1) Remove backtest performance charts and show only actual performance, or (2) Restrict document to professional clients only",
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
                perf_slide = infer_performance_slide(extraction_result) or 4
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.BACKTEST_MISSING_DISCLAIMER,
                    rule_reference="Rule 186 - Backtest Disclaimer",
                    location=f"Slide {perf_slide} - Performance table or chart footer",
                    slide_number=perf_slide,
                    severity="error",
                    message="Backtest performance shown but required disclaimer is missing. Backtest data must include a disclaimer stating it is simulated and not a promised return.",
                    context="Backtest performance detected without proper disclaimer. Performance based on back-tested data must be clearly identified.",
                    suggestion=f"Add backtest disclaimer on Slide {perf_slide}: 'Les chiffres se référent à des simulations des performances passées...'",
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
                perf_slide = infer_performance_slide(extraction_result) or 4
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.SIMULATION_MISSING_DISCLAIMER,
                    rule_reference="Rule 187 - Forward-Looking Simulation Disclaimer",
                    location=f"Slide {perf_slide} - Simulation chart footer or callout box",
                    slide_number=perf_slide,
                    severity="error",
                    message="Future performance simulation shown but required disclaimer is missing. Simulations must include a disclaimer stating they do not constitute a forecast.",
                    context="Forward-looking simulation/projection detected without proper disclaimer explaining non-forecast nature and uncertainty",
                    suggestion=f"Add disclaimer near simulation graphic on Slide {perf_slide}: 'The simulation presented does not constitute a forecast of future performance. The value may fall as well as rise. Past performance and simulations are not reliable indicators of future results.'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        return issues
    
    def _validate_visual_formatting(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate visual formatting of risk disclaimers (Rule 1)
        
        Rule 1 requires:
        - Risk disclaimers must be bold
        - Risk disclaimers must use same font size as body text
        - Risk disclaimers must not be hidden in footers
        """
        issues: List[ComplianceIssue] = []
        
        # Get PPTX file path from metadata or extraction result
        pptx_file_path = None
        
        if metadata and metadata.get('file_path'):
            pptx_file_path = metadata['file_path']
        elif extraction_result.get('source_file'):
            pptx_file_path = extraction_result['source_file']
        
        # If we can't find the PPTX file, we can't check formatting
        if not pptx_file_path or not Path(pptx_file_path).exists():
            return issues
        
        try:
            # Verify formatting
            formatting_results = verify_pptx_formatting(pptx_file_path, extraction_result)
            
            # Check if any disclaimers are not bold
            non_bold = formatting_results.get('non_bold_disclaimers', [])
            
            if non_bold:
                # Flag the first few non-compliant disclaimers
                for idx, disclaimer in enumerate(non_bold[:3]):
                    slide_num = disclaimer.get('slide', 1)
                    text_preview = disclaimer.get('text', 'Risk disclaimer')[:50]
                    location = disclaimer.get('location', 'slide')
                    
                    # Higher severity if in footer
                    severity = "critical" if location == "footer" else "high"
                    
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.MISSING_DISCLAIMER,  # Using this as proxy for formatting
                        rule_reference="Rule 1 - Disclaimer Formatting (Bold)",
                        location=f"Slide {slide_num} - {text_preview}",
                        slide_number=slide_num,
                        severity=severity,
                        message=f"Risk disclaimer not properly formatted - must be bold. Found: '{text_preview}...'",
                        context=(
                            f"Risk-related text on Slide {slide_num} is not bold. "
                            f"Location: {location}. "
                            f"Font: {disclaimer.get('font_name')}"
                        ),
                        suggestion=(
                            "Make all risk-related disclaimers bold with same font size as body text. "
                            "Ensure they are in main content area, not in footers or headers."
                        ),
                        client_type=client_type,
                        fund_type=fund_type,
                        details={
                            "text": text_preview,
                            "bold": disclaimer.get('is_bold'),
                            "location": location,
                            "font_name": disclaimer.get('font_name'),
                            "font_size": disclaimer.get('font_size')
                        }
                    ))
            
            # Also flag if many disclaimers are non-bold (systematic problem)
            summary = formatting_results.get('summary', {})
            compliance_rate = summary.get('compliance_percentage', 100)
            
            if compliance_rate < 50 and summary.get('total_disclaimers', 0) > 5:
                # Systematic formatting issue
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.VISUAL_VIOLATION,
                    rule_reference="Rule 1 - Systematic Disclaimer Formatting Issue",
                    location="Throughout document",
                    slide_number=1,
                    severity="error",
                    message=f"Systematic issue: Only {compliance_rate:.0f}% of risk disclaimers are bold. Rule 1 requires all disclaimers to be bold.",
                    context=(
                        f"Out of {summary.get('total_disclaimers')} risk-related text elements found, "
                        f"only {summary.get('compliant')} are properly formatted (bold). "
                        f"{summary.get('non_compliant')} are not bold."
                    ),
                    suggestion=(
                        "Apply bold formatting to all risk disclaimers throughout the document. "
                        "Use find-replace feature in PowerPoint to identify and format all risk-related text."
                    ),
                    client_type=client_type,
                    fund_type=fund_type,
                    details={
                        "total_disclaimers": summary.get('total_disclaimers'),
                        "compliant_count": summary.get('compliant'),
                        "non_compliant_count": summary.get('non_compliant'),
                        "compliance_percentage": compliance_rate
                    }
                ))
        
        except Exception as e:
            # If visual formatting check fails, don't fail the entire validation
            # Just log a warning
            pass
        
        return issues
