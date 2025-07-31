#!/usr/bin/env python3
"""
Debug script for Railway API to identify the 500 error
"""

import requests
import json

API_BASE_URL = "https://web-production-1ae9.up.railway.app"

def test_endpoints():
    """Test various endpoints to debug the issue"""
    
    endpoints = [
        "/health",
        "/docs",
        "/test-redis",
    ]
    
    for endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        print(f"\n🔍 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Success: {data}")
                except:
                    print(f"✅ Success (non-JSON): {response.text[:200]}...")
            else:
                print(f"❌ Error: {response.text[:300]}...")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def test_hackrx_with_minimal_payload():
    """Test HackRX endpoint with minimal payload to see detailed error"""
    
    url = f"{API_BASE_URL}/hackrx/run"
    print(f"\n🔍 Testing HackRX endpoint with minimal payload")
    
    # Very simple test
    payload = {
        "documents": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "questions": ["What is this?"]
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_with_original_pdf():
    """Test with the original PDF URL but very detailed error reporting"""
    
    url = f"{API_BASE_URL}/hackrx/run"
    print(f"\n🔍 Testing with original PDF URL")
    
    payload = {
        "documents": "https://hackrx.blob.core.windows.net/assets/Arogya%20Sanjeevani%20Policy%20-%20CIN%20-%20U10200WB1906GOI001713%201.pdf?sv=2023-01-03&st=2025-07-21T08%3A29%3A02Z&se=2025-09-22T08%3A29%3A00Z&sr=b&sp=r&sig=nzrz1K9Iurt%2BBXom%2FB%2BMPTFMFP3PRnIvEsipAX10Ig4%3D",
        "questions": ["What is the policy name?"]
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Error Response:")
            print(f"Raw text: {response.text}")
            
            # Try to parse as JSON for better error details
            try:
                error_data = response.json()
                print(f"Error JSON: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error as JSON")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🔧 Debugging Railway API Issues")
    print("=" * 50)
    
    test_endpoints()
    test_hackrx_with_minimal_payload()
    test_with_original_pdf()