"""
ESG Compliance Validator
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType
from .base import BaseValidator

logger = logging.getLogger(__name__)

class EsgValidator(BaseValidator):
    # ... (Same content as before)
    """Validator for ESG and securities mention rules."""
    
    def __init__(self, esg_analyzer=None, enable_esg_validation=True):
        self.esg_analyzer = esg_analyzer
        self.enable_esg_validation = enable_esg_validation
        self._esg_analysis_cache = {}

    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues = []
        issues.extend(self._validate_securities_rules(extraction_result, metadata, client_type, fund_type))
        
        if self.enable_esg_validation and self.esg_analyzer:
            try:
                esg_issues = self._validate_esg_compliance_integrated(
                    extraction_result=extraction_result,
                    metadata=metadata,
                    client_type=client_type,
                    fund_type=fund_type
                )
                issues.extend(esg_issues)
            except Exception as e:
                logger.error(f"[FAIL] ESG compliance validation failed: {e}")
                
        return issues

    def _validate_securities_rules(
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
        
        issuer_mentions = extraction_result.get('issuer_mentions', [])
        has_holdings = bool(extraction_result.get('top_holdings') or extraction_result.get('portfolio_breakdown') or issuer_mentions)
        
        disclaimers_found = extraction_result.get('disclaimers', [])
        disclaimer_texts = []
        for d in disclaimers_found:
            if isinstance(d, str):
                disclaimer_texts.append(d.lower())
            elif isinstance(d, dict):
                disclaimer_texts.append(d.get('text', '').lower())
        full_disclaimer_text = " ".join(disclaimer_texts)
        
        if has_holdings or issuer_mentions:
            if "recommandation" not in full_disclaimer_text and "recommendation" not in full_disclaimer_text:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.INVESTMENT_RECOMMENDATION,
                    rule_reference="Section 4.2",
                    location="Disclaimers",
                    severity="warning",
                    message="Specific securities are mentioned, but disclaimer stating 'This is not a recommendation to buy or sell' is missing.",
                    suggestion="Add disclaimer: 'This does not constitute an investment recommendation'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
            
            valuation_keywords = [
                "undervalued", "sous-évalué", "unterbewertet",
                "overvalued", "surévalué", "überbewertet",
                "correctly valued", "correctement évalué", "korrekt bewertet",
                "fair value", "valeur équitable", "faire wert",
                "intrinsic value", "valeur intrinsèque", "innerer wert"
            ]
            has_valuation_mention = any(keyword in all_text_lower for keyword in valuation_keywords)
            
            if has_valuation_mention:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.SECURITY_VALUATION_MENTION,
                    rule_reference="Section 4.2",
                    location="Content",
                    severity="error",
                    message="Security valuation mentions (undervalued/overvalued) are prohibited in marketing documents. Only factual information is allowed.",
                    context="Valuation keywords detected in document",
                    suggestion="Remove valuation opinions. Only factual information about securities is permitted.",
                    client_type=client_type,
                    fund_type=fund_type
                ))
            
            comparison_keywords = [
                "better than", "meilleur que", "besser als",
                "worse than", "pire que", "schlechter als",
                "compared to", "comparé à", "verglichen mit",
                "versus", "vs", "contre",
                "outperforms", "surperforme", "übertrifft",
                "underperforms", "sous-performe", "untertrifft"
            ]
            has_comparison = any(keyword in all_text_lower for keyword in comparison_keywords)
            if has_comparison and issuer_mentions:
                for mention in issuer_mentions[:5]:
                    mention_text = mention.get('text', '') or mention.get('snippet', '')
                    if mention_text:
                        mention_lower = mention_text.lower()
                        if any(keyword in mention_lower for keyword in comparison_keywords):
                            issues.append(ComplianceIssue(
                                issue_type=ComplianceIssueType.SECURITIES_COMPARISON,
                                rule_reference="Section 4.2",
                                location=mention.get('location', 'Content'),
                                severity="error",
                                message="Securities comparison detected. Direct comparison between securities is prohibited in marketing documents.",
                                context=f"Comparison found: {mention_text[:100]}",
                                suggestion="Remove direct securities comparisons. Only factual information is permitted.",
                                client_type=client_type,
                                fund_type=fund_type
                            ))
                            break
            
            if issuer_mentions:
                security_counts = {}
                for mention in issuer_mentions:
                    security_name = mention.get('issuer', '') or mention.get('company', '') or mention.get('name', '')
                    if security_name:
                        security_name_lower = security_name.lower()
                        security_counts[security_name_lower] = security_counts.get(security_name_lower, 0) + 1
                
                multiple_mentions = {name: count for name, count in security_counts.items() if count > 1}
                if multiple_mentions:
                    for security_name, count in multiple_mentions.items():
                        if count > 2:
                            issues.append(ComplianceIssue(
                                issue_type=ComplianceIssueType.MULTIPLE_SECURITY_MENTIONS,
                                rule_reference="Section 4.2",
                                location="Content",
                                severity="warning",
                                message=f"Security '{security_name}' is mentioned {count} times in the document. Multiple mentions may imply recommendation.",
                                context=f"Security mentioned {count} times",
                                suggestion="Review if multiple mentions are necessary. Ensure all mentions are factual and include proper disclaimer.",
                                client_type=client_type,
                                fund_type=fund_type
                            ))
                            break
            
            projection_keywords = [
                "will reach", "atteindra", "erreicht",
                "expected to", "devrait", "sollte",
                "forecast", "prévision", "prognose",
                "target price", "prix cible", "zielpreis",
                "price target", "objectif de prix", "kursziel",
                "future value", "valeur future", "zukünftiger wert",
                "projected", "projeté", "projiziert"
            ]
            has_projection = any(keyword in all_text_lower for keyword in projection_keywords)
            if has_projection and issuer_mentions:
                for mention in issuer_mentions[:5]:
                    mention_text = mention.get('text', '') or mention.get('snippet', '')
                    if mention_text:
                        mention_lower = mention_text.lower()
                        if any(keyword in mention_lower for keyword in projection_keywords):
                            issues.append(ComplianceIssue(
                                issue_type=ComplianceIssueType.SECURITY_PROJECTION,
                                rule_reference="Section 4.2",
                                location=mention.get('location', 'Content'),
                                severity="error",
                                message="Future projection for security detected. Projections of future security prices/performance are prohibited.",
                                context=f"Projection found: {mention_text[:100]}",
                                suggestion="Remove future projections for securities. Only historical/past performance is permitted.",
                                client_type=client_type,
                                fund_type=fund_type
                            ))
                            break
            
            buy_sell_keywords = [
                "buy", "acheter", "kaufen",
                "sell", "vendre", "verkaufen",
                "reinforce", "renforcer", "verstärken",
                "reduce", "réduire", "reduzieren",
                "increase position", "augmenter position", "position erhöhen",
                "decrease position", "diminuer position", "position verringern"
            ]
            has_buy_sell = any(keyword in all_text_lower for keyword in buy_sell_keywords)
            if has_buy_sell and issuer_mentions:
                for mention in issuer_mentions[:5]:
                    mention_text = mention.get('text', '') or mention.get('snippet', '')
                    if mention_text:
                        mention_lower = mention_text.lower()
                        if any(keyword in mention_lower for keyword in buy_sell_keywords):
                            issues.append(ComplianceIssue(
                                issue_type=ComplianceIssueType.BUY_SELL_RECOMMENDATION,
                                rule_reference="Section 4.2",
                                location=mention.get('location', 'Content'),
                                severity="error",
                                message="Buy/sell recommendation detected. Direct investment recommendations are prohibited in marketing documents.",
                                context=f"Buy/sell keyword found: {mention_text[:100]}",
                                suggestion="Remove buy/sell recommendations. Only factual information about securities is permitted.",
                                client_type=client_type,
                                fund_type=fund_type
                            ))
                            break
        
        return issues
        
    def _validate_esg_compliance_integrated(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
        try:
            fund_name = "Unknown Fund"
            sfdr_article = None
            document_type = "marketing"
            
            if metadata:
                title_info = metadata.get('title_information', {})
                fund_name = title_info.get('fund_name') or metadata.get('fund_name') or fund_name
                sfdr_article = metadata.get('sfdr_article')
                document_type = metadata.get('document_type', 'marketing')
                
                if not sfdr_article:
                    esg_approach = metadata.get('esg_approach', '').lower()
                    if 'article 9' in esg_approach or 'engaging' in esg_approach:
                        sfdr_article = 9
                    elif 'article 8' in esg_approach or 'reduced' in esg_approach:
                        sfdr_article = 8
                    elif 'article 6' in esg_approach or 'none' in esg_approach or 'limited' in esg_approach:
                        sfdr_article = 6
            
            full_text_parts = []
            slides_data = []
            all_slides = []
            
            if 'slides' in extraction_result and extraction_result['slides']:
                all_slides = extraction_result['slides']
            elif 'structure' in extraction_result and 'slides' in extraction_result['structure']:
                all_slides = extraction_result['structure']['slides']
            elif 'text' in extraction_result and extraction_result['text']:
                full_text = extraction_result['text']
                slides_data = [{'slide_number': 1, 'text': full_text, 'title': 'Document'}]
            
            if all_slides and not full_text_parts:
                for i, slide in enumerate(all_slides, 1):
                    if isinstance(slide, dict):
                        slide_num = slide.get('slide_number', i)
                        title = slide.get('title', '')
                        slide_text = title + "\n"
                        
                        if 'content' in slide:
                            for item in slide['content']:
                                if isinstance(item, dict):
                                    slide_text += item.get('text', '') + "\n"
                                else:
                                    slide_text += str(item) + "\n"
                        elif 'text' in slide:
                            slide_text += slide['text'] + "\n"
                        elif 'summary' in slide:
                            slide_text += slide['summary'] + "\n"
                        
                        full_text_parts.append(slide_text)
                        slides_data.append({'slide_number': slide_num, 'text': slide_text, 'title': title})
                    elif isinstance(slide, str):
                        full_text_parts.append(slide)
                        slides_data.append({'slide_number': i, 'text': slide, 'title': ''})
            
            if not slides_data and not full_text_parts:
                full_text = ""
            else:
                full_text = "\n".join(full_text_parts)
            
            if not full_text.strip():
                return issues
            
            max_retries = 2
            esg_level = None
            esg_mentions = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        future_level = executor.submit(self.esg_analyzer.detect_esg_level_v2, fund_name, full_text, sfdr_article)
                        future_mentions = executor.submit(self.esg_analyzer.analyze_esg_mentions_v2, full_text, document_type, slides_data)
                        esg_level = future_level.result()
                        esg_mentions = future_mentions.result()
                    break
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1)
            
            if not esg_level or not esg_mentions:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.ESG_LEVEL_MISMATCH,
                    severity="medium",
                    rule_reference="ESG Validation",
                    message=f"ESG validation could not be completed: {str(last_error)}",
                    location="ESG Analyzer",
                    details={"error": str(last_error), "fallback": "validation_failure"}
                ))
                return issues
            
            self._esg_analysis_cache = {
                "esg_level": {
                    "level": esg_level.level,
                    "sfdr_article": esg_level.sfdr_article,
                    "exclusion_percentage": esg_level.exclusion_percentage,
                    "portfolio_coverage": esg_level.portfolio_coverage,
                    "description": esg_level.description
                },
                "esg_mentions": {
                    "esg_percentage": esg_mentions.esg_percentage,
                    "total_text_length": esg_mentions.total_text_length,
                    "esg_text_length": esg_mentions.esg_text_length,
                    "commercial_esg_mentions": esg_mentions.commercial_esg_mentions,
                    "mandatory_regulatory_mentions": esg_mentions.mandatory_regulatory_mentions,
                    "keywords_found": esg_mentions.esg_keywords_found,
                    "keywords_by_slide": esg_mentions.esg_keywords_by_slide
                },
                "analysis_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
            
            if esg_level.level == "none" or esg_level.sfdr_article == 6:
                if esg_mentions.commercial_esg_mentions > 0:
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.ESG_FORBIDDEN_ARTICLE6,
                        rule_reference="SFDR Article 6",
                        location="Document-wide",
                        severity="critical",
                        message=f"Article 6 (non-ESG): {esg_mentions.commercial_esg_mentions} commercial ESG mentions detected",
                        context=f"ESG Level: {esg_level.level}, ESG%: {esg_mentions.esg_percentage}%",
                        suggestion="Remove all commercial ESG mentions from Article 6 fund materials",
                        client_type=client_type,
                        fund_type=fund_type,
                        details={"esg_percentage": esg_mentions.esg_percentage, "commercial_mentions": esg_mentions.commercial_esg_mentions}
                    ))
            
            if esg_level.level == "reduced" or esg_level.sfdr_article == 8:
                if esg_mentions.esg_percentage > 10.0:
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.ESG_OVERMENTIONED_ARTICLE8,
                        rule_reference="SFDR Article 8",
                        location="Document-wide",
                        severity="high",
                        message=f"Article 8 fund: ESG content exceeds 10% limit ({esg_mentions.esg_percentage}%)",
                        context=f"ESG Level: {esg_level.level}, Commercial mentions: {esg_mentions.commercial_esg_mentions}",
                        suggestion="Reduce ESG content to below 10% of total document text",
                        client_type=client_type,
                        fund_type=fund_type,
                        details={"esg_percentage": esg_mentions.esg_percentage, "limit": 10.0}
                    ))
            
            if esg_level.level == "engaging" or esg_level.sfdr_article == 9:
                criteria_issues = []
                if (esg_level.exclusion_percentage or 0) < 20:
                    criteria_issues.append(f"exclusion_percentage={esg_level.exclusion_percentage}% (required: >= 20%)")
                if (esg_level.portfolio_coverage or 0) < 90:
                    criteria_issues.append(f"portfolio_coverage={esg_level.portfolio_coverage}% (required: >= 90%)")
                
                if criteria_issues:
                    issues.append(ComplianceIssue(
                        issue_type=ComplianceIssueType.ENGAGING_CRITERIA_NOT_MET,
                        rule_reference="SFDR Article 9",
                        location="Document-wide",
                        severity="high",
                        message=f"Article 9 (engaging) fund does not meet criteria: {', '.join(criteria_issues)}",
                        context=f"ESG Level: {esg_level.level}",
                        suggestion="Verify fund classification or ensure exclusion percentage >= 20% and portfolio coverage >= 90%",
                        client_type=client_type,
                        fund_type=fund_type
                    ))
            
            if metadata and metadata.get('sfdr_article') and metadata.get('sfdr_article') != esg_level.sfdr_article:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.SFDR_ARTICLE_INCONSISTENCY,
                    rule_reference="SFDR Disclosure",
                    location="Document metadata",
                    severity="medium",
                    message=f"SFDR article mismatch: metadata indicates Article {metadata.get('sfdr_article')}, but content suggests Article {esg_level.sfdr_article or 'Unknown'}",
                    context=f"Detected ESG level: {esg_level.level}",
                    suggestion="Verify SFDR classification and ensure document content aligns with declared article",
                    client_type=client_type,
                    fund_type=fund_type,
                    details={"metadata_article": metadata.get('sfdr_article'), "detected_article": esg_level.sfdr_article}
                ))
                
            if esg_mentions.esg_keywords_by_slide and esg_level.level != "engaging":
                for keyword, slide_nums in esg_mentions.esg_keywords_by_slide.items():
                    if len(slide_nums) > 10:
                        issues.append(ComplianceIssue(
                            issue_type=ComplianceIssueType.ESG_KEYWORD_OVERUSE,
                            rule_reference="Best Practices",
                            location=f"Keyword '{keyword}' appears in {len(slide_nums)} slides",
                            severity="low",
                            message=f"ESG keyword '{keyword}' appears excessively across {len(slide_nums)} slides",
                            context=f"Slides: {', '.join(map(str, slide_nums[:10]))}...",
                            suggestion="Consider reducing repetitive ESG terminology",
                            client_type=client_type,
                            fund_type=fund_type,
                            details={"keyword": keyword, "slide_count": len(slide_nums)}
                        ))
            
        except ImportError as e:
            logger.error(f"[FAIL] ESG Analyzer import failed: {e}")
        except Exception as e:
            logger.error(f"[FAIL] ESG compliance validation error: {e}")
            import traceback
            traceback.print_exc()
        
        return issues
