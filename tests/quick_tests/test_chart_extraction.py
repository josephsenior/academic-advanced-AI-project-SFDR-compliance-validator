#!/usr/bin/env python3
"""Test script to debug chart extraction"""

from pathlib import Path
from backend.extractors.core.document_extractor import DocumentExtractor

# Run extraction with chart analysis enabled
extractor = DocumentExtractor(enable_chart_analysis=True)
# Disable caching to ensure fresh analysis
extractor.chart_analyzer.enable_caching = False
extractor.chart_analyzer.cache = None

file_path = Path('dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx').resolve()

print(f"Extracting from: {file_path}")
print(f"File exists: {file_path.exists()}")
print(f"Chart analysis enabled: {extractor.enable_chart_analysis}")
print(f"Chart analyzer present: {extractor.chart_analyzer is not None}")
print("\n" + "="*60)

result = extractor.extract(str(file_path))

print(f"\nExtraction Results:")
print(f"  Total slides: {result['total_slides']}")
print(f"  Total tables: {result['total_tables']}")
print(f"  Total charts: {result['total_charts']}")
print(f"\n" + "="*60)

# Check if debug log was created
import os
if os.path.exists('c:/temp/extraction_debug.log'):
    print("\nDebug log contents:")
    with open('c:/temp/extraction_debug.log', 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("\nDebug log was NOT created at c:/temp/extraction_debug.log")
