"""
Quick Test Runner - Runs fast tests without LLM dependencies

This script runs tests that don't require LLM API calls or long-running operations.
Useful for quick verification during development.
"""

import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_quick_tests():
    """Run quick tests that don't require LLM or external services"""
    print("=" * 80)
    print("QUICK TEST SUITE - Fast Tests Only")
    print("=" * 80)
    print()
    
    # Tests that should run quickly
    quick_test_files = [
        "tests/test_api.py",
        "tests/test_api_smoke_test_client.py",
        "tests/test_compliance_rules.py",
        "tests/test_edge_cases.py",
        "tests/test_refactor.py",
    ]
    
    # Filter to only existing files
    existing_tests = [f for f in quick_test_files if Path(f).exists()]
    
    if not existing_tests:
        print("[WARNING] No quick test files found!")
        return False
    
    print(f"Running {len(existing_tests)} quick test files...")
    print()
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + existing_tests + ["-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


def main():
    """Run quick tests"""
    success = run_quick_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("[SUCCESS] All quick tests passed!")
        return 0
    else:
        print("[FAILURE] Some quick tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())
