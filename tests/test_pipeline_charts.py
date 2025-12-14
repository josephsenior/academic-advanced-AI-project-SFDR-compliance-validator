#!/usr/bin/env python3
"""Test pipeline chart extraction"""

from backend.extractors.pipeline.orchestrator import ExtractionPipeline
import json

print("Creating pipeline...")
pipeline = ExtractionPipeline()

print(f"Document extractor chart analysis enabled: {pipeline.document_extractor.chart_analyzer is not None}")
print(f"Chart analyzer uses LLM: {pipeline.document_extractor.chart_analyzer.use_llm if pipeline.document_extractor.chart_analyzer else False}")

print("\nProcessing document...")
result = pipeline.process_document(
    'dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx',
    'dataset/example_3/metadata.json'
)

print(f"\nResult document_id: {result['document_id']}")
print(f"Extraction output path: {result['output_paths']['extraction']}")

# Load extraction file
with open(result['output_paths']['extraction'], 'r', encoding='utf-8') as f:
    extraction = json.load(f)

print(f"\nExtraction results:")
print(f"  Total slides: {extraction.get('total_slides', 0)}")
print(f"  Total tables: {extraction.get('total_tables', 0)}")
print(f"  Total charts: {extraction.get('total_charts', 0)}")
print(f"  Charts array length: {len(extraction.get('charts', []))}")

if extraction.get('total_charts', 0) == 0:
    print("\n[!] NO CHARTS FOUND - Debugging...")
    print(f"  Chart analyzer object exists: {pipeline.document_extractor.chart_analyzer is not None}")
    if pipeline.document_extractor.chart_analyzer:
        print(f"  Chart analyzer use_llm: {pipeline.document_extractor.chart_analyzer.use_llm}")
        print(f"  Chart analyzer llm: {pipeline.document_extractor.chart_analyzer.llm}")
