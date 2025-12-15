#!/usr/bin/env python3
"""
Run the full compliance validation pipeline end-to-end
"""

from pathlib import Path
import json
from datetime import date, datetime
from backend.extractors.pipeline import ExtractionPipeline
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent

# File paths
pptx_path = Path('dataset/example_3/3 - FINAL CLEAN-6PG-GB-ODDO BHF US Equity Active ETF-20250831.pptx')
metadata_path = Path('dataset/example_3/metadata.json')
prospectus_path = Path('dataset/example_3/prospectus.docx')
output_dir = Path('outputs/full_pipeline_test')
output_dir.mkdir(parents=True, exist_ok=True)

print("="*70)
print("RUNNING FULL COMPLIANCE VALIDATION PIPELINE")
print("="*70)
print(f"\nDocument: {pptx_path.name}")
print(f"Output: {output_dir}\n")

# Step 1: Extract content
print("Step 1: Extracting document content (with chart analysis)...")
try:
    pipeline = ExtractionPipeline(output_dir=str(output_dir))
    pipeline_result = pipeline.process_document(
        file_path_str=str(pptx_path),
        metadata_json_path=str(metadata_path) if metadata_path.exists() else None
    )
    
    # Load extraction data from the saved file
    doc_id = pipeline_result.get('document_id')
    extraction_file_path = output_dir / doc_id / 'extraction.json'
    if extraction_file_path.exists():
        with open(extraction_file_path, 'r', encoding='utf-8') as f:
            extraction_result = json.load(f)
    else:
        # Fallback if file doesn't exist
        print("WARNING: extraction.json not found, using empty result")
        extraction_result = {}
        
except Exception as e:
    print(f"WARNING: Full pipeline extraction failed: {e}")
    print("Falling back to direct extraction...")
    from backend.extractors.core.document_extractor import DocumentExtractor
    extractor = DocumentExtractor(enable_chart_analysis=True)
    extraction_result = extractor.extract(str(pptx_path))

print("[OK] Extraction complete")
print(f"  - Slides: {extraction_result.get('total_slides', 0)}")
print(f"  - Tables: {extraction_result.get('total_tables', 0)}")
print(f"  - Charts: {extraction_result.get('total_charts', 0)}")

# Step 2: Run validation
print("\nStep 2: Running compliance validation...")
validator = DataConsistencyAgent()

# Load metadata
with open(metadata_path, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

validation_result = validator.validate(
    extraction_result=extraction_result,
    metadata=metadata
)

print("[OK] Validation complete")
print(f"  - Total issues: {len(validation_result.compliance_issues)}")
print(f"  - Critical: {sum(1 for i in validation_result.compliance_issues if i.severity == 'critical')}")
print(f"  - High: {sum(1 for i in validation_result.compliance_issues if i.severity in ['high', 'error'])}")
print(f"  - Medium: {sum(1 for i in validation_result.compliance_issues if i.severity in ['medium', 'warning'])}")
print(f"  - Low: {sum(1 for i in validation_result.compliance_issues if i.severity == 'low')}")

# Step 3: Format and save results
print("\nStep 3: Saving results...")

# Helper to convert dates to ISO format
def convert_dates(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(item) for item in obj]
    return obj

# Format validation result
formatted_result = {
    'overall_status': validation_result.overall_status,
    'total_issues': len(validation_result.compliance_issues),
    'total_critical_issues': sum(1 for i in validation_result.compliance_issues if i.severity == 'critical'),
    'total_high_issues': sum(1 for i in validation_result.compliance_issues if i.severity in ['high', 'error']),
    'total_medium_issues': sum(1 for i in validation_result.compliance_issues if i.severity in ['medium', 'warning']),
    'total_low_issues': sum(1 for i in validation_result.compliance_issues if i.severity == 'low'),
    'compliance_issues': [
        {
            'type': issue.issue_type,
            'category': issue.issue_category,
            'severity': issue.severity,
            'rule': issue.rule_reference,
            'location': issue.location,
            'message': issue.message,
            'context': issue.context if issue.context else None,
            'suggestion': issue.suggestion if issue.suggestion else None
        }
        for issue in validation_result.compliance_issues
    ],
    'statistics': {
        'total_slides': extraction_result.get('total_slides', 0),
        'total_tables_checked': extraction_result.get('total_tables', 0),
        'total_charts_analyzed': extraction_result.get('total_charts', 0),
        'total_performance_entries_checked': len(extraction_result.get('performance_sections', [])),
    },
    'metadata': metadata
}

formatted_result = convert_dates(formatted_result)

# Save results
validation_file = output_dir / 'validation_result.json'
with open(validation_file, 'w', encoding='utf-8') as f:
    json.dump(formatted_result, f, indent=2, ensure_ascii=False)

extraction_file = output_dir / 'extraction.json'
with open(extraction_file, 'w', encoding='utf-8') as f:
    json.dump(convert_dates(extraction_result), f, indent=2, ensure_ascii=False)

print("[OK] Results saved")
print(f"  - {validation_file}")
print(f"  - {extraction_file}")

print("\n" + "="*70)
print("PIPELINE COMPLETE")
print("="*70)
print("\nSummary:")
print(f"  Status: {formatted_result['overall_status']}")
print(f"  Issues: {formatted_result['total_issues']}")
print(f"  Charts: {formatted_result['statistics']['total_charts_analyzed']}")
print(f"  Tables: {formatted_result['statistics']['total_tables_checked']}")

if formatted_result['statistics']['total_charts_analyzed'] > 0:
    print(f"\n[OK] Chart analysis WORKING - {formatted_result['statistics']['total_charts_analyzed']} charts analyzed!")
else:
    print("\n[!] Chart analysis NOT working - 0 charts found")

print(f"\nView full results in: {output_dir.absolute()}")
