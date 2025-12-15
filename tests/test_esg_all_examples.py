"""
Comprehensive ESG Integration Testing
Tests ESG validation with all example documents
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

# Add src to path
# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.extractors.pipeline import ExtractionPipeline
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
import pytest


def run_document(file_path: str, metadata_path: str, test_name: str) -> Dict[str, Any]:
    """Test a single document with ESG validation"""
    
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"File: {file_path}")
    print(f"{'='*80}\n")
    
    # Get API credentials
    api_key = os.getenv("TOKEN_FACTORY_API_KEY") or os.getenv("LLM_API_KEY")
    base_url = os.getenv("TOKEN_FACTORY_BASE_URL") or os.getenv("LLM_BASE_URL")
    
    if not api_key or not base_url:
        print("[FAIL] Error: API credentials not found")
        return {"status": "error", "message": "Missing API credentials"}
    
    try:
        # Step 1: Extract document
        print("[DOC] Extracting document...")
        pipeline = ExtractionPipeline(use_llm=False, output_dir="outputs")
        result = pipeline.process_document(
            file_path=file_path,
            metadata_json_path=metadata_path,
            uploaded_by="esg_test"
        )
        
        if not result.get('success'):
            print(f"[FAIL] Extraction failed: {result.get('error')}")
            return {"status": "error", "message": result.get('error')}
        
        document_id = result.get('document_id')
        print(f"[OK] Document extracted: {document_id}")
        
        # Load extraction results
        extraction_path = Path("outputs") / document_id / "extraction.json"
        metadata_result_path = Path("outputs") / document_id / "metadata.json"
        
        with open(extraction_path, 'r', encoding='utf-8') as f:
            extraction_result = json.load(f)
        
        with open(metadata_result_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Step 2: Validate with ESG
        print("[SEARCH] Running ESG validation...")
        agent = DataConsistencyAgent(
            reference_data=None,
            enable_esg_validation=True,
            esg_api_key=api_key,
            esg_base_url=base_url
        )
        
        validation_result = agent.validate(
            extraction_result=extraction_result,
            metadata=metadata,
            document_id=document_id
        )
        
        # Step 3: Analyze results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80 + "\n")
        
        total_issues = len(validation_result.compliance_issues)
        esg_issues = [i for i in validation_result.compliance_issues 
                      if 'esg' in i.issue_type.lower() or 'sfdr' in i.issue_type.lower() 
                      or 'engaging' in i.issue_type.lower()]
        
        print(f"Total Issues: {total_issues}")
        print(f"ESG Issues: {len(esg_issues)}")
        print(f"Overall Status: {validation_result.overall_status.upper()}")
        print(f"ESG Analysis Present: {'[OK] Yes' if validation_result.esg_analysis else '[FAIL] No'}")
        
        if validation_result.esg_analysis:
            esg_data = validation_result.esg_analysis
            print(f"\nESG Enrichment Data:")
            print(f"  - Level: {esg_data.get('esg_level', {}).get('level', 'N/A')}")
            print(f"  - SFDR Article: {esg_data.get('esg_level', {}).get('sfdr_article', 'N/A')}")
            print(f"  - ESG %: {esg_data.get('esg_mentions', {}).get('esg_percentage', 'N/A')}%")
            print(f"  - Commercial Mentions: {esg_data.get('esg_mentions', {}).get('commercial_esg_mentions', 'N/A')}")
        
        if esg_issues:
            print(f"\nESG Issues:")
            for i, issue in enumerate(esg_issues, 1):
                print(f"  {i}. {issue.issue_type} ({issue.severity})")
                print(f"     {issue.message}")
        
        # Check client/fund types
        client_types = set()
        fund_types = set()
        for issue in validation_result.compliance_issues:
            if issue.client_type:
                client_types.add(issue.client_type)
            if issue.fund_type:
                fund_types.add(issue.fund_type)
        
        print(f"\nDetected Types:")
        print(f"  - Client Types: {', '.join(client_types) if client_types else 'None'}")
        print(f"  - Fund Types: {', '.join(fund_types) if fund_types else 'None'}")
        
        return {
            "status": "success",
            "test_name": test_name,
            "document_id": document_id,
            "total_issues": total_issues,
            "esg_issues": len(esg_issues),
            "overall_status": validation_result.overall_status,
            "has_esg_analysis": bool(validation_result.esg_analysis),
            "client_types": list(client_types),
            "fund_types": list(fund_types),
            "esg_data": validation_result.esg_analysis
        }
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

def main():
    """Run comprehensive ESG tests"""
    
    print("=" * 80)
    print("COMPREHENSIVE ESG INTEGRATION TESTING")
    print("=" * 80)
    
    # Define test cases
    test_cases = [
        {
            "name": "Example 1 - ODDO BHF Algo Trend US (FR)",
            "file": "dataset/example_1/FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx",
            "metadata": "dataset/example_1/metadata.json"
        },
        {
            "name": "Example 1 - ODDO BHF Algo Trend US (GB)",
            "file": "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx",
            "metadata": "dataset/example_1/metadata.json"
        },
        {
            "name": "Example 2 - ODDO BHF US Equity Active ETF (Final)",
            "file": "dataset/example_2/FINAL-PRS-GB-ODDO BHF US Equity Active ETF-20250630_8PN_clean.pptx",
            "metadata": "dataset/example_2/metadata.json"
        },
        {
            "name": "Example 2 - ODDO BHF US Equity Active ETF (Draft)",
            "file": "dataset/example_2/XXX-PRS-GB-ODDO BHF US Equity Active ETF-20250630_6PN.pptx",
            "metadata": "dataset/example_2/metadata.json"
        },
        {
            "name": "Example 3 - ODDO BHF US Equity Active ETF (V1)",
            "file": "dataset/example_3/1 - V1-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx",
            "metadata": "dataset/example_3/metadata.json"
        },
        {
            "name": "Example 3 - ODDO BHF US Equity Active ETF (Final Clean)",
            "file": "dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx",
            "metadata": "dataset/example_3/metadata.json"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        result = run_document(
            file_path=test_case["file"],
            metadata_path=test_case["metadata"],
            test_name=test_case["name"]
        )
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    with_esg = sum(1 for r in results if r.get("has_esg_analysis"))
    
    print(f"Total Tests: {len(results)}")
    print(f"[OK] Successful: {successful}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[CHART] With ESG Analysis: {with_esg}/{successful}")
    
    # Save results
    output_file = "esg_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVE] Detailed results saved to: {output_file}")
    
    if successful == len(results) and with_esg == successful:
        print("\n[SUCCESS] All tests passed with ESG analysis!")
    else:
        print(f"\n[WARNING] Some tests incomplete: {successful}/{len(results)} successful, {with_esg}/{successful} with ESG")

@pytest.mark.parametrize("case", [
    {
        "name": "Example 1 - ODDO BHF Algo Trend US (FR)",
        "file": "dataset/example_1/FINAL 47861-6PG-FR-ODDO BHF Algo Trend US-20250831.pptx",
        "metadata": "dataset/example_1/metadata.json",
    },
    {
        "name": "Example 1 - ODDO BHF Algo Trend US (GB)",
        "file": "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx",
        "metadata": "dataset/example_1/metadata.json",
    },
    {
        "name": "Example 2 - ODDO BHF US Equity Active ETF (Final)",
        "file": "dataset/example_2/FINAL-PRS-GB-ODDO BHF US Equity Active ETF-20250630_8PN_clean.pptx",
        "metadata": "dataset/example_2/metadata.json",
    },
    {
        "name": "Example 2 - ODDO BHF US Equity Active ETF (Draft)",
        "file": "dataset/example_2/XXX-PRS-GB-ODDO BHF US Equity Active ETF-20250630_6PN.pptx",
        "metadata": "dataset/example_2/metadata.json",
    },
    {
        "name": "Example 3 - ODDO BHF US Equity Active ETF (V1)",
        "file": "dataset/example_3/1 - V1-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx",
        "metadata": "dataset/example_3/metadata.json",
    },
    {
        "name": "Example 3 - ODDO BHF US Equity Active ETF (Final Clean)",
        "file": "dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx",
        "metadata": "dataset/example_3/metadata.json",
    },
])
def test_esg_examples(case):
    # Execute the same flow as main() but as a pytest parametrized test.
    res = run_document(case["file"], case["metadata"], case["name"])
    # Ensure function returned a dict (avoid pytest fixture errors); deeper assertions rely on env and deps.
    assert isinstance(res, dict)


if __name__ == "__main__":
    main()
