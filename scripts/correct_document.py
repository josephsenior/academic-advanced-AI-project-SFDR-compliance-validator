"""
CLI Tool for Document Correction

Usage:
    python scripts/correct_document.py input.pptx [--output output.pptx] [--fix-disclaimers]
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.extractors.pipeline import ExtractionPipeline
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent, ReferenceData
from backend.extractors.document_corrector import DocumentCorrector
from backend.extractors.validators.disclaimer_validator import DisclaimerValidator


def main():
    parser = argparse.ArgumentParser(
        description="Correct document based on validation results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic correction (source/date fixes only)
  python scripts/correct_document.py input.pptx
  
  # Specify output file
  python scripts/correct_document.py input.pptx --output corrected.pptx
  
  # Also fix disclaimers
  python scripts/correct_document.py input.pptx --fix-disclaimers
  
  # With reference data for numerical validation
  python scripts/correct_document.py input.pptx --reference-data reference.json
        """
    )
    
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to input document (PPTX format)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to output corrected document (default: adds _corrected suffix)"
    )
    
    parser.add_argument(
        "--fix-disclaimers",
        action="store_true",
        help="Also auto-fix missing disclaimers"
    )
    
    parser.add_argument(
        "--reference-data",
        type=str,
        default=None,
        help="Path to JSON file with reference data for numerical validation"
    )
    
    parser.add_argument(
        "--metadata",
        type=str,
        default=None,
        help="Path to metadata JSON file"
    )
    
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM for feature extraction (slower but more accurate)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)
    
    if input_path.suffix.lower() != '.pptx':
        print(f"[WARN] Only .pptx format is currently supported")
        print(f"   File: {input_path.suffix}")
    
    print("=" * 80)
    print("Document Correction Tool")
    print("=" * 80)
    print()
    print(f"Input file: {input_path}")
    if args.output:
        print(f"Output file: {args.output}")
    else:
        print(f"Output file: {input_path.stem}_corrected{input_path.suffix}")
    print()
    
    # Step 1: Process document
    print("Step 1: Processing document...")
    try:
        pipeline = ExtractionPipeline(use_llm=args.use_llm)
        pipeline_result = pipeline.process_document(
            file_path=str(input_path),
            metadata_json_path=args.metadata
        )
        
        # Check if extraction succeeded even if pipeline has serialization issues
        if pipeline_result['status'] != 'success':
            errors = pipeline_result.get('errors', [])
            # Check if it's just a serialization error (extraction may have succeeded)
            if 'extraction_result' in pipeline_result:
                print(f"[WARN] Pipeline has errors but extraction succeeded: {errors}")
                print(f"[OK] Continuing with extracted data...")
            else:
                print(f"[ERROR] Pipeline failed: {errors}")
                sys.exit(1)
        
        print(f"[OK] Document processed: {pipeline_result.get('document_id', 'unknown')}")
        extraction_result = pipeline_result.get('extraction_result', {})
        metadata = pipeline_result.get('metadata', {})
        
        if not extraction_result:
            print(f"[ERROR] No extraction result available")
            sys.exit(1)
        
    except Exception as e:
        print(f"[ERROR] Error processing document: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 2: Validate
    print("\nStep 2: Validating document...")
    try:
        # Load reference data if provided
        reference_data = None
        if args.reference_data:
            import json
            with open(args.reference_data, 'r') as f:
                ref_dict = json.load(f)
            from backend.extractors.agents.data_consistency_agent import create_reference_data_from_dict
            reference_data = create_reference_data_from_dict(ref_dict)
        
        agent = DataConsistencyAgent(reference_data=reference_data)
        validation_result = agent.validate(
            extraction_result=extraction_result,
            metadata=metadata,
            document_id=pipeline_result['document_id']
        )
        
        print(f"[OK] Validation completed")
        print(f"   Status: {validation_result.overall_status.upper()}")
        print(f"   Source/Date issues: {len(validation_result.source_date_issues)}")
        print(f"   Numerical inconsistencies: {len(validation_result.numerical_inconsistencies)}")
        print(f"   Cross-reference issues: {len(validation_result.cross_reference_issues)}")
        
    except Exception as e:
        print(f"[ERROR] Error validating document: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 3: Validate disclaimers if requested
    disclaimer_result = None
    if args.fix_disclaimers:
        print("\nStep 3: Validating disclaimers...")
        try:
            from backend.extractors.validators.disclaimer_validator import DisclaimerValidator
            validator = DisclaimerValidator()
            disclaimer_result = validator.validate(
                extraction_result=extraction_result,
                metadata=metadata,
                document_id=pipeline_result['document_id']
            )
            print(f"[OK] Disclaimer validation completed")
            if hasattr(disclaimer_result, 'total_missing'):
                print(f"   Missing disclaimers: {disclaimer_result.total_missing}")
        except Exception as e:
            print(f"[WARN] Disclaimer validation failed: {e}")
            print("   Continuing without disclaimer fixes...")
    
    # Step 4: Correct document
    print("\nStep 4: Applying corrections...")
    try:
        corrector = DocumentCorrector()
        correction_result = corrector.correct(
            original_path=str(input_path),
            validation_result=validation_result,
            disclaimer_result=disclaimer_result,
            output_path=args.output,
            auto_fix_disclaimers=args.fix_disclaimers
        )
        
        if not correction_result.success:
            print(f"[ERROR] Correction failed: {correction_result.error_message}")
            sys.exit(1)
        
        print(f"[OK] Correction completed!")
        print(f"   Corrected file: {correction_result.corrected_path}")
        print(f"   Fixes applied: {len(correction_result.fixes_applied)}")
        print(f"   Fixes failed: {len(correction_result.fixes_failed)}")
        print(f"   Manual review required: {len(correction_result.manual_review_required)}")
        
        # Show fixes applied
        if correction_result.fixes_applied:
            print("\n   Fixes Applied:")
            for fix in correction_result.fixes_applied:
                print(f"     • {fix['type']}: {fix.get('fix', fix.get('location', 'N/A'))}")
        
        # Show fixes that failed
        if correction_result.fixes_failed:
            print("\n   Fixes Failed:")
            for fix in correction_result.fixes_failed:
                print(f"     • {fix.get('issue', 'Unknown')}: {fix.get('reason', 'N/A')}")
        
        # Show manual review items
        if correction_result.manual_review_required:
            print("\n   Manual Review Required:")
            for item in correction_result.manual_review_required[:5]:  # Show first 5
                print(f"     • {item['type']}: {item.get('issue', item.get('location', 'N/A'))}")
            if len(correction_result.manual_review_required) > 5:
                print(f"     ... and {len(correction_result.manual_review_required) - 5} more")
        
    except Exception as e:
        print(f"[ERROR] Error correcting document: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("[SUCCESS] Document correction completed successfully!")
    print("=" * 80)
    print(f"\nCorrected document saved to: {correction_result.corrected_path}")
    
    if correction_result.manual_review_required:
        print(f"\n[NOTE] {len(correction_result.manual_review_required)} item(s) require manual review")
        print("   These are numerical inconsistencies and cross-reference issues")
        print("   that should be verified by a human before finalizing the document.")


if __name__ == "__main__":
    main()

