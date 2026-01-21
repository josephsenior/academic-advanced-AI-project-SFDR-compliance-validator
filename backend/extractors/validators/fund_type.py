"""
Fund Type Validator
"""
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType, FundType
from .base import BaseValidator
from .utils import infer_last_slide, infer_performance_slide

class FundTypeValidator(BaseValidator):
    """Validator for rules specific to certain fund types (Dated, PE, ETF, Money Market, RAIF)."""
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
        # Get all text content
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
        
        # Determine fund type from metadata or title
        fund_name = ""
        if metadata:
            title_info = metadata.get('title_information', {})
            fund_name = (title_info.get('fund_name') or metadata.get('fund_name') or "").lower()
        
        # Enhanced fund type detection
        detected_fund_type = fund_type
        if not detected_fund_type or detected_fund_type == FundType.STANDARD:
            if "fcpr" in fund_name or "fpci" in fund_name or "private equity" in fund_name:
                detected_fund_type = FundType.PRIVATE_EQUITY
            elif "etf" in fund_name or "exchange traded" in fund_name:
                detected_fund_type = FundType.ETF
            elif "daté" in fund_name or "dated" in fund_name or "échéance" in fund_name or "target date" in fund_name:
                # Try to determine if active or buy-hold (default to active for safety)
                if "buy" in fund_name and "hold" in fund_name:
                    detected_fund_type = FundType.DATED_FUND_BUY_HOLD
                else:
                    detected_fund_type = FundType.DATED_FUND_ACTIVE
            elif "money market" in fund_name or "fonds monétaire" in fund_name or "geldmarktfonds" in fund_name:
                detected_fund_type = FundType.MONEY_MARKET
            elif "raif" in fund_name or "reserved alternative" in fund_name:
                detected_fund_type = FundType.RAIF
        
        # Update fund_type reference for return
        if detected_fund_type:
            fund_type = detected_fund_type

        # ============================================================================
        # DATED FUND RULES
        # ============================================================================
        if detected_fund_type in [FundType.DATED_FUND_ACTIVE, FundType.DATED_FUND_BUY_HOLD]:
            # YTM/YTW detection
            ytm_keywords = ["ytm", "yield to maturity", "rendement à l'échéance", "rendement jusqu'à l'échéance"]
            ytw_keywords = ["ytw", "yield to worst", "rendement au pire", "rendement minimum"]
            
            has_ytm = any(keyword in all_text_lower for keyword in ytm_keywords)
            has_ytw = any(keyword in all_text_lower for keyword in ytw_keywords)
            
            # Rule: Active dated funds - YTM/YTW not allowed for retail
            if detected_fund_type == FundType.DATED_FUND_ACTIVE:
                if client_type == ClientType.RETAIL:
                    if has_ytm:
                        perf_slide = infer_performance_slide(extraction_result) or 4
                        issues.append(ComplianceIssue(
                            issue_type=ComplianceIssueType.YTM_FOR_ACTIVE_RETAIL,
                            rule_reference="Rule 162 - Active Dated Fund Restrictions",
                            location=f"Slide {perf_slide} - Performance or yield metrics table",
                            slide_number=perf_slide,
                            severity="error",
                            message="YTM (Yield to Maturity) should not be shown for active management dated funds to retail clients.",
                            context="YTM metric detected for active dated fund shown to retail investors. YTM implies buy-and-hold strategy which is inconsistent with active management disclosure rules.",
                            suggestion=f"Remove YTM metric from the table on Slide {perf_slide} or restrict document to professional clients only. Active retail dated funds must prioritize actual performance.",
                            client_type=client_type,
                            fund_type=detected_fund_type
                        ))
                    
                    if has_ytw:
                        perf_slide = infer_performance_slide(extraction_result) or 4
                        issues.append(ComplianceIssue(
                            issue_type=ComplianceIssueType.YTW_FOR_ACTIVE_RETAIL,
                            rule_reference="Rule 162 - Active Dated Fund Restrictions",
                            location=f"Slide {perf_slide} - Yield or risk metrics section",
                            slide_number=perf_slide,
                            severity="error",
                            message="YTW (Yield to Worst) should not be shown for active management dated funds to retail clients.",
                            context="YTW metric detected for active dated fund shown to retail investors. YTW assumes worst-case bond call scenarios not applicable to active management retail marketing.",
                            suggestion=f"Remove YTW metric from Slide {perf_slide} or restrict document to professional clients. Show fund performance and SRI risk profile instead.",
                            client_type=client_type,
                            fund_type=detected_fund_type
                        ))
        
        # ============================================================================
        # PRIVATE EQUITY RULES
        # ============================================================================
        if detected_fund_type == FundType.PRIVATE_EQUITY:
            # Check for liquidity disclaimer (existing rule)
            disclaimers_found = extraction_result.get('disclaimers', [])
            disclaimer_texts = []
            for d in disclaimers_found:
                if isinstance(d, str):
                    disclaimer_texts.append(d.lower())
                elif isinstance(d, dict):
                    disclaimer_texts.append(d.get('text', '').lower())
            full_disclaimer_text = " ".join(disclaimer_texts)
            
            if "liquidité" not in full_disclaimer_text and "liquidity" not in full_disclaimer_text:
                last_slide = infer_last_slide(extraction_result)
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_STANDARD_DISCLAIMER,
                    rule_reference="Rule 164 - PE Fund Risk Disclosure",
                    location=f"Slide {last_slide} - Risk Factors or Disclaimer section (PE)",
                    slide_number=last_slide,
                    severity="error",
                    message="Private Equity fund detected, but warning about 'Liquidity Risk' is missing.",
                    context="Private Equity fund (FCPR/FPCI) without liquidity risk warning. PE investments are illiquid by nature and require specific regulatory warnings.",
                    suggestion="Add to Slide 6 disclaimers: 'Private Equity Fund - Limited Liquidity: Redemptions may be restricted. Investors should have long-term investment horizons.'",
                    client_type=client_type,
                    fund_type=detected_fund_type
                ))
            
            # Rule: Net IRR not for retail
            if client_type == ClientType.RETAIL:
                irr_keywords = [
                    "net irr", "irr net", "taux de rendement interne net",
                    "internal rate of return", "taux de rendement interne"
                ]
                has_irr = any(keyword in all_text_lower for keyword in irr_keywords)
                
                if has_irr:
                    perf_slide = infer_performance_slide(extraction_result) or 4
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.NET_IRR_FOR_RETAIL,
                        rule_reference="Rule 165 - PE Performance Metrics Restrictions",
                        location=f"Slide {perf_slide} - Performance summary table (PE)",
                        slide_number=perf_slide,
                        severity="error",
                        message="Net IRR (Internal Rate of Return) should not be shown to retail clients for Private Equity funds.",
                        context="Net IRR metric detected in PE fund document for retail investors. IRR methodology is complex and can be misleading for non-professional investors.",
                        suggestion=f"Remove Net IRR from Slide {perf_slide} or restrict document to professional clients only. Show fund NAV and simple annual performance.",
                        client_type=client_type,
                        fund_type=detected_fund_type
                    ))
                
                # Rule: Institutional track record not for retail
                institutional_track_keywords = [
                    "institutional track record", "track record institutionnel",
                    "performance institutionnelle", "institutional performance"
                ]
                has_institutional_track = any(keyword in all_text_lower for keyword in institutional_track_keywords)
                
                if has_institutional_track:
                    perf_slide = infer_performance_slide(extraction_result) or 4
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.INSTITUTIONAL_TRACK_FOR_RETAIL,
                        rule_reference="Rule 165 - PE Performance Metrics Restrictions",
                        location=f"Slide {perf_slide} - Historical track record section",
                        slide_number=perf_slide,
                        severity="error",
                        message="Institutional track record should not be shown to retail clients for Private Equity funds.",
                        context="Institutional track record (separate from current fund) shown to retail. This is prohibited as it may imply performance expectations that don't apply to the retail share class.",
                        suggestion=f"Remove institutional track record from Slide {perf_slide} or restrict document to professional clients. Show only current retail share class performance.",
                        client_type=client_type,
                        fund_type=detected_fund_type
                    ))
        
        # ============================================================================
        # ETF RULES
        # ============================================================================
        if detected_fund_type == FundType.ETF:
            # Rule: ETF should not be called "liquid"
            liquid_keywords = [
                "liquid etf", "etf liquid", "liquid exchange traded",
                "etf liquide", "fonds négociable liquide"
            ]
            has_liquid_mention = any(keyword in all_text_lower for keyword in liquid_keywords)
            
            # Also check if "liquid" appears near "etf"
            if "liquid" in all_text_lower and "etf" in all_text_lower:
                # Check if they appear close together (within 50 chars)
                etf_positions = [i for i, word in enumerate(all_text_lower.split()) if "etf" in word]
                liquid_positions = [i for i, word in enumerate(all_text_lower.split()) if word == "liquid"]
                
                for etf_pos in etf_positions:
                    for liq_pos in liquid_positions:
                        if abs(etf_pos - liq_pos) <= 10:  # Within 10 words
                            has_liquid_mention = True
                            break
                    if has_liquid_mention:
                        break
            
            if has_liquid_mention:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.ETF_CALLED_LIQUID,
                    rule_reference="Rule 139 - ETF Terminology Restrictions",
                    location="Slide 1 - Cover Page or Marketing messaging",
                    severity="error",
                    message="ETF should not be called 'liquid'. ETFs have secondary market liquidity risks and should not be described as liquid in marketing headers.",
                    context="ETF described as 'liquid' in marketing material. Using 'liquid' misrepresents ETF liquidity characteristics which depend on market makers and exchange volume.",
                    suggestion="Remove 'liquid' descriptor from Slide 1. Use accurate language: 'shares trade on exchange' or 'secondary market liquidity depends on market conditions'.",
                    client_type=client_type,
                    fund_type=detected_fund_type
                ))
        
        # ============================================================================
        # MONEY MARKET FUND RULES
        # ============================================================================
        if detected_fund_type == FundType.MONEY_MARKET:
            # Check for money market disclaimer
            money_market_disclaimer_keywords = [
                "money market fund", "fonds monétaire", "geldmarktfonds",
                "not a guaranteed investment", "n'est pas un investissement garanti",
                "different from investment in deposits", "différent d'un investissement en dépôt"
            ]
            has_money_market_disclaimer = any(keyword in all_text_lower for keyword in money_market_disclaimer_keywords)
            
            if not has_money_market_disclaimer:
                last_slide = infer_last_slide(extraction_result)
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_STANDARD_DISCLAIMER,
                    rule_reference="Rule 140 - Money Market Fund Disclosures",
                    location=f"Slide {last_slide} - Disclaimer section (Money Market)",
                    slide_number=last_slide,
                    severity="warning",
                    message="Money Market fund detected, but specific Money Market disclaimer may be missing.",
                    context="Money Market fund without standard disclaimer explaining no guaranteed return and difference from bank deposits.",
                    suggestion="Add to Slide 6: 'This money market fund is not a guaranteed investment. Investment differs from bank deposits. Capital is not guaranteed.'",
                    client_type=client_type,
                    fund_type=detected_fund_type
                ))
            
            # Additional Rule for Weekly Factsheet
            document_type_keywords = ["weekly factsheet", "reporting hebdomadaire", "wöchentliches reporting"]
            is_weekly = any(keyword in all_text_lower for keyword in document_type_keywords)
            
            if is_weekly:
                # glossary: "pursuant to Article 36 (2) of EU Regulation 2017/1131"
                has_citation = "article 36" in all_text_lower and "2017/1131" in all_text_lower
                
                if not has_citation:
                    last_slide = infer_last_slide(extraction_result)
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.MISSING_WEEKLY_MM_LEGAL_CITATION,
                        rule_reference="EU Regulation 2017/1131 - Article 36(2)",
                        location=f"Slide {last_slide} - Footer or Legal Information section",
                        slide_number=last_slide,
                        severity="error",
                        message="Weekly Money Market Factsheet missing required Article 36 citation.",
                        context="Weekly reporting for MM funds must include a specific legal citation referencing Article 36(2) of EU Regulation 2017/1131.",
                        suggestion="Add legal citation to footer: 'Factsheet prepared pursuant to Article 36(2) of EU Regulation 2017/1131'",
                        client_type=client_type,
                        fund_type=detected_fund_type
                    ))
        
        # ============================================================================
        # RAIF RULES
        # ============================================================================
        if detected_fund_type == FundType.RAIF:
            well_informed_keywords = [
                "well-informed investor", "investisseur bien informé",
                "well informed investor", "investisseur averti"
            ]
            has_well_informed_mention = any(keyword in all_text_lower for keyword in well_informed_keywords)
            
            if not has_well_informed_mention:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_TARGET_AUDIENCE,
                    rule_reference="RAIF Directive - Target Audience Disclosure",
                    location="Slide 1 - Cover Page (Confidentiality Banner)",
                    slide_number=1,
                    severity="error",
                    message="RAIF fund detected, but 'Well-informed investor' target audience indication is missing.",
                    context="Reserved Alternative Investment Funds (RAIF) are restricted to well-informed investors. This status must be visible on the cover.",
                    suggestion="Add to Slide 1 header: 'RESERVED FOR WELL-INFORMED INVESTORS AS DEFINED BY RAIF DIRECTIVE'",
                    client_type=client_type,
                    fund_type=detected_fund_type
                ))
            
            # RAIF requires specific disclaimer
            raif_disclaimer_keywords = [
                "raif", "reserved alternative investment fund",
                "fonds d'investissement alternatif réservé"
            ]
            
            # Get disclaimer text if not available
            disclaimers_found = extraction_result.get('disclaimers', [])
            disclaimer_texts = []
            for d in disclaimers_found:
                if isinstance(d, str):
                    disclaimer_texts.append(d.lower())
                elif isinstance(d, dict):
                    disclaimer_texts.append(d.get('text', '').lower())
            full_disclaimer_text = " ".join(disclaimer_texts)
            
            has_raif_disclaimer = any(keyword in full_disclaimer_text for keyword in raif_disclaimer_keywords)
            
            if not has_raif_disclaimer:
                last_slide = infer_last_slide(extraction_result)
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_STANDARD_DISCLAIMER,
                    rule_reference="RAIF Directive - Alternative Risk Disclosure",
                    location=f"Slide {last_slide} - Legal Information section (RAIF)",
                    slide_number=last_slide,
                    severity="warning",
                    message="RAIF fund detected, but RAIF-specific disclaimer may be missing.",
                    context="Reserved Alternative Investment Fund (RAIF) requires a standard disclaimer about its specialized nature and risk profile.",
                    suggestion="Add RAIF disclaimer: 'This is a Reserved Alternative Investment Fund (RAIF). It is reserved for well-informed investors and involves high risks.'",
                    client_type=client_type,
                    fund_type=detected_fund_type
                ))
                
        return issues
