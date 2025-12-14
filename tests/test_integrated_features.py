"""
Test script for integrated features from teammate's work.

Tests:
1. Enhanced text matching (multi-level)
2. Medical-style recommendations
3. Detailed slide validation rules
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_text_matcher():
    """Test enhanced text matching"""
    print("=" * 70)
    print("TEST 1: Enhanced Text Matching")
    print("=" * 70)
    
    try:
        from backend.utils.text_matcher import EnhancedTextMatcher, TextNormalizer
        
        matcher = EnhancedTextMatcher(debug=True)
        
        # Test case 1: Exact match
        print("\n1. Testing exact match:")
        required = "Past performance is not indicative of future results"
        target = "This document shows past performance is not indicative of future results and should not be relied upon."
        
        is_match, confidence, method = matcher.match(required, target)
        print(f"   Result: {is_match}, Confidence: {confidence:.2%}, Method: {method}")
        assert is_match, "Exact match should be found"
        
        # Test case 2: High similarity
        print("\n2. Testing high similarity:")
        required = "The value of investments and income may go down as well as up"
        target = "Value of investments and income can go down as well as up and investors may not get back amount invested"
        
        is_match, confidence, method = matcher.match(required, target)
        print(f"   Result: {is_match}, Confidence: {confidence:.2%}, Method: {method}")
        
        # Test case 3: Keywords match
        print("\n3. Testing keywords match:")
        required = "This product promotes environmental or social characteristics"
        target = "The fund promotes environmental characteristics according to Article 8"
        
        is_match, confidence, method = matcher.match(required, target)
        print(f"   Result: {is_match}, Confidence: {confidence:.2%}, Method: {method}")
        
        print("\n[OK] Text matcher tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Text matcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_normalizer():
    """Test text normalization"""
    print("\n" + "=" * 70)
    print("TEST 2: Text Normalization")
    print("=" * 70)
    
    try:
        from backend.utils.text_matcher import TextNormalizer
        
        # Test normalization
        text = "Les performances passées ne préjugent pas des résultats futurs!"
        normalized = TextNormalizer.normalize(text)
        print(f"\nOriginal: {text}")
        print(f"Normalized: {normalized}")
        
        # Test keyword extraction
        keywords = TextNormalizer.extract_keywords(text)
        print(f"Keywords: {keywords}")
        
        print("\n[OK] Text normalizer tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Text normalizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_medical_recommendations():
    """Test medical-style recommendations engine"""
    print("\n" + "=" * 70)
    print("TEST 3: Medical-Style Recommendations")
    print("=" * 70)
    
    try:
        from backend.utils.medical_recommendations import MedicalRecommendationEngine
        
        # Generate sample medical report
        print("\nGenerating sample medical report...")
        
        report = MedicalRecommendationEngine.generate_medical_report(
            score=65,
            status="partially_compliant",
            total_missing=5,
            total_incorrect=2,
            structural_errors=["Missing cover page date", "Performance section too short"],
            inconsistent_items=[{"item": "disclaimer_1", "reason": "Present on 3/10 slides"}],
            non_compliant_sections=3,
            total_sections=10,
            incorrect_items=[
                {
                    'section_id': 5,
                    'id': 'wrong_disclaimer_type',
                    'reason': 'Article 8 disclaimer on Article 6 fund',
                    'intended_type': 'sfdr'
                }
            ],
            critical_missing=[
                {
                    'id': 'performance_disclaimer',
                    'sections': [3, 4, 5],
                    'preview': 'Past performance disclaimer required'
                }
            ],
            non_critical_missing=[
                {
                    'id': 'source_info',
                    'sections': [2, 6],
                    'preview': 'Source information missing'
                }
            ],
            doc_type="fund_presentation"
        )
        
        print("\n[CHART] Medical Diagnosis:")
        print(f"   Overall Health: {report['medical_diagnosis']['overall_health']}")
        print(f"   Severity: {report['medical_diagnosis']['severity_level']}")
        print(f"   Primary: {report['medical_diagnosis']['primary_diagnosis']}")
        
        print("\n Prescriptions:")
        for i, prescription in enumerate(report['prescriptions'][:3], 1):
            print(f"\n   {i}. {prescription['issue']} [{prescription['priority']}]")
            print(f"      Prescription: {prescription['prescription'][:100]}...")
            print(f"      Time: {prescription['estimated_time']}")
        
        print("\n[UP] Treatment Plan:")
        print(f"   Estimated Recovery Time: {report['treatment_plan']['estimated_recovery_time']}")
        print(f"   Total Prescriptions: {report['treatment_plan']['total_prescriptions']}")
        
        print("\n Prognosis:")
        print(f"   Recovery Likelihood: {report['prognosis']['recovery_likelihood']}")
        print(f"   Expected Final Score: {report['prognosis']['expected_final_score']}/100")
        
        print("\n[OK] Medical recommendations tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Medical recommendations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slide_validation_rules():
    """Test detailed slide validation rules"""
    print("\n" + "=" * 70)
    print("TEST 4: Detailed Slide Validation Rules")
    print("=" * 70)
    
    try:
        from backend.extractors.compliance_rules import SlideValidationRules
        
        # Test cover slide validation
        print("\n1. Testing cover slide validation:")
        cover_slide = {
            'text': 'ODDO BHF Asset Management\nFund Name: Global Equity Fund\nJanuary 2024',
            'slide_number': 1
        }
        errors = SlideValidationRules.validate_cover_slide(cover_slide)
        print(f"   Errors found: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
        
        # Test performance slide validation
        print("\n2. Testing performance slide validation:")
        perf_slide = {
            'text': 'Performance 2023: 15.2%\nShare Class: CR\nAs of 31/12/2023',
            'slide_number': 4
        }
        errors = SlideValidationRules.validate_performance_slide(
            perf_slide, 4, {'document_type': 'fund_presentation'}
        )
        print(f"   Errors found: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
        
        # Test structural consistency
        print("\n3. Testing structural consistency:")
        all_slides = [
            {'text': 'ODDO BHF Fund\n2024', 'slide_number': 1},
            {'text': 'Fund objective: Long-term capital growth', 'slide_number': 2},
            {'text': 'Performance: 10%', 'slide_number': 3},
        ]
        errors = SlideValidationRules.validate_structural_consistency(
            all_slides, {'document_type': 'fund_presentation'}
        )
        print(f"   Errors found: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
        
        print("\n[OK] Slide validation rules tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Slide validation rules test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_disclaimer_validator_integration():
    """Test enhanced disclaimer validator with text matching"""
    print("\n" + "=" * 70)
    print("TEST 5: Disclaimer Validator Integration")
    print("=" * 70)
    
    try:
        from backend.extractors.validators.disclaimer_validator import DisclaimerValidator
        
        print("\nInitializing validator (enhanced matching always enabled)...")
        validator = DisclaimerValidator(debug_matching=True)
        
        # Create mock extraction result
        extraction_result = {
            'full_text': '''
                ODDO BHF Asset Management presents the Global Equity Fund.
                Performance data as of December 2023.
                Past performance is not indicative of future results.
                The fund promotes environmental characteristics under Article 8 SFDR.
            ''',
            'structure': {
                'performance_slides': [3, 4],
                'disclaimer_categories': {
                    3: ['performance'],
                    4: ['sfdr', 'esg_risk']
                }
            }
        }
        
        metadata = {
            'language_code': 'ENGLISH',
            'is_professional_client': False,
            'management_company': 'OBAM SAS',
            'document_type': 'presentation'
        }
        
        print("\nRunning validation...")
        result = validator.validate(extraction_result, metadata)
        
        print(f"\n[CHART] Validation Results:")
        print(f"   Total Required: {result.total_required}")
        print(f"   Total Present: {result.total_present}")
        print(f"   Total Missing: {result.total_missing}")
        print(f"   Status: {'[FAIL] Has Errors' if result.has_errors else '[OK] No Errors'}")
        
        if result.missing_disclaimers:
            print(f"\n   Missing Disclaimers:")
            for missing in result.missing_disclaimers[:3]:
                print(f"   - {missing.disclaimer_type}")
                print(f"     Reason: {missing.reason}")
                if missing.match_score is not None:
                    print(f"     Best Match: {missing.match_score:.2%} ({missing.match_method})")
        
        print("\n[OK] Disclaimer validator integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Disclaimer validator integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n[TEST] TESTING INTEGRATED FEATURES FROM TEAMMATE'S WORK")
    print("=" * 70)
    
    results = []
    
    # Run all tests
    results.append(("Text Matcher", test_text_matcher()))
    results.append(("Text Normalizer", test_text_normalizer()))
    results.append(("Medical Recommendations", test_medical_recommendations()))
    results.append(("Slide Validation Rules", test_slide_validation_rules()))
    results.append(("Disclaimer Validator Integration", test_disclaimer_validator_integration()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n[WARNING] {total_tests - total_passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
