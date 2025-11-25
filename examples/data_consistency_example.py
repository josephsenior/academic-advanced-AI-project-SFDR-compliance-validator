"""
Example: Using the Data Consistency Agent

This example demonstrates how to use the Data Consistency Agent
to validate marketing documents against reference data.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import (
    DataConsistencyAgent,
    ReferenceData,
    create_reference_data_from_dict
)


def main():
    """Example usage of Data Consistency Agent"""
    
    print("=" * 60)
    print("Data Consistency Agent Example")
    print("=" * 60)
    print()
    
    # Step 1: Process a document through the extraction pipeline
    print("Step 1: Processing document...")
    document_path = "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx"
    metadata_path = "dataset/example_1/metadata.json"
    
    if not Path(document_path).exists():
        print(f"⚠️  Document not found: {document_path}")
        print("   Please update the path to an existing document")
        return
    
    pipeline = ExtractionPipeline(use_llm=False)  # Set to True if you have LLM configured
    pipeline_result = pipeline.process_document(
        file_path=document_path,
        metadata_json_path=metadata_path if Path(metadata_path).exists() else None
    )
    
    if pipeline_result['status'] != 'success':
        print(f"❌ Pipeline failed: {pipeline_result.get('errors', [])}")
        return
    
    print(f"✅ Document processed: {pipeline_result['document_id']}")
    print()
    
    # Step 2: Prepare reference data
    # In a real scenario, this would come from your Prospectus/KID/SFDR database
    print("Step 2: Preparing reference data...")
    reference_data = ReferenceData(
        fund_name="ODDO BHF Algo Trend US",
        performance_data={
            "1y": {"net": 10.0},  # Example reference values
            "3y": {"net": 8.5},
            "ytd": {"net": 7.2}
        },
        table_data={
            "fund": 10.0,
            "benchmark": 8.0
        },
        reference_date="2025-08-31",
        source_document="Prospectus"
    )
    print("✅ Reference data prepared")
    print()
    
    # Alternative: Create from dictionary
    # reference_data = create_reference_data_from_dict({
    #     'fund_name': 'ODDO BHF Algo Trend US',
    #     'performance_data': {'1y': {'net': 10.0}},
    #     'table_data': {'fund': 10.0},
    #     'source_document': 'Prospectus'
    # })
    
    # Step 3: Initialize and run Data Consistency Agent
    print("Step 3: Running Data Consistency validation...")
    agent = DataConsistencyAgent(reference_data=reference_data)
    
    validation_result = agent.validate(
        extraction_result=pipeline_result['extraction_result'],
        metadata=pipeline_result['metadata'],
        document_id=pipeline_result['document_id']
    )
    print("✅ Validation completed")
    print()
    
    # Step 4: Display results
    print("=" * 60)
    print("Validation Results")
    print("=" * 60)
    print()
    
    print(f"Overall Status: {validation_result.overall_status.upper()}")
    print()
    
    # Source/Date validation
    print("Source/Date Validation:")
    print(f"  Tables checked: {validation_result.total_tables_checked}")
    print(f"  Tables with source+date: {validation_result.tables_with_source_date}")
    print(f"  Tables missing source/date: {validation_result.tables_missing_source_date}")
    
    if validation_result.source_date_issues:
        print(f"\n  Issues found ({len(validation_result.source_date_issues)}):")
        for issue in validation_result.source_date_issues:
            severity_icon = "❌" if issue.severity == "error" else "⚠️"
            print(f"    {severity_icon} [{issue.severity.upper()}] {issue.message}")
    else:
        print("  ✅ No source/date issues found")
    print()
    
    # Numerical validation
    if validation_result.total_numerical_values_checked > 0:
        print("Numerical Validation:")
        print(f"  Values checked: {validation_result.total_numerical_values_checked}")
        print(f"  Values matching reference: {validation_result.values_matching_reference}")
        print(f"  Values with inconsistencies: {validation_result.values_with_inconsistencies}")
        
        if validation_result.numerical_inconsistencies:
            print(f"\n  Inconsistencies found ({len(validation_result.numerical_inconsistencies)}):")
            for inc in validation_result.numerical_inconsistencies:
                severity_icon = "❌" if inc.severity == "error" else "⚠️"
                print(f"    {severity_icon} [{inc.severity.upper()}] {inc.message}")
        else:
            print("  ✅ No numerical inconsistencies found")
        print()
    else:
        print("Numerical Validation: Skipped (no reference data or no numerical values found)")
        print()
    
    # Summary
    print("Summary:")
    for msg in validation_result.summary:
        print(f"  {msg}")
    print()
    
    # Step 5: Save results (optional)
    output_path = Path("outputs") / pipeline_result['document_id'] / "data_consistency_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(validation_result.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✅ Results saved to: {output_path}")
    print()
    
    print("=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

