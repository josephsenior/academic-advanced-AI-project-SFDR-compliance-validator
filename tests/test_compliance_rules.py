import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Standard imports - no need for complex importlib hacks since we use 'backend' now
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
from backend.extractors.rules.enums import ComplianceIssueType

class TestComplianceRules(unittest.TestCase):
    def setUp(self):
        self.agent = DataConsistencyAgent()

    def test_performance_on_slide_1(self):
        extraction_result = {
            'performance_sections': [
                {'slide_number': 1, 'entries': [{'value': 10.0, 'period': '1Y'}]}
            ]
        }
        result = self.agent.validate(extraction_result)
        
        issues = [i for i in result.compliance_issues if i.issue_type == ComplianceIssueType.PERFORMANCE_STARTS_DOCUMENT]
        self.assertTrue(any("Slide 1" in i.message for i in issues))

    def test_missing_history(self):
        extraction_result = {
            'performance_sections': [
                {'slide_number': 3, 'entries': [{'value': 10.0, 'period': '1Y'}]}
            ]
        }
        result = self.agent.validate(extraction_result)
        
        issues = [i for i in result.compliance_issues if i.issue_type == ComplianceIssueType.INSUFFICIENT_PERFORMANCE_HISTORY]
        self.assertTrue(any("5-year" in i.message for i in issues))
        self.assertTrue(any("10-year" in i.message for i in issues))

    def test_missing_cover_page_info(self):
        extraction_result = {}
        metadata = {'title_information': {}} # Empty title info
        
        result = self.agent.validate(extraction_result, metadata=metadata)
        
        issues = [i for i in result.compliance_issues if "Fund Name" in i.message]
        self.assertTrue(len(issues) > 0)

    def test_missing_risk_scale(self):
        extraction_result = {'risk_indicators': {}} # Empty risk indicators
        
        result = self.agent.validate(extraction_result)
        
        issues = [i for i in result.compliance_issues if "Risk Scale" in i.message]
        self.assertTrue(len(issues) > 0)

    def test_missing_disclaimers(self):
        extraction_result = {
            'disclaimers': ["Some generic text"],
            'performance_sections': [{'slide_number': 3, 'entries': []}] # Trigger past perf check
        }
        
        result = self.agent.validate(extraction_result)
        
        issues_capital = [i for i in result.compliance_issues if i.issue_type == ComplianceIssueType.MISSING_STANDARD_DISCLAIMER]
        self.assertTrue(any("Capital Loss" in i.message for i in issues_capital))
        
        issues_perf = [i for i in result.compliance_issues if i.issue_type == ComplianceIssueType.MISSING_PERFORMANCE_DISCLAIMER]
        self.assertTrue(any("Past performance" in i.message for i in issues_perf))

    def test_valid_compliance(self):
        extraction_result = {
            'performance_sections': [
                {'slide_number': 3, 'entries': [
                    {'value': 10.0, 'period': '1Y'},
                    {'value': 20.0, 'period': '5Y'},
                    {'value': 30.0, 'period': '10Y'}
                ]}
            ],
            'risk_indicators': {'sri': 4, 'investment_horizon': '5 years'},
            'disclaimers': [
                "Risque de perte en capital.",
                "Les performances passées ne préjugent pas des performances futures."
            ]
        }
        metadata = {
            'title_information': {
                'fund_name': 'Test Fund',
                'document_date': '2023-01-01'
            }
        }
        
        result = self.agent.validate(extraction_result, metadata=metadata)
        
        # Should have no errors, maybe some warnings if I missed something, but let's check for critical errors
        errors = [i for i in result.compliance_issues if i.severity == "error"]
        self.assertEqual(len(errors), 0, f"Found errors: {[e.message for e in errors]}")

if __name__ == '__main__':
    unittest.main()
