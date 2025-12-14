
import os
import sys
import subprocess
import glob
import time
from pathlib import Path

def run_test_file(test_file):
    print(f"Running {test_file}...", end="", flush=True)
    start_time = time.time()
    try:
        # Run pytest on the single file with a timeout
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout per file for integration tests
        )
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f" PASS ({duration:.2f}s)")
            return "PASS", result.stdout
        else:
            print(f" FAIL ({duration:.2f}s)")
            return "FAIL", result.stdout + "\n" + result.stderr
            
    except subprocess.TimeoutExpired:
        print(f" TIMEOUT ({time.time() - start_time:.2f}s)")
        return "TIMEOUT", "Test execution timed out"
    except Exception as e:
        print(f" ERROR ({time.time() - start_time:.2f}s)")
        return "ERROR", str(e)

def main():
    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))
    
    print(f"Found {len(test_files)} test files in {test_dir.resolve()}")
    
    results = {}
    
    for test_file in sorted(test_files):
        status, output = run_test_file(str(test_file))
        results[test_file.name] = (status, output)
        
    print("\n" + "="*60)
    print("TEST SUITE SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for filename, (status, _) in results.items():
        if status == "PASS":
            passed += 1
            print(f"[PASS] {filename}")
        else:
            failed += 1
            print(f"[{status}] {filename}")
            
    print("-" * 60)
    print(f"Total: {len(test_files)} | Passed: {passed} | Failed: {failed}")
    
    if failed > 0:
        print("\n" + "="*60)
        print("FAILURE DETAILS")
        print("="*60)
        for filename, (status, output) in results.items():
            if status != "PASS":
                print(f"\n--- {filename} ({status}) ---")
                # Print last 20 lines of output for brevity
                lines = output.splitlines()
                print("\n".join(lines[-20:]))

if __name__ == "__main__":
    main()
