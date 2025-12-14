#!/usr/bin/env python3
"""Extract document and save full JSON output"""

from pathlib import Path
import json
from datetime import date, datetime
from backend.extractors.core.document_extractor import DocumentExtractor

# Paths
pptx_path = Path('dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx')
output_file = Path('outputs/extraction_output.json')
output_file.parent.mkdir(exist_ok=True)

print("Extracting document with chart analysis...")
print(f"Document: {pptx_path.name}\n")

# Create extractor with NO caching to ensure fresh analysis
extractor = DocumentExtractor(enable_chart_analysis=True)
extractor.chart_analyzer.enable_caching = False
extractor.chart_analyzer.cache = None

# Extract
result = extractor.extract(str(pptx_path))

# Convert dates to strings for JSON serialization
def convert_dates(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(item) for item in obj]
    return obj

result = convert_dates(result)

# Save to file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f" Extraction complete!")
print(f"  - Charts: {result.get('total_charts', 0)}")
print(f"  - Tables: {result.get('total_tables', 0)}")
print(f"  - Slides: {result.get('total_slides', 0)}")
print(f"\n Full JSON saved to: {output_file.absolute()}")
print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")
