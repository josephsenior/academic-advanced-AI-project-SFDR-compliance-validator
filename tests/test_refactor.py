
import sys
import os
import logging

# Add project root to path
sys.path.append("C:\\Users\\GIGABYTE\\Desktop\\Advanced Ai Project")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_loading():
    print("Testing DataConsistencyAgent loading...")
    try:
        import backend.extractors
        print(f"backend.extractors file: {backend.extractors.__file__}")
        with open(backend.extractors.__file__, 'r') as f:
            content = f.read()
            print("Content of __init__.py around line 70-80:")
            lines = content.splitlines()
            for i, line in enumerate(lines[70:90], 70):
                print(f"{i}: {line}")
        
        from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
        print("Successfully imported DataConsistencyAgent")
        
        agent = DataConsistencyAgent(enable_esg_validation=False) # Disable ESG for basic load test to avoid complex setup
        print("Successfully instantiated DataConsistencyAgent (ESG disabled)")
        
        # Create dummy extraction result
        dummy_result = {
            "pages": [{"content": "This is a test fund document. Fund A. Date: 2025-01-01."}],
            "disclaimers": ["Past performance is not a reliable indicator."],
            "structure": {"countries_detected": ["Germany"]},
            "country_entries": [{"country": "Germany", "heading": "Marketing in Germany"}]
        }
        
        dummy_metadata = {
            "fund_name": "Test Fund",
            "title_information": {"fund_name": "Test Fund"},
            "target_audience": "Professional"
        }
        
        print("Running validation...")
        result = agent.validate(dummy_result, dummy_metadata)
        print(f"Validation finished. Issues found: {len(result.compliance_issues)}")
        for issue in result.compliance_issues:
            print(f"- {issue.issue_type}: {issue.message}")
            
        print("Test PASSED")
        
    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_loading()
