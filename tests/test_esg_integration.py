"""
Test ESG Integration with Data Consistency Agent
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.data_consistency_agent import DataConsistencyAgent

def test_esg_validation():
    """Test ESG validation with a real document"""
    
    print("=" * 80)
    print("[TEST] TESTING ESG COMPLIANCE INTEGRATION")
    print("=" * 80)
    print()
    
    # Use example document
    test_file = "dataset/example_2/XXX-PRS-GB-ODDO BHF US Equity Active ETF-20250630_6PN.pptx"
    
    if not Path(test_file).exists():
        # Try alternative path
        test_file = "dataset/example_1/1369-PRS-FR-ODDO BHF Génération - 20231231 - FVv1.pptx"
    
    if not Path(test_file).exists():
        print("[FAIL] No test document found. Please ensure dataset exists.")
        return
    
    print(f"[DOC] Test Document: {test_file}")
    print()
    
    # Create mock extraction result with required fields
    extraction_result = {
        'file_path': test_file,
        'document_id': 'test-esg-001',
        'text': """
        ODDO BHF US Equity Active ETF
        
        This fund promotes ESG (Environmental, Social and Governance) characteristics 
        in accordance with Article 8 of the SFDR regulation.
        
        Our sustainable investment approach focuses on:
        - Environmental criteria: Climate change mitigation
        - Social criteria: Human rights and labor standards
        - Governance criteria: Board independence and transparency
        
        The fund integrates ESG factors systematically in the investment process.
        Sustainability is at the core of our investment philosophy.
        
        We believe in responsible investing and sustainable development.
        ESG integration enhances long-term value creation.
        
        Performance data as of 31/12/2023
        Risk Warning: Past performance is not a reliable indicator of future results.
        Capital at risk.
        """,
        'structure': {
            'slides': [
                {'title': 'Cover Page', 'content': 'ODDO BHF US Equity Active ETF'},
                {'title': 'ESG Approach', 'content': 'Our sustainable investment approach...'},
                {'title': 'Investment Process', 'content': 'ESG integration...'},
                {'title': 'Performance', 'content': 'Performance data...'},
                {'title': 'Risk Disclaimers', 'content': 'Risk Warning...'}
            ]
        },
        'disclaimers': [
            'Past performance is not a reliable indicator of future results.',
            'Capital at risk. You may not get back the amount invested.'
        ]
    }
    
    metadata = {
        'fund_name': 'ODDO BHF US Equity Active ETF',
        'sfdr_article': 8,  # Article 8 - should have < 10% ESG content
        'document_type': 'marketing',
        'file_path': test_file,
        'is_professional_client': False
    }
    
    print("⚙️  Initializing Data Consistency Agent with ESG Validation...")
    print()
    
    # Get API credentials
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    
    if not api_key or not base_url:
        print("[FAIL] Error: TOKEN_FACTORY_API_KEY and TOKEN_FACTORY_BASE_URL must be set in .env")
        print()
        print("Required environment variables:")
        print("  - TOKEN_FACTORY_API_KEY")
        print("  - TOKEN_FACTORY_BASE_URL")
        return
    
    try:
        # Initialize agent with ESG validation enabled
        agent = DataConsistencyAgent(
            enable_esg_validation=True,
            esg_api_key=api_key,
            esg_base_url=base_url
        )
        
        print("[OK] Agent initialized successfully")
        print()
        print("[SEARCH] Running ESG Compliance Validation...")
        print("   - Text Analysis: Detecting ESG level (Article 6/8/9)")
        print("   - ESG Percentage Calculation: Measuring ESG content")
        print("   - Vision Analysis: Analyzing slides for visual ESG content")
        print()
        
        # Run validation
        result = agent.validate(extraction_result, metadata)
        
        print("=" * 80)
        print("[CHART] VALIDATION RESULTS")
        print("=" * 80)
        print()
        
        # Show compliance issues
        if result.compliance_issues:
            print(f"[WARNING]  Found {len(result.compliance_issues)} compliance issue(s):")
            print()
            
            for i, issue in enumerate(result.compliance_issues, 1):
                print(f"{i}. {issue.severity.upper()}: {issue.issue_type}")
                print(f"   Location: {issue.location}")
                print(f"   Message: {issue.message}")
                if issue.context:
                    print(f"   Context: {issue.context[:150]}...")
                if issue.suggestion:
                    print(f"   Suggestion: {issue.suggestion[:150]}...")
                print()
        else:
            print("[OK] No compliance issues found")
            print()
        
        # Show overall status
        print(f"Overall Status: {result.overall_status.upper()}")
        print()
        
        # Save result to file
        output_file = "test_esg_output.json"
        output_data = {
            'document_id': result.document_id,
            'overall_status': result.overall_status,
            'compliance_issues': [
                {
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'location': issue.location,
                    'message': issue.message,
                    'context': issue.context,
                    'suggestion': issue.suggestion,
                    'client_type': issue.client_type,
                    'fund_type': issue.fund_type,
                    'slide_number': issue.slide_number,
                    'country': issue.country
                }
                for issue in result.compliance_issues
            ]
        }
        
        # Include ESG enrichment data if available
        if result.esg_analysis:
            output_data['esg_analysis'] = result.esg_analysis
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SAVE] Results saved to: {output_file}")
        print()
        
        # Show summary
        print("=" * 80)
        print("[UP] SUMMARY")
        print("=" * 80)
        print()
        print(f"Total Compliance Issues: {len(result.compliance_issues)}")
        
        # Count by severity
        critical = sum(1 for i in result.compliance_issues if i.severity == "critical")
        errors = sum(1 for i in result.compliance_issues if i.severity == "error")
        warnings = sum(1 for i in result.compliance_issues if i.severity == "warning")
        
        if critical > 0:
            print(f"  [RED] Critical: {critical}")
        if errors > 0:
            print(f"  [FAIL] Errors: {errors}")
        if warnings > 0:
            print(f"  [WARNING]  Warnings: {warnings}")
        
        print()
        print("[OK] Test completed successfully!")
        
    except Exception as e:
        print(f"[FAIL] Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    test_esg_validation()
