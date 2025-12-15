"""
Run All Tests - Complete Test Suite Runner

Runs all test files and provides a comprehensive summary.
"""

import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables before running tests
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_pytest():
    """Run pytest on all test files"""
    print("=" * 80)
    print("RUNNING PYTEST TESTS")
    print("=" * 80)
    print()
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def run_comprehensive_metadata_test():
    """Run the comprehensive metadata test"""
    print("\n" + "=" * 80)
    print("RUNNING COMPREHENSIVE METADATA TEST")
    print("=" * 80)
    print()
    
    result = subprocess.run(
        [sys.executable, "tests/test_metadata_extractor_comprehensive.py"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def main():
    """Run all tests"""
    print("=" * 80)
    print("FULL TEST SUITE RUNNER")
    print("=" * 80)
    print()
    
    results = {}
    
    # Run pytest tests
    results['pytest'] = run_pytest()
    
    # Run comprehensive metadata test
    results['metadata_comprehensive'] = run_comprehensive_metadata_test()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUITE SUMMARY")
    print("=" * 80)
    print()
    
    all_passed = all(results.values())
    
    for test_suite, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_suite}")
    
    print()
    if all_passed:
        print("[SUCCESS] All test suites passed!")
        return 0
    else:
        print("[FAILURE] Some test suites failed. See details above.")
        return 1


if __name__ == "__main__":
    exit(main())

