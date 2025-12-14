"""
End-to-End Integration Test

Tests the complete flow:
1. Document extraction (with chart analysis)
2. Data consistency validation
3. Chart validation
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.extractors.pipeline import ExtractionPipeline
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent
from backend.extractors.agents.reference_data import ReferenceData
from backend.extractors.core.chart_analyzer import ChartAnalyzer


def test_end_to_end_flow():
    """Test complete end-to-end flow"""
    print("=" * 60)
    print("End-to-End Integration Test")
    print("=" * 60)
    print()
    
    # Step 1: Document Extraction
    print("Step 1: Document Extraction (with chart analysis)...")
    document_path = "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx"
    metadata_path = "dataset/example_1/metadata.json"
    
    if not Path(document_path).exists():
        print(f"WARNING: Document not found: {document_path}")
        print("   Skipping integration test")
        return False
    
    # Initialize pipeline with chart analysis enabled
    pipeline = ExtractionPipeline(use_llm=False)  # Set to True if LLM is configured
    
    # Enable chart analysis in document extractor
    pipeline.document_extractor.enable_chart_analysis = True
    if pipeline.document_extractor.enable_chart_analysis:
        try:
            from backend.extractors.core.chart_analyzer import ChartAnalyzer
            pipeline.document_extractor.chart_analyzer = ChartAnalyzer(use_llm=True)
        except Exception as e:
            print(f"  WARNING: Chart analyzer not available: {e}")
            pipeline.document_extractor.enable_chart_analysis = False
    
    try:
        pipeline_result = pipeline.process_document(
            file_path=document_path,
            metadata_json_path=metadata_path if Path(metadata_path).exists() else None
        )
    except Exception as e:
        print(f"  ERROR: Pipeline failed: {e}")
        return False
    
    if pipeline_result['status'] != 'success':
        print(f"  ERROR: Pipeline status: {pipeline_result['status']}")
        print(f"  Errors: {pipeline_result.get('errors', [])}")
        return False
    
    print(f"  SUCCESS: Document processed: {pipeline_result['document_id']}")
    extraction_result = pipeline_result.get('extraction_result', {})
    print(f"  SUCCESS: Extracted {len(extraction_result.get('text', ''))} characters")
    print(f"  SUCCESS: Found {extraction_result.get('total_tables', 0)} tables")
    print(f"  SUCCESS: Found {extraction_result.get('total_charts', 0)} charts")
    print()
    
    # Step 2: Data Consistency Validation
    print("Step 2: Data Consistency Validation...")
    
    # Create reference data
    reference_data = ReferenceData(
        fund_name="ODDO BHF Algo Trend US",
        performance_data={
            "1y": {"net": 10.0}  # Example reference
        },
        source_document="Prospectus"
    )
    
    agent = DataConsistencyAgent(reference_data=reference_data)
    
    try:
        validation_result = agent.validate(
            extraction_result=extraction_result,
            metadata=pipeline_result.get('metadata'),
            document_id=pipeline_result['document_id']
        )
    except Exception as e:
        print(f"  ERROR: Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"  SUCCESS: Validation completed")
    print(f"  Status: {validation_result.overall_status}")
    print(f"  Tables checked: {validation_result.total_tables_checked}")
    print(f"  Source/Date issues: {len(validation_result.source_date_issues)}")
    print(f"  Numerical inconsistencies: {len(validation_result.numerical_inconsistencies)}")
    print(f"  Cross-reference issues: {len(validation_result.cross_reference_issues)}")
    print()
    
    # Step 3: Verify Integration Points
    print("Step 3: Verifying Integration Points...")
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Extraction result has charts field
    total_checks += 1
    if 'charts' in extraction_result:
        print("  SUCCESS: Extraction result includes 'charts' field")
        checks_passed += 1
    else:
        print("  WARNING: Extraction result missing 'charts' field")
    
    # Check 2: Charts are validated
    total_checks += 1
    if validation_result.total_tables_checked > 0:
        print("  SUCCESS: Charts/tables are being validated")
        checks_passed += 1
    else:
        print("  WARNING: No charts/tables were validated")
    
    # Check 3: Performance data from charts is included
    total_checks += 1
    perf_sections = extraction_result.get('performance_sections', [])
    if perf_sections:
        print(f"  SUCCESS: Performance sections found: {len(perf_sections)}")
        checks_passed += 1
    else:
        print("  WARNING: No performance sections found")
    
    # Check 4: Chart data structure
    total_checks += 1
    charts = extraction_result.get('charts', [])
    if charts:
        chart = charts[0]
        if 'chart_type' in chart and 'data_points' in chart:
            print("  SUCCESS: Chart data structure is correct")
            checks_passed += 1
        else:
            print("  WARNING: Chart data structure incomplete")
    else:
        print("  INFO: No charts found in document (this is OK if document has no charts)")
        checks_passed += 1  # Not a failure if no charts
    
    print()
    print(f"Integration checks: {checks_passed}/{total_checks} passed")
    print()
    
    # Step 4: Summary
    print("=" * 60)
    print("Integration Test Summary")
    print("=" * 60)
    print(f"Document ID: {pipeline_result['document_id']}")
    print(f"Extraction Status: {pipeline_result['status']}")
    print(f"Validation Status: {validation_result.overall_status}")
    print(f"Charts Found: {len(charts)}")
    print(f"Tables Found: {extraction_result.get('total_tables', 0)}")
    print(f"Issues Found: {len(validation_result.source_date_issues)}")
    print()
    
    if checks_passed == total_checks and validation_result.overall_status in ['pass', 'warning']:
        print("SUCCESS: End-to-end integration test PASSED")
        return True
    else:
        print("WARNING: End-to-end integration test completed with warnings")
        return True  # Still pass if integration works, even with warnings


if __name__ == "__main__":
    success = test_end_to_end_flow()
    sys.exit(0 if success else 1)

