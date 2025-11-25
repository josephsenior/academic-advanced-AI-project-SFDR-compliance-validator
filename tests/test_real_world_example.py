"""
Real-World System Test

Tests the complete system with an actual ODD PowerPoint document
from the dataset, including all validation features.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.pipeline import ExtractionPipeline
from src.extractors.disclaimer_validator import DisclaimerValidator
from src.extractors.registration_parser import RegistrationParser
from src.extractors.data_consistency_agent import DataConsistencyAgent, ReferenceData
from src.utils.toon_serializer import dump_toon


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---")


def main():
    """Run real-world test with actual document"""
    
    print_section("REAL-WORLD SYSTEM TEST")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Document to test
    doc_path = "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx"
    
    if not Path(doc_path).exists():
        print(f"\n[ERROR] Document not found: {doc_path}")
        print("Please ensure the document exists in the dataset folder.")
        return
    
    print(f"\nDocument: {Path(doc_path).name}")
    print(f"Path: {doc_path}")
    
    # ========================================================================
    # STEP 1: Document Extraction
    # ========================================================================
    print_section("STEP 1: Document Extraction")
    
    try:
        print("Initializing extraction pipeline...")
        pipeline = ExtractionPipeline(use_llm=False)  # Disable LLM for faster testing
        
        print("Extracting document...")
        result = pipeline.process_document(doc_path)
        
        extraction_result = result['extraction_result']
        metadata = result['metadata']
        document_id = result.get('document_id', 'test-doc')
        
        print(f"\n[OK] Extraction successful!")
        print(f"  - Document ID: {document_id}")
        print(f"  - Slides: {extraction_result.get('total_slides', 0)}")
        print(f"  - Tables: {extraction_result.get('total_tables', 0)}")
        print(f"  - Charts: {extraction_result.get('total_charts', 0)}")
        print(f"  - Text length: {len(extraction_result.get('full_text', '') or extraction_result.get('text', ''))} characters")
        
        # Show metadata
        print_subsection("Metadata")
        print(f"  - Fund name: {metadata.get('fund_name', 'N/A')}")
        print(f"  - Language: {metadata.get('language_code', 'N/A')}")
        print(f"  - Document type: {metadata.get('document_type', 'N/A')}")
        
    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========================================================================
    # STEP 2: Disclaimer Validation
    # ========================================================================
    print_section("STEP 2: Disclaimer Validation")
    
    try:
        print("Initializing disclaimer validator...")
        disclaimer_validator = DisclaimerValidator()
        
        print("Validating disclaimers...")
        disclaimer_result = disclaimer_validator.validate(
            extraction_result,
            metadata,
            document_id
        )
        
        print(f"\n[OK] Disclaimer validation complete!")
        print(f"  - Required disclaimers: {disclaimer_result.total_required}")
        print(f"  - Present disclaimers: {disclaimer_result.total_present}")
        print(f"  - Missing disclaimers: {disclaimer_result.total_missing}")
        print(f"  - Has errors: {disclaimer_result.has_errors}")
        
        print_subsection("Required Disclaimers")
        for i, req in enumerate(disclaimer_result.required_disclaimers, 1):
            status = "[OK]" if req.disclaimer_type in disclaimer_result.present_disclaimers else "[MISSING]"
            print(f"  {i}. {status} {req.disclaimer_type}")
            print(f"      Reason: {req.reason}")
            if req.location:
                print(f"      Location: {req.location}")
        
        if disclaimer_result.missing_disclaimers:
            print_subsection("Missing Disclaimers (Errors)")
            for i, missing in enumerate(disclaimer_result.missing_disclaimers, 1):
                print(f"  {i}. {missing.disclaimer_type}")
                print(f"      Reason: {missing.reason}")
                if missing.expected_text:
                    preview = missing.expected_text[:150] + "..." if len(missing.expected_text) > 150 else missing.expected_text
                    print(f"      Expected: {preview}")
        else:
            print("\n  [SUCCESS] All required disclaimers are present!")
        
    except Exception as e:
        print(f"\n[ERROR] Disclaimer validation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================================================
    # STEP 3: Registration Validation
    # ========================================================================
    print_section("STEP 3: Country Registration Validation")
    
    try:
        print("Initializing registration parser...")
        registration_parser = RegistrationParser()
        
        # Get mentioned countries
        structure = extraction_result.get('structure', {})
        mentioned_countries = structure.get('countries_detected', [])
        fund_name = metadata.get('fund_name', 'ODDO BHF Algo Trend US')
        
        print(f"\nFund: {fund_name}")
        print(f"Mentioned countries: {', '.join(mentioned_countries) if mentioned_countries else 'None'}")
        
        if mentioned_countries:
            print("\nValidating country registrations...")
            validation = registration_parser.validate_country_mentions(
                mentioned_countries,
                fund_name
            )
            
            print_subsection("Registration Status")
            all_registered = True
            for country, is_registered in validation.items():
                status = "[OK]" if is_registered else "[ERROR]"
                reg_status = "Registered" if is_registered else "NOT Registered"
                print(f"  {status} {country}: {reg_status}")
                if not is_registered:
                    all_registered = False
            
            if all_registered:
                print("\n  [SUCCESS] All mentioned countries are registered!")
            else:
                print("\n  [WARNING] Some countries are not registered for this fund")
        else:
            print("\n  [INFO] No countries mentioned in document")
        
    except Exception as e:
        print(f"\n[ERROR] Registration validation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================================================
    # STEP 4: Data Consistency Validation
    # ========================================================================
    print_section("STEP 4: Data Consistency Validation")
    
    try:
        print("Initializing data consistency agent...")
        
        # Create agent with disclaimer validation enabled
        agent = DataConsistencyAgent(
            enable_disclaimer_validation=True,
            disclaimer_validator=disclaimer_validator,
            enable_cross_reference=True,
            enable_date_validation=True
        )
        
        print("Running comprehensive validation...")
        consistency_result = agent.validate(
            extraction_result,
            metadata,
            document_id
        )
        
        print(f"\n[OK] Data consistency validation complete!")
        print(f"  - Overall status: {consistency_result.overall_status.upper()}")
        print(f"  - Has errors: {consistency_result.has_errors}")
        print(f"  - Has warnings: {consistency_result.has_warnings}")
        
        print_subsection("Source/Date Validation")
        print(f"  - Tables checked: {consistency_result.total_tables_checked}")
        print(f"  - Tables with source/date: {consistency_result.tables_with_source_date}")
        print(f"  - Tables missing source/date: {consistency_result.tables_missing_source_date}")
        
        if consistency_result.source_date_issues:
            print(f"  - Issues found: {len(consistency_result.source_date_issues)}")
            for issue in consistency_result.source_date_issues[:3]:  # Show first 3
                print(f"    • {issue.issue_type}: {issue.message}")
        
        print_subsection("Cross-Reference Validation")
        if consistency_result.cross_reference_issues:
            print(f"  - Issues found: {len(consistency_result.cross_reference_issues)}")
            for issue in consistency_result.cross_reference_issues[:3]:  # Show first 3
                print(f"    • {issue.issue_type}: {issue.message}")
        else:
            print("  - No cross-reference issues found")
        
        print_subsection("Disclaimer Validation (Integrated)")
        if consistency_result.disclaimer_validation:
            disc_val = consistency_result.disclaimer_validation
            print(f"  - Required: {disc_val.get('total_required', 0)}")
            print(f"  - Present: {disc_val.get('total_present', 0)}")
            print(f"  - Missing: {disc_val.get('total_missing', 0)}")
        
        print_subsection("Summary")
        for summary_line in consistency_result.summary[:5]:  # Show first 5
            print(f"  - {summary_line}")
        
    except Exception as e:
        print(f"\n[ERROR] Data consistency validation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================================================
    # STEP 5: Save Results
    # ========================================================================
    print_section("STEP 5: Saving Results")
    
    try:
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"real_world_test_{timestamp}.toon"
        
        results = {
            "test_timestamp": timestamp,
            "document": doc_path,
            "document_id": document_id,
            "extraction": {
                "slides": extraction_result.get('total_slides', 0),
                "tables": extraction_result.get('total_tables', 0),
                "charts": extraction_result.get('total_charts', 0),
            },
            "disclaimer_validation": disclaimer_result.model_dump() if 'disclaimer_result' in locals() else None,
            "registration_validation": {
                "mentioned_countries": mentioned_countries if 'mentioned_countries' in locals() else [],
                "validation": validation if 'validation' in locals() else {}
            },
            "data_consistency": {
                "overall_status": consistency_result.overall_status if 'consistency_result' in locals() else None,
                "has_errors": consistency_result.has_errors if 'consistency_result' in locals() else None,
                "has_warnings": consistency_result.has_warnings if 'consistency_result' in locals() else None,
                "summary": consistency_result.summary if 'consistency_result' in locals() else []
            }
        }
        
        dump_toon(results, output_file, indent=2)
        
        print(f"[OK] Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to save results: {e}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_section("FINAL SUMMARY")
    
    print("\nTest Results:")
    print(f"  [OK] Document extraction: SUCCESS")
    print(f"  [OK] Disclaimer validation: {'SUCCESS' if 'disclaimer_result' in locals() else 'SKIPPED'}")
    print(f"  [OK] Registration validation: {'SUCCESS' if 'registration_parser' in locals() else 'SKIPPED'}")
    print(f"  [OK] Data consistency validation: {'SUCCESS' if 'consistency_result' in locals() else 'SKIPPED'}")
    
    if 'consistency_result' in locals():
        print(f"\nOverall Status: {consistency_result.overall_status.upper()}")
        if consistency_result.has_errors:
            print("  [WARNING] Errors found - document needs review")
        elif consistency_result.has_warnings:
            print("  [WARNING] Warnings found - document may need attention")
        else:
            print("  [OK] No errors or warnings - document appears compliant")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

