"""
Performance Validator
"""
import re
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType, ClientType
from .base import BaseValidator

def infer_period_from_column(column_name: str) -> Optional[str]:
    """Infer time period from column name."""
    col = column_name.lower()
    if 'ytd' in col: return 'YTD'
    if 'mtd' in col: return 'MTD'
    if '1y' in col or '1 an' in col or '1 year' in col: return '1Y'
    if '3y' in col or '3 ans' in col or '3 year' in col: return '3Y'
    if '5y' in col or '5 ans' in col or '5 year' in col: return '5Y'
    if '10y' in col or '10 ans' in col or '10 year' in col: return '10Y'
    if 'inception' in col or 'création' in col or 'lancierung' in col: return 'Since Inception'
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
        
        # Check if performance is on the cover page (Slide 1)
        performance_sections = extraction_result.get('performance_sections', [])
        for section in performance_sections:
            slide_num = section.get('slide_number')
            if slide_num == 1:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.PERFORMANCE_STARTS_DOCUMENT,
                    rule_reference="Section 4.3",
                    location="Slide 1",
                    slide_number=1,
                    severity="error",
                    message="Performance data should not be displayed on the cover page (Slide 1). It must not be the main focus.",
                    context="Performance found on first slide",
                    suggestion="Move performance data to later slides (typically slide 3 or later)",
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
        
        if not has_5y:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.INSUFFICIENT_PERFORMANCE_HISTORY,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="5-year performance history not found. Required if the fund is older than 5 years.",
                context="Missing 5-year performance history",
                suggestion="Add 5-year performance data if fund is older than 5 years",
                client_type=client_type,
                fund_type=fund_type
            ))
            
        if not has_10y:
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.INSUFFICIENT_PERFORMANCE_HISTORY,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="10-year performance history not found. Required if the fund is older than 10 years.",
                context="Missing 10-year performance history",
                suggestion="Add 10-year performance data if fund is older than 10 years",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule: MTD Performance should not be shown
        if has_mtd:
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MTD_PERFORMANCE_SHOWN,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="error",
                message="MTD (Month-to-Date) performance should not be displayed in marketing documents.",
                context="MTD performance found in document",
                suggestion="Remove MTD performance data",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Rule: YTD requires full history
        if has_ytd and not has_10y:
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.YTD_WITHOUT_FULL_HISTORY,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="YTD (Year-to-Date) performance shown without full 10-year history. YTD should be accompanied by longer-term performance.",
                context="YTD performance without full history",
                suggestion="Add longer-term performance history (5Y, 10Y) alongside YTD",
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
                    rule_reference="Section 4.3",
                    location="Performance Section",
                    severity="error",
                    message="Cumulative performance shown but fund has less than 3 years of history. Cumulative performance requires minimum 3 years.",
                    context="Cumulative performance without sufficient history",
                    suggestion="Either remove cumulative performance or ensure fund has at least 3 years of history",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        # Rule: Performance less than 1 year should not be shown
        if not has_1y and (has_ytd or has_cumulative):
            # If showing YTD or cumulative but no 1Y, might be too new
            issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.PERFORMANCE_LESS_THAN_1_YEAR,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="Performance data shown for fund with less than 1 year of history. Marketing documents should wait until fund has at least 1 year of performance.",
                context="Performance shown for very new fund",
                suggestion="Wait until fund has at least 1 year of performance history before including in marketing materials",
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
                    rule_reference="Section 4.3",
                    location="Performance Section",
                    severity="error",
                    message="Institutional track record should not be shown to retail clients.",
                    context="Institutional track record found in retail document",
                    suggestion="Remove institutional track record or use retail share class performance only",
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

        if not has_benchmark and (performance_sections or extraction_result.get('performance_table_entries')):
             issues.append(ComplianceIssue(
                issue_type=ComplianceIssueType.MISSING_BENCHMARK_COMPARISON,
                rule_reference="Section 4.3",
                location="Performance Section",
                severity="warning",
                message="Performance is shown but no benchmark comparison detected. Performance must be compared to the official benchmark.",
                context="No benchmark found in performance data",
                suggestion="Add benchmark comparison alongside fund performance",
                client_type=client_type,
                fund_type=fund_type
            ))
        
        # Check for Net Performance indication (for retail clients)
        if client_type == ClientType.RETAIL and (performance_sections or extraction_result.get('performance_table_entries')):
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
                    rule_reference="Section 4.3",
                    location="Performance Section",
                    severity="warning",
                    message="Performance shown to retail clients must be net of fees. No indication of 'Net' performance found.",
                    context="Performance data without 'Net' indication",
                    suggestion="Ensure performance is net of fees and labeled as such (e.g., 'Net Performance')",
                    client_type=client_type,
                    fund_type=fund_type
                ))
        
        return issues
