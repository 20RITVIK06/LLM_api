#!/usr/bin/env python3
"""
Debug Railway environment configuration
"""

import requests
import json

API_BASE_URL = "https://web-production-1ae9.up.railway.app"

def test_service_endpoints():
    """Test individual service endpoints to identify which service is failing"""
    
    endpoints_to_test = [
        ("/health", "Health check"),
        ("/test-redis", "Redis connection test"),
    ]
    
    print("🔍 Testing individual service endpoints...")
    
    for endpoint, description in endpoints_to_test:
        url = f"{API_BASE_URL}{endpoint}"
        print(f"\n📋 Testing {description}: {endpoint}")
        
        try:
            response = requests.get(url, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ {description} working: {data}")
                except:
                    print(f"✅ {description} working (non-JSON response)")
            else:
                print(f"❌ {description} failed:")
                print(f"Response: {response.text[:300]}...")
                
        except Exception as e:
            print(f"❌ {description} error: {e}")

def test_minimal_hackrx():
    """Test HackRX with absolute minimal payload to isolate the issue"""
    
    print(f"\n🧪 Testing minimal HackRX payload...")
    
    # Test with a very simple, small PDF
    test_payloads = [
        {
            "name": "Empty questions test",
            "payload": {
                "documents": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                "questions": []
            }
        },
        {
            "name": "Single simple question",
            "payload": {
                "documents": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", 
                "questions": ["What is this?"]
            }
        }
    ]
    
    for test in test_payloads:
        print(f"\n🔬 {test['name']}:")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/hackrx/run",
                json=test['payload'],
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                print("✅ This test passed!")
                break
            
        except Exception as e:
            print(f"❌ Error: {e}")

def check_docs_endpoint():
    """Check if we can access the API documentation"""
    
    print(f"\n📚 Checking API documentation...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        print(f"Docs endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API docs accessible - this confirms FastAPI is running")
        else:
            print(f"❌ Docs not accessible: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Docs endpoint error: {e}")

def main():
    """Main diagnostic function"""
    
    print("🔧 RAILWAY DEPLOYMENT DIAGNOSTICS")
    print("=" * 50)
    print(f"🔗 API URL: {API_BASE_URL}")
    print("=" * 50)
    
    check_docs_endpoint()
    test_service_endpoints()
    test_minimal_hackrx()
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS SUMMARY:")
    print("=" * 50)
    print("Based on the 500 error with empty detail, likely causes:")
    print("1. ❌ Missing environment variables (GEMINI_API_KEY, PINECONE_API_KEY)")
    print("2. ❌ Service initialization failure (Gemini, Pinecone, or Redis)")
    print("3. ❌ Dependency issues in Railway environment")
    print("\n💡 RECOMMENDED FIXES:")
    print("1. Check Railway environment variables are set correctly")
    print("2. Verify all API keys are valid and have proper permissions")
    print("3. Check Railway logs for detailed error messages")
    print("4. Ensure all dependencies in requirements.txt are compatible")

if __name__ == "__main__":
    main()