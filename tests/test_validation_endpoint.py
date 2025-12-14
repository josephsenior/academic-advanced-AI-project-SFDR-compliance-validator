#!/usr/bin/env python3
"""
Test the validation endpoint end-to-end
"""

import sys
import requests
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:5000/api/v1"


def test_validation_endpoint():
    """Test the validation endpoint"""
    print("=" * 70)
    print("Validation Endpoint Test")
    print("=" * 70)
    print()
    
    # Step 1: Check if server is running
    print("1. Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"   [OK] Server is running")
            print(f"   - Response: {response.json()}")
        else:
            print(f"   [ERROR] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   [ERROR] Cannot connect to server at {BASE_URL}")
        print(f"   Please start the server first: python api.py")
        return False
    except Exception as e:
        print(f"   [ERROR] Health check failed: {e}")
        return False
    
    print()
    
    # Step 2: Upload a test document
    print("2. Uploading test document...")
    test_file = None
    test_files = [
        "dataset/example_1/47861-6PG-FR-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
        "dataset/example_1/47861-6PG-GB-ODDO BHF Algo Trend US-20250831 v3 pn.pptx",
    ]
    
    for f in test_files:
        if Path(f).exists():
            test_file = Path(f)
            break
    
    if not test_file:
        print(f"   [ERROR] No test document found")
        return False
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/vnd.openxmlformats-officedocument.presentationml.presentation')}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
        
        if response.status_code not in [200, 201]:
            print(f"   [ERROR] Upload failed: {response.status_code}")
            print(f"   - Response: {response.text}")
            return False
        
        upload_result = response.json()
        document_id = upload_result.get('document_id')
        
        if not document_id:
            print(f"   [ERROR] No document_id in upload response")
            print(f"   - Response: {upload_result}")
            return False
        
        print(f"   [OK] Document uploaded successfully")
        print(f"   - Document ID: {document_id}")
        print(f"   - Status: {upload_result.get('status')}")
        
    except Exception as e:
        print(f"   [ERROR] Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Step 3: Check status (validation will trigger extraction if needed)
    print("3. Checking document status...")
    try:
        response = requests.get(f"{BASE_URL}/status/{document_id}", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            print(f"   - Status: {status}, Progress: {progress}%")
        else:
            print(f"   - Status check returned {response.status_code}")
    except Exception as e:
        print(f"   - Status check failed: {e}")
    
    print()
    print("   Note: Validation endpoint will trigger extraction if needed")
    print()
    
    # Step 4: Run validation (this will also trigger extraction)
    print("4. Running validation...")
    print("   This may take 2-5 minutes (extraction + validation)...")
    try:
        validation_options = {
            "enable_disclaimers": True,
            "enable_esg": False
        }
        
        # Use a longer timeout for the full pipeline
        response = requests.post(
            f"{BASE_URL}/validate/{document_id}",
            json={"options": validation_options},
            timeout=300  # 5 minutes for full extraction + validation
        )
        
        if response.status_code != 200:
            print(f"   [ERROR] Validation failed: {response.status_code}")
            print(f"   - Response: {response.text[:500]}")
            return False
        
        validation_result = response.json()
        
        print(f"   [OK] Validation completed successfully!")
        print(f"   - Status: {validation_result.get('status')}")
        print(f"   - Progress: {validation_result.get('progress')}%")
        
        results = validation_result.get('results', {})
        if results:
            print(f"   - Total issues: {results.get('total_issues', 0)}")
            print(f"   - Has errors: {results.get('has_errors', False)}")
            print(f"   - Has warnings: {results.get('has_warnings', False)}")
            
            # Show breakdown
            if 'data_consistency' in results:
                dc = results['data_consistency']
                print(f"   - Data consistency issues: {dc.get('total_issues', 0)}")
            
            if 'disclaimer_validation' in results:
                dv = results['disclaimer_validation']
                print(f"   - Missing disclaimers: {dv.get('missing_count', 0)}")
            
            if 'registration_validation' in results:
                rv = results['registration_validation']
                print(f"   - Invalid countries: {rv.get('invalid_countries', 0)}")
        
    except requests.exceptions.Timeout:
        print(f"   [ERROR] Validation timed out (took longer than 120 seconds)")
        return False
    except Exception as e:
        print(f"   [ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Step 5: Check final status
    print("5. Checking final status...")
    try:
        response = requests.get(f"{BASE_URL}/status/{document_id}", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"   - Status: {status_data.get('status')}")
            print(f"   - Progress: {status_data.get('progress')}%")
    except Exception as e:
        print(f"   - Status check failed: {e}")
    
    print()
    
    # Step 6: Get final results
    print("5. Getting final results...")
    try:
        response = requests.get(f"{BASE_URL}/results/{document_id}", timeout=10)
        if response.status_code == 200:
            results = response.json()
            print(f"   [OK] Results retrieved")
            print(f"   - Document ID: {results.get('document_id')}")
            print(f"   - Status: {results.get('status')}")
            
            # Save results to file
            output_file = Path("test_output") / "validation_endpoint_results.json"
            output_file.parent.mkdir(exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"   - Results saved to: {output_file}")
        else:
            print(f"   [WARNING] Could not retrieve results: {response.status_code}")
    except Exception as e:
        print(f"   [WARNING] Could not retrieve results: {e}")
    
    print()
    print("=" * 70)
    print("[SUCCESS] Validation endpoint test completed!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_validation_endpoint()
    sys.exit(0 if success else 1)

