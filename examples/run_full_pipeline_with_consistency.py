"""
Run Full Pipeline with Data Consistency Validation

Runs extraction + consistency validation on a single document
and saves all outputs including consistency report.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Note: pydantic v1 compatibility handled centrally when needed
# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.extractors.pipeline import ExtractionPipeline  # noqa: E402
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent  # noqa: E402
from backend.extractors.compliance_rules import ClientType, FundType  # noqa: E402


def load_extraction_result(output_dir: Path, doc_id: str) -> dict:
    """Load extraction result from JSON files"""
    doc_dir = output_dir / doc_id
    
    result = {}
    
    # Load extraction.json
    extraction_path = doc_dir / 'extraction.json'
    if extraction_path.exists():
        with open(extraction_path, 'r', encoding='utf-8') as f:
            result['extraction'] = json.load(f)
    
    # Load metadata.json
    metadata_path = doc_dir / 'metadata.json'
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            result['metadata'] = json.load(f)
    
    # Load features.json
    features_path = doc_dir / 'features.json'
    if features_path.exists():
        with open(features_path, 'r', encoding='utf-8') as f:
            result['features'] = json.load(f)
    
    return result


def main():
    # Setup paths
    workspace = Path(__file__).resolve().parent
    
    # Create a dedicated output folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = workspace / 'outputs' / f'full_run_{timestamp}'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Target document - using a real fund presentation with tables and performance data
    doc_path = workspace / 'dataset' / 'example_1' / '47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx'
    
    print("=" * 80)
    print("FULL PIPELINE RUN (Extraction + Data Consistency Validation)")
    print("=" * 80)
    print(f"Target Document: {doc_path}")
    print(f"Output Directory: {output_dir}")
    print("-" * 80)

    if not doc_path.exists():
        print(f"[ERROR] Document not found: {doc_path}")
        return

    # ============================================================================
    # STEP 1: Run Extraction Pipeline
    # ============================================================================
    print("\n[STEP 1] Running Extraction Pipeline...")
    print("-" * 80)
    
    pipeline = ExtractionPipeline(
        use_llm=True,
        output_dir=str(output_dir)
    )
    
    try:
        result = pipeline.process_document(file_path=str(doc_path))
        
        if result.get('status') != 'success':
            print("\n[ERROR] Extraction failed.")
            for err in result.get('errors', []):
                print(f"- {err}")
            return
        
        doc_id = result.get('document_id')
        print("\n[SUCCESS] Extraction complete!")
        print(f"Document ID: {doc_id}")
        
    except Exception as e:
        print(f"\n[EXCEPTION] Extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # ============================================================================
    # STEP 2: Load Extraction Results
    # ============================================================================
    print("\n[STEP 2] Loading extraction results...")
    print("-" * 80)
    
    extraction_data = load_extraction_result(output_dir, doc_id)
    
    if not extraction_data:
        print("[ERROR] Could not load extraction results.")
        return
    
    extraction = extraction_data.get('extraction', {})
    metadata = extraction_data.get('metadata', {})
    features = extraction_data.get('features', {})
    
    print("Loaded extraction data:")
    print(f"  - Text length: {len(extraction.get('text', ''))}")
    print(f"  - Tables: {len(extraction.get('tables', []))}")
    print(f"  - Slides: {len(extraction.get('slides', []))}")
    if features:
        print(f"  - ESG mentions: {len(features.get('esg_mentions', []))}")
        print(f"  - Performance data: {len(features.get('performance_data', []))}")
        print(f"  - Country mentions: {len(features.get('country_mentions', []))}")

    # ============================================================================
    # STEP 3: Run Data Consistency Validation
    # ============================================================================
    print("\n[STEP 3] Running Data Consistency Validation...")
    print("-" * 80)
    
    # Determine client type and fund type from metadata
    client_type = ClientType.PROFESSIONAL if metadata.get('is_professional_client') else ClientType.RETAIL
    fund_type = FundType.STANDARD  # Default to standard fund type
    
    print(f"Client Type: {client_type.value}")
    print(f"Fund Type: {fund_type.value}")
    
    # Initialize Data Consistency Agent
    # Note: For demo purposes, we don't have reference data (Prospectus/KID)
    # In production, you would load this from a database or file
    agent = DataConsistencyAgent(
        reference_data=None,  # No reference data for now
        max_date_age_days=365,
        enable_cross_reference=True,
        enable_date_validation=True,
        enable_disclaimer_validation=False
    )
    
    # Run validation
    consistency_result = agent.validate(
        extraction_result=extraction,
        metadata=metadata,
        document_id=doc_id
    )
    
    print("\n[SUCCESS] Data Consistency Validation complete!")
    print(f"Overall Status: {consistency_result.overall_status.upper()}")
    
    # ============================================================================
    # STEP 4: Save Consistency Report
    # ============================================================================
    print("\n[STEP 4] Saving consistency report...")
    print("-" * 80)
    
    doc_dir = output_dir / doc_id
    consistency_path = doc_dir / 'consistency_report.json'
    
    with open(consistency_path, 'w', encoding='utf-8') as f:
        json.dump(consistency_result.model_dump(), f, ensure_ascii=False, indent=2)
    
    print(f"Saved: {consistency_path.relative_to(workspace)}")
    
    # ============================================================================
    # STEP 5: Display Summary
    # ============================================================================
    print("\n" + "=" * 80)
    print("DATA CONSISTENCY REPORT SUMMARY")
    print("=" * 80)
    
    # Source/Date Issues
    print("\nSource & Date Validation:")
    print(f"  - Tables checked: {consistency_result.total_tables_checked}")
    print(f"  - Tables with source/date: {consistency_result.tables_with_source_date}")
    print(f"  - Tables missing source/date: {consistency_result.tables_missing_source_date}")
    if consistency_result.source_date_issues:
        print(f"  - Issues found: {len(consistency_result.source_date_issues)}")
        for issue in consistency_result.source_date_issues[:5]:  # Show first 5
            print(f"    • [{issue.severity.upper()}] {issue.message} (at {issue.location})")
    
    # Numerical Inconsistencies
    print("\nNumerical Validation:")
    print(f"  - Values checked: {consistency_result.total_numerical_values_checked}")
    print(f"  - Values matching reference: {consistency_result.values_matching_reference}")
    print(f"  - Inconsistencies found: {len(consistency_result.numerical_inconsistencies)}")
    if consistency_result.numerical_inconsistencies:
        for inc in consistency_result.numerical_inconsistencies[:5]:  # Show first 5
            print(f"    • [{inc.severity.upper()}] {inc.message} (at {inc.location})")
    
    # Cross-Reference Issues
    if consistency_result.cross_reference_issues:
        print("\nCross-Reference Issues:")
        print(f"  - Issues found: {len(consistency_result.cross_reference_issues)}")
        for issue in consistency_result.cross_reference_issues[:5]:  # Show first 5
            print(f"    • [{issue.severity.upper()}] {issue.message}")
    
    # Compliance Issues
    if consistency_result.compliance_issues:
        print("\nCompliance Issues:")
        print(f"  - Issues found: {len(consistency_result.compliance_issues)}")
        for issue in consistency_result.compliance_issues[:10]:  # Show first 10
            print(f"    • [{issue.severity.upper()}] {issue.message} (at {issue.location})")
    
    # Overall Status
    print(f"\n{'='*80}")
    status_text = "PASS" if consistency_result.overall_status == "pass" else "WARNING" if consistency_result.overall_status == "warning" else "ERROR"
    print(f"{status_text}: Overall Status: {consistency_result.overall_status.upper()}")
    
    if consistency_result.has_errors:
        print("ERROR: Document has ERRORS - requires correction")
    elif consistency_result.has_warnings:
        print("WARNING: Document has WARNINGS - review recommended")
    else:
        print("PASS: Document passes all consistency checks")
    
    print(f"\n{'='*80}")
    print("Generated Output Files:")
    print(f"{'='*80}")
    for root, dirs, files in os.walk(output_dir):
        for file in sorted(files):
            rel_path = Path(root) / file
            print(f"  - {rel_path.relative_to(workspace)}")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
