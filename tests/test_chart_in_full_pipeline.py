#!/usr/bin/env python3
"""
Test chart analysis in the full extraction pipeline
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.extractors.pipeline import ExtractionPipeline

def test_full_pipeline_with_charts():
    """Test chart analysis in the full pipeline"""
    print("=" * 70)
    print("Full Pipeline Chart Analysis Test")
    print("=" * 70)
    print()
    
    # Find a test document
    test_files = [
        "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "dataset/example_1/47861-6PG-GB-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "dataset/example_2/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
    ]
    
    test_file = None
    for f in test_files:
        if Path(f).exists():
            test_file = Path(f)
            break
    
    if not test_file:
        print("[ERROR] No test document found")
        print("   Looking for files in dataset/example_1/ or dataset/example_2/")
        return False
    
    print(f"1. Using test document: {test_file}")
    print()
    
    # Initialize pipeline with chart analysis enabled
    print("2. Initializing ExtractionPipeline...")
    try:
        pipeline = ExtractionPipeline(use_llm=True)
        print(f"   [OK] Pipeline initialized")
        print(f"   - Chart analysis enabled: {pipeline.document_extractor.enable_chart_analysis}")
        print(f"   - Chart analyzer available: {pipeline.document_extractor.chart_analyzer is not None}")
        
        if pipeline.document_extractor.chart_analyzer:
            print(f"   - Chart analyzer LLM available: {pipeline.document_extractor.chart_analyzer.llm is not None}")
    except Exception as e:
        print(f"   [ERROR] Failed to initialize pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Process document
    print("3. Processing document through full pipeline...")
    try:
        result = pipeline.process_document(
            file_path=str(test_file),
            metadata_json_path=None
        )
        print(f"   [OK] Document processed")
        print()
        
        # Check for chart data in results
        print("4. Checking for chart analysis results...")
        
        extraction_result = result.get('extraction_result', {})
        
        # Check charts_data (might be at root level or nested)
        charts_data = extraction_result.get('charts_data', [])
        if not charts_data:
            # Try alternative locations
            charts_data = extraction_result.get('charts', [])
        if not charts_data and 'structure' in extraction_result:
            charts_data = extraction_result['structure'].get('charts_data', [])
        
        print(f"   - Charts found in extraction_result: {len(charts_data)}")
        print(f"   - Total charts reported: {extraction_result.get('total_charts', 0)}")
        
        if charts_data:
            print(f"   [SUCCESS] Chart analysis is working in pipeline!")
            print()
            print("   Chart Details:")
            for i, chart in enumerate(charts_data[:3], 1):  # Show first 3
                print(f"   Chart {i}:")
                print(f"     - Slide: {chart.get('slide_number', 'N/A')}")
                print(f"     - Is Chart: {chart.get('is_chart', False)}")
                print(f"     - Chart Type: {chart.get('chart_type', 'N/A')}")
                print(f"     - Confidence: {chart.get('confidence', 0.0):.2f}")
                if chart.get('metadata'):
                    meta = chart['metadata']
                    print(f"     - Title: {meta.get('title', 'N/A')}")
                    print(f"     - Has Source: {meta.get('has_source', False)}")
                    print(f"     - Has Date: {meta.get('has_date', False)}")
                print(f"     - Data Points: {len(chart.get('data_points', []))}")
                print(f"     - Performance Values: {len(chart.get('performance_values', []))}")
                print()
        else:
            print(f"   [WARNING] No charts found in extraction results")
            print(f"   This could mean:")
            print(f"     - Document has no images/charts")
            print(f"     - Chart analysis failed silently")
            print(f"     - Charts were not detected")
            print()
            
            # Check if there are images at all
            total_slides = extraction_result.get('total_slides', 0)
            print(f"   - Total slides: {total_slides}")
            
            # Check performance sections (might contain chart data)
            perf_sections = extraction_result.get('performance_sections', [])
            print(f"   - Performance sections: {len(perf_sections)}")
            
            # Check if chart analyzer was actually called
            if pipeline.document_extractor.chart_analyzer:
                print(f"   - Chart analyzer was initialized")
            else:
                print(f"   - Chart analyzer was NOT initialized")
        
        # Check performance sections for chart-extracted data
        perf_sections = extraction_result.get('performance_sections', [])
        chart_perf_count = 0
        for section in perf_sections:
            entries = section.get('entries', [])
            for entry in entries:
                if entry.get('source') == 'chart_analysis':
                    chart_perf_count += 1
        
        if chart_perf_count > 0:
            print(f"   [INFO] Found {chart_perf_count} performance entries from chart analysis")
        
        return len(charts_data) > 0 or chart_perf_count > 0
        
    except Exception as e:
        print(f"   [ERROR] Pipeline processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_pipeline_with_charts()
    sys.exit(0 if success else 1)

