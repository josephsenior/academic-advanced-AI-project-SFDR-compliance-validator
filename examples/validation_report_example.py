"""
Example: Generate Multiple Report Formats from Validation Results

This example shows how to use ValidationReportGenerator to create
JSON, HTML, CSV, and summary reports from DataConsistencyResult.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent, ReferenceData
from src.utils.validation_report_generator import ValidationReportGenerator


def main():
    """Example: Generate all report formats"""
    
    print("=" * 70)
    print("Validation Report Generator Example")
    print("=" * 70)
    print()
    
    # Step 1: Process document
    print("Step 1: Processing document...")
    doc_path = "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx"
    
    if not Path(doc_path).exists():
        print(f"[ERROR] Document not found: {doc_path}")
        return
    
    pipeline = ExtractionPipeline(use_llm=False)
    result = pipeline.process_document(doc_path)
    
    if result['status'] != 'success':
        print(f"[ERROR] Pipeline failed: {result.get('errors', [])}")
        return
    
    print(f"[OK] Document processed: {result['document_id']}")
    print()
    
    # Step 2: Prepare reference data
    print("Step 2: Preparing reference data...")
    reference_data = ReferenceData(
        fund_name="ODDO BHF Algo Trend US",
        performance_data={
            "1Y": {"net": 10.0},
            "3Y": {"net": 8.5}
        },
        source_document="Prospectus"
    )
    print("[OK] Reference data prepared")
    print()
    
    # Step 3: Run validation
    print("Step 3: Running validation...")
    agent = DataConsistencyAgent(reference_data=reference_data)
    validation_result = agent.validate(
        extraction_result=result['extraction_result'],
        metadata=result['metadata'],
        document_id=result['document_id']
    )
    print(f"[OK] Validation completed: {validation_result.overall_status}")
    print()
    
    # Step 4: Generate all report formats
    print("Step 4: Generating reports...")
    report_generator = ValidationReportGenerator(output_dir="outputs")
    
    reports = report_generator.generate_all_reports(
        validation_result=validation_result,
        document_id=result['document_id'],
        document_name=Path(doc_path).name
    )
    
    print("[OK] Reports generated:")
    for report_type, report_path in reports.items():
        print(f"  - {report_type.upper()}: {report_path}")
    print()
    
    print("=" * 70)
    print("Example completed!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Open the HTML report in your browser for a human-readable view")
    print("  2. Use the JSON report for programmatic access")
    print("  3. Import the CSV report into Excel for analysis")
    print("  4. Use the summary JSON for dashboard integration")


if __name__ == "__main__":
    main()

