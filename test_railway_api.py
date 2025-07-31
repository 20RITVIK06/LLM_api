#!/usr/bin/env python3
"""
Test script for HackRX API endpoint with Railway deployment
Testing the Arogya Sanjeevani Policy PDF URL
"""

import requests
import json
import time
from typing import List

# API endpoint - Railway deployment
API_BASE_URL = "https://web-production-1ae9.up.railway.app"
HACKRX_ENDPOINT = f"{API_BASE_URL}/hackrx/run"

# The PDF URL provided
PDF_URL = "https://hackrx.blob.core.windows.net/assets/Arogya%20Sanjeevani%20Policy%20-%20CIN%20-%20U10200WB1906GOI001713%201.pdf?sv=2023-01-03&st=2025-07-21T08%3A29%3A02Z&se=2025-09-22T08%3A29%3A00Z&sr=b&sp=r&sig=nzrz1K9Iurt%2BBXom%2FB%2BMPTFMFP3PRnIvEsipAX10Ig4%3D"

# Test questions about the Arogya Sanjeevani Policy
TEST_QUESTIONS = [
    "What is the maximum sum insured available under this policy?",
    "What is the waiting period for pre-existing diseases?",
    "What are the key exclusions in this policy?",
    "What is the minimum entry age for this policy?",
    "What is the maximum entry age for this policy?",
    "What is the room rent limit under this policy?",
    "What are the co-payment requirements?",
    "What is the policy term and renewal conditions?",
    "What diseases are covered under this policy?",
    "What is the claim settlement process?",
    "Are maternity benefits covered?",
    "What is the coverage for pre and post hospitalization expenses?",
    "What are the network hospital benefits?",
    "What is the premium payment frequency?",
    "What documents are required for claims?"
]

def test_api_health():
    """Test if the API is running"""
    try:
        print(f"🔍 Testing API health: {API_BASE_URL}/health")
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                print(f"✅ API is running and healthy: {health_data}")
                return True
            except:
                print("✅ API is running (non-JSON response)")
                return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    except requests.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def submit_hackrx_request(pdf_url: str, questions: List[str]):
    """Submit request to HackRX endpoint"""
    
    print(f"\n🚀 Submitting request to HackRX endpoint...")
    print(f"🔗 Endpoint: {HACKRX_ENDPOINT}")
    print(f"📄 PDF URL: {pdf_url[:80]}...")
    print(f"❓ Number of questions: {len(questions)}")
    
    # Prepare request payload
    payload = {
        "documents": pdf_url,
        "questions": questions
    }
    
    try:
        # Make the request
        print("⏳ Sending request...")
        start_time = time.time()
        response = requests.post(
            HACKRX_ENDPOINT,
            json=payload,
            timeout=300,  # 5 minutes timeout for processing
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request successful!")
            return result
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error response: {response.text[:500]}...")
            return None
            
    except requests.Timeout:
        print("❌ Request timed out (5 minutes)")
        return None
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def display_results(result: dict, questions: List[str]):
    """Display the results in a formatted way"""
    
    if not result or 'answers' not in result:
        print("❌ No valid results to display")
        return
    
    answers = result['answers']
    
    print("\n" + "="*80)
    print("🎯 AROGYA SANJEEVANI POLICY - QUESTION & ANSWER RESULTS")
    print("="*80)
    
    for i, (question, answer) in enumerate(zip(questions, answers), 1):
        print(f"\n📋 Question {i}:")
        print(f"❓ {question}")
        print(f"💡 Answer: {answer}")
        print("-" * 60)
    
    print(f"\n✅ Successfully processed {len(answers)} questions")

def test_simple_request():
    """Test with just one question first"""
    print("\n🧪 Testing with a single question first...")
    
    simple_payload = {
        "documents": PDF_URL,
        "questions": ["What is this policy about?"]
    }
    
    try:
        response = requests.post(
            HACKRX_ENDPOINT,
            json=simple_payload,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Simple test status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Simple test successful!")
            print(f"Answer: {result.get('answers', ['No answer'])[0]}")
            return True
        else:
            print(f"❌ Simple test failed: {response.text[:300]}...")
            return False
            
    except Exception as e:
        print(f"❌ Simple test error: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 Testing HackRX API on Railway with Arogya Sanjeevani Policy PDF")
    print("="*70)
    
    # Test API health first
    if not test_api_health():
        print("❌ API is not available. Deployment might be down.")
        return
    
    # Test with simple request first
    if not test_simple_request():
        print("❌ Simple test failed. Skipping full test.")
        return
    
    # Submit the full request
    print("\n🚀 Running full test with all questions...")
    result = submit_hackrx_request(PDF_URL, TEST_QUESTIONS)
    
    if result:
        # Display results
        display_results(result, TEST_QUESTIONS)
        
        # Save results to file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"railway_hackrx_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "api_url": API_BASE_URL,
                "pdf_url": PDF_URL,
                "questions": TEST_QUESTIONS,
                "answers": result.get('answers', []),
                "timestamp": timestamp,
                "processing_info": "Arogya Sanjeevani Policy Analysis via Railway"
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")
        print(f"🎉 Test completed successfully!")
    else:
        print("❌ Test failed - no results obtained")

if __name__ == "__main__":
    main()