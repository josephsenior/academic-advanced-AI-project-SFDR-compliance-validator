"""
Example: Disclaimer Validation

Demonstrates how to use the DisclaimerValidator to check if required
disclaimers are present in marketing documents.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.disclaimer_validator import DisclaimerValidator
from src.extractors.registration_parser import RegistrationParser
from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent


def main():
    """Example usage of disclaimer validation"""
    
    print("=" * 60)
    print("Disclaimer Validation Example")
    print("=" * 60)
    print()
    
    # 1. Initialize disclaimer validator
    print("[1] Initializing Disclaimer Validator...")
    disclaimer_validator = DisclaimerValidator()
    print(f"    Loaded glossary: {len(disclaimer_validator.glossary)} languages")
    print()
    
    # 2. Initialize registration parser
    print("[2] Initializing Registration Parser...")
    registration_parser = RegistrationParser()
    print(f"    Loaded registrations: {len(registration_parser.registrations)} funds")
    print()
    
    # 3. Extract document
    print("[3] Extracting document...")
    pipeline = ExtractionPipeline(use_llm=False)
    doc_path = "dataset/example_1/FINAL 47861-6PG-GB-ODDO BHF Algo Trend US-20250831vdef.pptx"
    
    if not Path(doc_path).exists():
        print(f"    Document not found: {doc_path}")
        print("    Please provide a valid document path")
        return
    
    result = pipeline.process_document(doc_path)
    extraction_result = result['extraction_result']
    metadata = result['metadata']
    
    print(f"    Extracted {extraction_result.get('total_slides', 0)} slides")
    print(f"    Found {extraction_result.get('total_tables', 0)} tables")
    print(f"    Found {extraction_result.get('total_charts', 0)} charts")
    print()
    
    # 4. Validate disclaimers
    print("[4] Validating Disclaimers...")
    disclaimer_result = disclaimer_validator.validate(
        extraction_result,
        metadata,
        result.get('document_id')
    )
    
    print(f"    Required disclaimers: {disclaimer_result.total_required}")
    print(f"    Present disclaimers: {disclaimer_result.total_present}")
    print(f"    Missing disclaimers: {disclaimer_result.total_missing}")
    print()
    
    if disclaimer_result.required_disclaimers:
        print("    Required Disclaimers:")
        for req in disclaimer_result.required_disclaimers:
            status = "[PASS]" if req.disclaimer_type in disclaimer_result.present_disclaimers else "[FAIL]"
            print(f"      {status} {req.disclaimer_type}: {req.reason}")
    print()
    
    if disclaimer_result.missing_disclaimers:
        print("    Missing Disclaimers:")
        for missing in disclaimer_result.missing_disclaimers:
            print(f"      [MISSING] {missing.disclaimer_type}: {missing.reason}")
            if missing.expected_text:
                print(f"        Expected text: {missing.expected_text[:100]}...")
    else:
        print("    [PASS] All required disclaimers are present!")
    print()
    
    # 5. Validate country registrations
    print("[5] Validating Country Registrations...")
    fund_name = metadata.get('fund_name', 'ODDO BHF Algo Trend US')
    mentioned_countries = extraction_result.get('structure', {}).get('countries_detected', [])
    
    if mentioned_countries:
        print(f"    Fund: {fund_name}")
        print(f"    Mentioned countries: {', '.join(mentioned_countries)}")
        
        validation = registration_parser.validate_country_mentions(
            mentioned_countries,
            fund_name
        )
        
        print("    Registration status:")
        for country, is_registered in validation.items():
            status = "[PASS]" if is_registered else "[FAIL]"
            print(f"      {status} {country}: {'Registered' if is_registered else 'NOT Registered'}")
    else:
        print("    No countries mentioned in document")
    print()
    
    # 6. Integrated validation with Data Consistency Agent
    print("[6] Integrated Validation with Data Consistency Agent...")
    agent = DataConsistencyAgent(
        enable_disclaimer_validation=True,
        disclaimer_validator=disclaimer_validator
    )
    
    consistency_result = agent.validate(
        extraction_result,
        metadata,
        result.get('document_id')
    )
    
    print(f"    Overall status: {consistency_result.overall_status}")
    print(f"    Has errors: {consistency_result.has_errors}")
    print(f"    Has warnings: {consistency_result.has_warnings}")
    
    if consistency_result.disclaimer_validation:
        disc_val = consistency_result.disclaimer_validation
        print(f"    Disclaimer validation: {disc_val.get('total_missing', 0)} missing")
    
    print()
    print("=" * 60)
    print("Example Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

