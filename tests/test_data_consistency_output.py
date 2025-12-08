"""
Test script to generate data consistency output JSON results
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent, ReferenceData
from src.utils.validation_report_generator import ValidationReportGenerator
import json


def test_data_consistency_output():
    """Test data consistency validation and generate all output files"""
    
    print("=" * 70)
    print("Data Consistency Output Test")
    print("=" * 70)
    print()
    
    # Step 1: Find a test document
    print("Step 1: Finding test document...")
    test_docs = [
        "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "dataset/example_1/47861-6PG-GB-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "uploads/2fce0951-c887-49cb-af4d-f1dd5bcfa67f_47861-6PG-FR-ODDO_BHF_Algo_Trend_US-20250831_v3_pn.pptx"
    ]
    
    doc_path = None
    for path in test_docs:
        if Path(path).exists():
            doc_path = path
            break
    
    if not doc_path:
        print("[ERROR] No test document found!")
        return
    
    print(f"[OK] Using document: {doc_path}")
    print()
    
    # Step 2: Process document
    print("Step 2: Processing document through pipeline...")
    try:
        pipeline = ExtractionPipeline(use_llm=False)
        pipeline_result = pipeline.process_document(doc_path)
        
        if pipeline_result['status'] != 'success':
            print(f"[ERROR] Pipeline failed: {pipeline_result.get('errors', [])}")
            return
        
        document_id = pipeline_result['document_id']
        print(f"[OK] Document processed: {document_id}")
        print()
    except Exception as e:
        print(f"[ERROR] Error processing document: {e}")
        return
    
    # Step 3: Run data consistency validation
    print("Step 3: Running data consistency validation...")
    try:
        agent = DataConsistencyAgent(reference_data=None)  # No reference data for this test
        validation_result = agent.validate(
            extraction_result=pipeline_result['extraction_result'],
            metadata=pipeline_result['metadata'],
            document_id=document_id
        )
        print(f"[OK] Validation completed: {validation_result.overall_status}")
        print(f"   - Source/Date Issues: {len(validation_result.source_date_issues)}")
        print(f"   - Numerical Inconsistencies: {len(validation_result.numerical_inconsistencies)}")
        print(f"   - Cross-Reference Issues: {len(validation_result.cross_reference_issues)}")
        print()
    except Exception as e:
        print(f"[ERROR] Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Generate all report files
    print("Step 4: Generating report files...")
    try:
        report_generator = ValidationReportGenerator(output_dir="outputs")
        document_name = Path(doc_path).name
        reports = report_generator.generate_all_reports(
            validation_result=validation_result,
            document_id=document_id,
            document_name=document_name
        )
        
        print("[OK] Reports generated successfully:")
        for report_type, report_path in reports.items():
            file_size = Path(report_path).stat().st_size if Path(report_path).exists() else 0
            print(f"   - {report_type.upper()}: {report_path} ({file_size:,} bytes)")
        print()
    except Exception as e:
        print(f"[ERROR] Error generating reports: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Display JSON result summary
    print("Step 5: Displaying JSON result summary...")
    json_path = reports.get('json')
    if json_path and Path(json_path).exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            print("[OK] JSON Result Summary:")
            print(f"   - Document ID: {json_data.get('document_id')}")
            print(f"   - Validation Timestamp: {json_data.get('validation_timestamp')}")
            print(f"   - Overall Status: {json_data.get('overall_status')}")
            print(f"   - Has Errors: {json_data.get('has_errors')}")
            print(f"   - Has Warnings: {json_data.get('has_warnings')}")
            print(f"   - Total Tables Checked: {json_data.get('total_tables_checked')}")
            print(f"   - Tables with Source/Date: {json_data.get('tables_with_source_date')}")
            print(f"   - Source/Date Issues: {len(json_data.get('source_date_issues', []))}")
            print(f"   - Numerical Inconsistencies: {len(json_data.get('numerical_inconsistencies', []))}")
            print(f"   - Cross-Reference Issues: {len(json_data.get('cross_reference_issues', []))}")
            print()
            
            # Show first few issues if any
            if json_data.get('source_date_issues'):
                print("   First Source/Date Issue:")
                first_issue = json_data['source_date_issues'][0]
                print(f"     - Type: {first_issue.get('issue_type')}")
                print(f"     - Location: {first_issue.get('location')}")
                print(f"     - Severity: {first_issue.get('severity')}")
                print(f"     - Message: {first_issue.get('message')[:100]}...")
                print()
        except Exception as e:
            print(f"[WARNING] Could not read JSON file: {e}")
    
    # Step 6: Verify all files exist
    print("Step 6: Verifying all output files...")
    expected_files = {
        'JSON': 'data_consistency_result.json',
        'HTML': 'data_consistency_report.html',
        'CSV': 'data_consistency_issues.csv',
        'Summary': 'data_consistency_summary.json'
    }
    
    output_dir = Path("outputs") / document_id
    all_exist = True
    for file_type, filename in expected_files.items():
        file_path = output_dir / filename
        exists = file_path.exists()
        status = "[OK]" if exists else "[MISSING]"
        print(f"   {status} {file_type}: {filename}")
        if not exists:
            all_exist = False
    
    print()
    if all_exist:
        print("=" * 70)
        print("[SUCCESS] TEST PASSED: All data consistency output files generated!")
        print("=" * 70)
        print()
        print(f"Output directory: {output_dir}")
        print()
        print("Files generated:")
        for file_type, filename in expected_files.items():
            file_path = output_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  - {filename} ({size:,} bytes)")
    else:
        print("=" * 70)
        print("[FAILED] TEST FAILED: Some files are missing")
        print("=" * 70)
    
    return document_id


if __name__ == "__main__":
    test_data_consistency_output()

