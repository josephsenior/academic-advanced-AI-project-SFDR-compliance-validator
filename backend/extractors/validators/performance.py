"""
Performance Validator
"""
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType
from .base import BaseValidator
from .utils import infer_performance_slide

def infer_period_from_column(column_name: str) -> Optional[str]:
    """Infer time period from column name."""
    col = column_name.lower()
    if 'ytd' in col:
        return 'YTD'
    if 'mtd' in col:
        return 'MTD'
    if '1y' in col or '1 an' in col or '1 year' in col:
        return '1Y'
    if '3y' in col or '3 ans' in col or '3 year' in col:
        return '3Y'
    if '5y' in col or '5 ans' in col or '5 year' in col:
        return '5Y'
    if '10y' in col or '10 ans' in col or '10 year' in col:
        return '10Y'
    if 'inception' in col or 'création' in col or 'lancierung' in col:
        return 'Since Inception'
    return None

class PerformanceValidator(BaseValidator):
    """Validator for performance display rules."""
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        issues: List[ComplianceIssue] = []
        
        # Get all text content for age detection
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

        # Try to determine fund age from inception date
        is_new_fund = False
        
        # 1. Check performance table entries
        perf_entries = extraction_result.get('performance_table_entries', [])
        for entry in perf_entries:
            label = str(entry.get('label') or '').lower()
            if any(k in label for k in ['inception', 'création', 'launch', 'date d\'effet']):
                val = str(entry.get('raw', '') or entry.get('value', ''))
                if any(year in val for year in ['2024', '2025', '2026']):
                    is_new_fund = True
                    break
        
        # 2. Check metadata
        if not is_new_fund and metadata:
            if metadata.get('is_new_product') or metadata.get('is_new_strategy'):
                is_new_fund = True
            elif 'inception_date' in metadata:
                 idate = str(metadata['inception_date'])
                 if any(year in idate for year in ['2024', '2025', '2026']):
                     is_new_fund = True

        # 3. Check for recent launch mentions in text
        if not is_new_fund:
            recent_keywords = [
                "launched in 2024", "launched in 2025", "launched in 2026",
                "lancé en 2024", "lancé en 2025", "lancé en 2026",
                "newly launched", "nouvellement lancé"
            ]
            if any(k in all_text_lower for k in recent_keywords):
                is_new_fund = True

        # Determine target performance slide for annotations
        performance_sections = extraction_result.get('performance_sections', [])
        perf_slide = infer_performance_slide(extraction_result, performance_sections) or 4
        
        # Check if performance is on the cover page (Slide 1)
        has_perf_on_slide_1 = False
        
        # 1. Check sections
        for section in performance_sections:
            slide_num = section.get('slide_number')
            if slide_num == 1:
                has_perf_on_slide_1 = True
                break
        
        # 2. Fallback: Check text keywords on Slide 1
        # (This handles cases where chart analysis fails but text descriptions exist)
        if not has_perf_on_slide_1 and 'slides' in extraction_result and len(extraction_result['slides']) > 0:
            slide_1 = extraction_result['slides'][0]
            if isinstance(slide_1, dict):
                content = (slide_1.get('content', '') or slide_1.get('text', '')).lower()
                perf_keywords = ['performance', 'rendement', 'ytd', '1y', '3y', '5y', 'benchmark']
                if any(kw in content for kw in perf_keywords):
                    # Verify it's not just a disclaimer or ToC
                    if "table of contents" not in content and "sommaire" not in content:
                        has_perf_on_slide_1 = True

        if has_perf_on_slide_1:
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.PERFORMANCE_STARTS_DOCUMENT,
                rule_reference="Rule 89 - Performance Document Positioning",
                location="Slide 1 - Cover Page",
                slide_number=1,
                severity="error",
                message="Performance data should not be displayed on the cover page (Slide 1). It must not be the main focus.",
                context="Performance metrics/chart found on cover page. Main focus should be fund name, date, and key disclosures.",
                suggestion="Move performance section to slides 4-5 after risk disclosure and fund characteristics",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Check for required performance history (5Y, 10Y)
        periods_found = set()
        
        for section in performance_sections:
            for entry in section.get('entries', []):
                if entry.get('period'):
                    period_lower = entry.get('period').lower()
                    periods_found.add(period_lower)
        
        for entry in extraction_result.get('performance_table_entries', []):
            column = entry.get('column')
            if column:
                period = infer_period_from_column(column)
                if period:
                    period_lower = period.lower()
                    periods_found.add(period_lower)
        
        # Normalize period detection
        has_5y = any('5y' in p or '5 year' in p or '5-year' in p or '5yrs' in p for p in periods_found)
        has_10y = any('10y' in p or '10 year' in p or '10-year' in p or '10yrs' in p for p in periods_found)
        has_ytd = any('ytd' in p or 'year to date' in p or 'ytd' == p for p in periods_found)
        has_mtd = any('mtd' in p or 'month to date' in p or 'mtd' == p for p in periods_found)
        has_cumulative = any('cumulative' in p or 'cumul' in p or 'since inception' in p or 'since launch' in p for p in periods_found)
        has_1y = any('1y' in p or '1 year' in p or '1-year' in p or '12m' in p or '12 month' in p for p in periods_found)
        
        if not has_5y and not is_new_fund:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.INSUFFICIENT_PERFORMANCE_HISTORY,
                rule_reference="Rule 93 - Minimum Performance History",
                location=f"Slide {perf_slide} - Performance summary table",
                slide_number=perf_slide,
                severity="high",
                message="5-year performance history not found. Required if the fund is older than 5 years.",
                context="Performance table missing 5-year column. Essential for investor evaluation over medium term.",
                suggestion=f"Add '5Y' column to performance table on Slide {perf_slide} with net of fees returns",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        if not has_10y and not is_new_fund:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.INSUFFICIENT_PERFORMANCE_HISTORY,
                rule_reference="Rule 93 - Minimum Performance History",
                location=f"Slide {perf_slide} - Performance historical data section",
                slide_number=perf_slide,
                severity="high",
                message="10-year performance history not found. Required if the fund is older than 10 years.",
                context="Performance table missing 10-year column. Critical for long-term performance assessment.",
                suggestion=f"Add '10Y' or 'Since Inception' column to performance table on Slide {perf_slide}",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule: MTD Performance should not be shown
        if has_mtd:
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MTD_PERFORMANCE_SHOWN,
                rule_reference="Rule 11 - MTD Performance Prohibition",
                location=f"Slide {perf_slide} - Performance table or chart, MTD column",
                slide_number=perf_slide,
                severity="error",
                message="MTD (Month-to-Date) performance should not be displayed in marketing documents.",
                context="MTD column found in performance table. Month-to-date data is too volatile and unreliable.",
                suggestion=f"Remove MTD column from performance table on Slide {perf_slide}. Keep only YTD, 1Y, 3Y, 5Y, 10Y periods.",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule: YTD requires full history
        if has_ytd and not has_10y:
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.YTD_WITHOUT_FULL_HISTORY,
                rule_reference="Rule 95 - YTD Context Requirement",
                location=f"Slide {perf_slide} - Performance table, YTD column vs longer periods",
                slide_number=perf_slide,
                severity="warning",
                message="YTD (Year-to-Date) performance shown without full 10-year history. YTD should be accompanied by longer-term performance.",
                context="YTD column present but 10Y/inception columns missing. YTD alone is misleading without context.",
                suggestion=f"For funds older than 10Y: Add 10Y column alongside YTD. For younger funds on Slide {perf_slide}: Ensure 5Y or inception columns present.",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule: Cumulative performance requires minimum 3 years
        if has_cumulative:
            # Check if we have at least 3 years of history
            has_3y = any('3y' in p or '3 year' in p or '3-year' in p or '36m' in p or '36 month' in p for p in periods_found)
            if not has_3y:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.CUMULATIVE_LESS_THAN_3_YEARS,
                    rule_reference="Rule 98 - Cumulative Performance Minimum",
                    location=f"Slide {perf_slide} - Performance table, 'Since Inception' or 'Cumulative' row/column",
                    slide_number=perf_slide,
                    severity="error",
                    message="Cumulative performance shown but fund has less than 3 years of history. Cumulative performance requires minimum 3 years.",
                    context="'Since Inception' or 'Cumulative' return shown for fund less than 3 years old. Fund too new for reliable performance assessment.",
                    suggestion=f"Remove cumulative/inception performance from Slide {perf_slide} if fund created less than 3 years ago. Wait until sufficient history exists.",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule: Performance less than 1 year should not be shown
        if not has_1y and (has_ytd or has_cumulative):
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.PERFORMANCE_LESS_THAN_1_YEAR,
                rule_reference="Rule 91 - Minimum 1-Year History",
                location=f"Slide {perf_slide} - Performance table YTD or inception columns",
                slide_number=perf_slide,
                severity="warning",
                message="Performance data shown for fund with less than 1 year of history. Marketing documents should wait until fund has at least 1 year of performance.",
                context="YTD or cumulative performance shown for very new fund. Insufficient history for meaningful performance assessment.",
                suggestion=f"Exclude performance data from Slide {perf_slide} until fund reaches 1 year anniversary. Show fund characteristics instead.",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule: Track record for retail (institutional track record should not be shown to retail)
        if client_type == ClientType.RETAIL:
            track_record_phrases = [
                "institutional track record", "track record institutionnel",
                "performance institutionnelle", "institutional performance",
                "historique institutionnel"
            ]
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
            if any(phrase in all_text_lower for phrase in track_record_phrases):
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.TRACK_RECORD_FOR_RETAIL,
                    rule_reference="Rule 127 - Institutional Performance Restrictions",
                    location=f"Slide {perf_slide} - Performance table or historical performance section",
                    slide_number=perf_slide,
                    severity="error",
                    message="Institutional track record should not be shown to retail clients.",
                    context="Institutional track record or performance found in retail document. Institutional data misleads retail investors.",
                    suggestion=f"Replace institutional track record on Slide {perf_slide} with retail share class performance only, or restrict document to professional clients.",
                    client_type=client_type,
                    fund_type=fund_type
                ))

        # Check for Benchmark Comparison
        has_benchmark = False
        
        # Check table labels
        for entry in extraction_result.get('performance_table_entries', []):
            label = (entry.get('label') or '').lower()
            if 'benchmark' in label or 'index' in label or 'indice' in label or 'vergleichsindex' in label:
                has_benchmark = True
                break
        
        if metadata and metadata.get('benchmark_name'):
            has_benchmark = True

        # Check if we have ANY performance data to validate against
        has_perf_data = bool(performance_sections or extraction_result.get('performance_table_entries'))
        if not has_perf_data and 'slides' in extraction_result:
             # Relaxed check: if we see performance keywords in body, assume performance is discussed
             all_content = ""
             for slide in extraction_result['slides']:
                 if isinstance(slide, dict):
                     all_content += (slide.get('content', '') or "").lower()
             if "performance" in all_content or "rendement" in all_content:
                  has_perf_data = True

        if not has_benchmark and has_perf_data:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_BENCHMARK_COMPARISON,
                rule_reference="Rule 110 - Benchmark Comparison Requirement",
                location=f"Slide {perf_slide} - Performance table or chart, benchmark row/line missing",
                slide_number=perf_slide,
                severity="warning",
                message="Performance is shown but no benchmark comparison detected. Performance must be compared to the official benchmark on the same slide.",
                context="Fund performance table exists but benchmark/index row missing. Investors need performance context.",
                suggestion=f"Add benchmark comparison on Slide {perf_slide} (typically as second row in table or second line in chart) with official index name and performance.",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Check for Net Performance indication (for retail clients)
        if client_type == ClientType.RETAIL and has_perf_data:
            has_net_indication = False
            
            # Check table labels/columns
            for entry in extraction_result.get('performance_table_entries', []):
                label = (entry.get('label') or '').lower()
                column = (entry.get('column') or '').lower()
                if 'net' in label or 'net' in column or 'nette' in label or 'nette' in column:
                    has_net_indication = True
                    break
            
            # Check text content
            if not has_net_indication:
                if 'net of fees' in all_text_lower or 'nettes de frais' in all_text_lower or 'net performance' in all_text_lower or 'performance nette' in all_text_lower:
                    has_net_indication = True
            
            if not has_net_indication:
                 issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.MISSING_NET_PERFORMANCE_INDICATION,
                    rule_reference="Rule 120 - Net Performance Disclosure",
                    location=f"Slide {perf_slide} - Performance table header or footnote",
                    slide_number=perf_slide,
                    severity="warning",
                    message="Performance shown to retail clients must be net of fees. No indication of 'Net' performance found.",
                    context="Performance table for retail investor shows returns without 'Net of fees' label. Retail must see realistic net returns.",
                    suggestion=f"Add 'Net' label to performance table header on Slide {perf_slide} or add footnote: '* Performance shown net of fund management fees'",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Germany-specific rule: Fee loading in performance (Rule 3)
        # For German documents: first year must include max subscription fees, last year must include redemption fees
        if metadata and metadata.get('language_code') == 'DE':
            self._validate_germany_fee_loading(
                extraction_result, metadata, client_type, fund_type, perf_slide, issues
            )
        
        return issues
    
    def _validate_germany_fee_loading(
        self,
        extraction_result: Dict[str, Any],
        metadata: Dict[str, Any],
        client_type: Optional[Any],
        fund_type: Optional[Any],
        perf_slide: int,
        issues: List[ComplianceIssue]
    ) -> None:
        """
        Validate Germany-specific fee loading in performance tables (Rule 3)
        
        Rule 3: "la première année de présentation des performances glissantes incorpore 
                 les frais de souscription maximum. Il en est de même pour les frais de 
                 rachat maximum (acquis ou non acquis au fonds) prévus dans le prospectus"
        
        Translation: "the first year of rolling performance presentation must incorporate 
                     maximum subscription fees. The same applies to maximum redemption fees 
                     (whether or not acquired by the fund) provided for in the prospectus"
        """
        # Only applies to German documents
        if metadata.get('language_code') != 'DE':
            return
        
        # Check for performance data
        perf_entries = extraction_result.get('performance_table_entries', [])
        if not perf_entries:
            return
        
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
        
        # Look for performance years (1Y, 2Y, 3Y, 5Y, 10Y, inception)
        # We need to check if first year and last year include fees
        
        has_first_year_fee_notation = False
        has_last_year_fee_notation = False
        has_year_columns = False
        
        # Check for year columns and fee mentions
        for entry in perf_entries:
            label = str(entry.get('label', '')).lower()
            value = str(entry.get('value', '')).lower()
            
            # Check for year columns (1Y, 2Y, 3Y, 5Y, 10Y)
            if any(y in label for y in ['1y', '1 year', '1 jahr', '12m']):
                has_year_columns = True
                # Check if this entry mentions fees
                if any(f in value for f in ['gebühr', 'gebühren', 'frais', 'fee', 'fees', 'souscription', 'subscription']):
                    has_first_year_fee_notation = True
        
        # Check text for fee loading mentions
        fee_loading_keywords = [
            'gebühren eingerechnet', 'gebühren berücksichtigt',
            'frais de souscription inclus', 'frais inclus',
            'fee loaded', 'fees included', 'subscription fees',
            'subscription fees included', 'inkl. gebühren',
            'einschließlich gebühren', 'including fees'
        ]
        
        has_fee_loading_mention = any(kw in all_text_lower for kw in fee_loading_keywords)
        
        # Check for prospectus reference
        has_prospectus_ref = any(w in all_text_lower for w in ['prospektus', 'prospectus', 'prospectus', 'prospekt'])
        
        # If performance table exists but no fee loading mention and prospectus referenced
        if has_year_columns and not has_fee_loading_mention:
            # Flag missing fee loading disclosure
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_PERFORMANCE_DISCLAIMER,
                rule_reference="Rule 3 - Germany Fee Loading in Performance (Subscription Fees)",
                location=f"Slide {perf_slide} - Performance table, 1-year column footnote",
                slide_number=perf_slide,
                severity="high",
                message="German document: First year performance must include maximum subscription fees (Gebühren eingerechnet)",
                context=(
                    "Performance table shown for German audience without disclosure that "
                    "first year includes subscription fees as per prospectus. Rule 3 requires "
                    "this disclosure for German marketing materials."
                ),
                suggestion=(
                    f"Add footnote to 1-year performance column on Slide {perf_slide}: "
                    "'* 1-year performance includes maximum subscription fees as per prospectus' "
                    "or '* Die 1-Jahres-Performance berücksichtigt die Gebühren des Prospekts'"
                ),
                client_type=client_type,
                fund_type=fund_type,
                details={
                    "rule": "German Rule 3 - Fee Loading",
                    "requirement": "subscription_fees_in_first_year",
                    "document_language": metadata.get('language_code')
                }
            ))
        
        # Check for redemption fee mention for last year
        redemption_keywords = [
                'rücknahmegebühren', 'rücknahmegebühr',
            'frais de rachat', 'frais rachat',
            'redemption fees', 'redemption fee',
            'exit fees', 'frais de sortie'
        ]
        
        has_redemption_mention = any(kw in all_text_lower for kw in redemption_keywords)
        
        if has_year_columns and not has_redemption_mention and has_prospectus_ref:
            # Flag missing redemption fee disclosure for last year
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_PERFORMANCE_DISCLAIMER,
                rule_reference="Rule 3 - Germany Fee Loading in Performance (Redemption Fees)",
                location=f"Slide {perf_slide} - Performance table, latest year column footnote",
                slide_number=perf_slide,
                severity="high",
                message="German document: Performance must disclose maximum redemption fees for last year period",
                context=(
                    "Performance table shown for German audience without disclosure of "
                    "redemption fees (whether acquired or not) as per prospectus. "
                    "Rule 3 requires this for complete fee transparency."
                ),
                suggestion=(
                    f"Add footnote to latest period column on Slide {perf_slide}: "
                    "'* Performance includes maximum redemption fees (acquired and unacquired) as per prospectus' "
                    "or '* Die Wertentwicklung berücksichtigt die maximalen Rücknahmegebühren des Prospekts'"
                ),
                client_type=client_type,
                fund_type=fund_type,
                details={
                    "rule": "German Rule 3 - Fee Loading",
                    "requirement": "redemption_fees_in_last_year",
                    "document_language": metadata.get('language_code')
                }
            ))
