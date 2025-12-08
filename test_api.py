"""
Test script for API endpoints
"""

import requests
import json
from pathlib import Path
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
TEST_FILE = "dataset/example_1/ODDO BHF Active Small Cap_Product Presentation_4p_Mai 2024.pptx"

def test_api():
    print("=" * 80)
    print("API Test Suite")
    print("=" * 80)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
        print("   ✅ Health check passed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Upload Document
    print("\n2. Testing Document Upload...")
    try:
        if not Path(TEST_FILE).exists():
            print(f"   ⚠️  Test file not found: {TEST_FILE}")
            print("   Skipping upload test")
            return
        
        with open(TEST_FILE, 'rb') as f:
            files = {'file': f}
            metadata = {
                "Société de Gestion": "ODDO BHF ASSET MANAGEMENT SAS",
                "Le client est-il un professionnel": False
            }
            data = {'metadata': json.dumps(metadata)}
            
            response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        assert response.status_code == 201
        document_id = result['document_id']
        print(f"   ✅ Upload successful. Document ID: {document_id}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 3: Get Status
    print("\n3. Testing Status Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/status/{document_id}")
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Document Status: {result['status']}")
        print(f"   Progress: {result['progress']}%")
        assert response.status_code == 200
        print("   ✅ Status check passed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Start Validation
    print("\n4. Testing Validation...")
    try:
        validation_options = {
            "options": {
                "enable_llm": False,
                "enable_esg": False,
                "enable_disclaimers": True
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/validate/{document_id}",
            json=validation_options
        )
        
        print(f"   Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"   Validation Status: {result['status']}")
            print(f"   Progress: {result['progress']}%")
            
            if result['status'] == 'completed':
                validation_result = result['results']
                print(f"\n   Validation Results:")
                print(f"   - Compliance Score: {validation_result['compliance_score']}%")
                print(f"   - Total Issues: {validation_result['total_issues']}")
                print(f"   - By Severity:")
                for severity, count in validation_result['issues_by_severity'].items():
                    print(f"     * {severity.capitalize()}: {count}")
                print(f"   - Tables Checked: {validation_result['statistics']['total_tables_checked']}")
                print(f"   - Charts Analyzed: {validation_result['statistics']['total_charts_analyzed']}")
                
                print("   ✅ Validation completed")
            else:
                print("   ⏳ Validation in progress...")
        else:
            print(f"   ❌ Error: {result}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 5: Get Results
    print("\n5. Testing Results Retrieval...")
    try:
        time.sleep(1)  # Wait a moment
        response = requests.get(f"{API_BASE_URL}/results/{document_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Total Issues: {result['total_issues']}")
            print(f"   Categories: {list(result['issues_by_category'].keys())}")
            
            # Test filtering
            response_filtered = requests.get(
                f"{API_BASE_URL}/results/{document_id}?severity=critical"
            )
            if response_filtered.status_code == 200:
                filtered = response_filtered.json()
                critical_count = sum(
                    len(issues) for issues in filtered['issues_by_category'].values()
                )
                print(f"   Critical Issues (filtered): {critical_count}")
            
            print("   ✅ Results retrieval passed")
        else:
            print(f"   ⚠️  Results not ready yet: {response.json()}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: List Documents
    print("\n6. Testing Document List...")
    try:
        response = requests.get(f"{API_BASE_URL}/list?limit=10")
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Total Documents: {result['total']}")
        print(f"   Returned: {len(result['documents'])}")
        
        if result['documents']:
            doc = result['documents'][0]
            print(f"   Latest Document:")
            print(f"   - ID: {doc['document_id'][:20]}...")
            print(f"   - Filename: {doc['filename']}")
            print(f"   - Status: {doc['status']}")
        
        print("   ✅ List documents passed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: Generate Report
    print("\n7. Testing Report Generation...")
    try:
        response = requests.get(f"{API_BASE_URL}/report/{document_id}?format=json")
        
        if response.status_code == 200:
            print(f"   Report generated successfully")
            print(f"   Size: {len(response.content)} bytes")
            print("   ✅ Report generation passed")
        else:
            print(f"   ⚠️  Report not ready: {response.json()}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ API Test Suite Complete")
    print("=" * 80)
    print(f"\nDocument ID for further testing: {document_id}")
    print(f"\nTry these commands:")
    print(f"  curl {API_BASE_URL}/status/{document_id}")
    print(f"  curl {API_BASE_URL}/results/{document_id}")
    print(f"  curl -X POST {API_BASE_URL}/fix/{document_id}")
    print(f"  curl {API_BASE_URL}/download/{document_id}?type=corrected -o corrected.pptx")
    print()

if __name__ == "__main__":
    try:
        test_api()
    except KeyboardInterrupt:
        print("\n\n⏸️  Test interrupted")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
