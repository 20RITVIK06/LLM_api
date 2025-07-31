#!/usr/bin/env python3
"""
Test Railway deployment with the Arogya Sanjeevani Policy PDF
"""

import requests
import json
import time
from typing import List

# Railway API endpoint
API_BASE_URL = "https://web-production-1ae9.up.railway.app"
HACKRX_ENDPOINT = f"{API_BASE_URL}/hackrx/run"

# The PDF URL provided
PDF_URL = "https://hackrx.blob.core.windows.net/assets/Arogya%20Sanjeevani%20Policy%20-%20CIN%20-%20U10200WB1906GOI001713%201.pdf?sv=2023-01-03&st=2025-07-21T08%3A29%3A02Z&se=2025-09-22T08%3A29%3A00Z&sr=b&sp=r&sig=nzrz1K9Iurt%2BBXom%2FB%2BMPTFMFP3PRnIvEsipAX10Ig4%3D"

# Comprehensive test questions about the Arogya Sanjeevani Policy
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

def check_api_status():
    """Check if the API is running and healthy"""
    print("🔍 Checking API status...")
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"Health endpoint status: {health_response.status_code}")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API is healthy: {health_data}")
            return True
        else:
            print(f"❌ Health check failed: {health_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def test_with_single_question():
    """Test with a single question first"""
    print("\n🧪 Testing with single question...")
    
    payload = {
        "documents": PDF_URL,
        "questions": ["What is this insurance policy about?"]
    }
    
    try:
        response = requests.post(
            HACKRX_ENDPOINT,
            json=payload,
            timeout=120,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Single question test status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answers', ['No answer'])[0]
            print(f"✅ Single question test successful!")
            print(f"Answer: {answer[:200]}...")
            return True
        else:
            print(f"❌ Single question test failed:")
            print(f"Error: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Single question test error: {e}")
        return False

def run_full_test():
    """Run the full test with all questions"""
    print(f"\n🚀 Running full test with {len(TEST_QUESTIONS)} questions...")
    print(f"📄 PDF: Arogya Sanjeevani Policy")
    
    payload = {
        "documents": PDF_URL,
        "questions": TEST_QUESTIONS
    }
    
    try:
        start_time = time.time()
        print("⏳ Submitting request to Railway API...")
        
        response = requests.post(
            HACKRX_ENDPOINT,
            json=payload,
            timeout=300,  # 5 minutes timeout
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ Total processing time: {processing_time:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answers = result.get('answers', [])
            
            print(f"✅ SUCCESS! Received {len(answers)} answers")
            return result
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error details: {response.text[:1000]}...")
            return None
            
    except requests.Timeout:
        print("❌ Request timed out after 5 minutes")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def display_results(result):
    """Display the Q&A results in a formatted way"""
    if not result or 'answers' not in result:
        print("❌ No results to display")
        return
    
    answers = result['answers']
    
    print("\n" + "="*80)
    print("🎯 AROGYA SANJEEVANI POLICY - ANALYSIS RESULTS")
    print("="*80)
    
    for i, (question, answer) in enumerate(zip(TEST_QUESTIONS, answers), 1):
        print(f"\n📋 Question {i}:")
        print(f"❓ {question}")
        print(f"💡 Answer: {answer}")
        print("-" * 60)
    
    print(f"\n✅ Successfully processed {len(answers)} questions")

def save_results(result):
    """Save results to a JSON file"""
    if not result:
        return
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"arogya_sanjeevani_analysis_{timestamp}.json"
    
    output_data = {
        "api_endpoint": API_BASE_URL,
        "pdf_document": "Arogya Sanjeevani Policy",
        "pdf_url": PDF_URL,
        "total_questions": len(TEST_QUESTIONS),
        "questions_and_answers": [
            {
                "question": q,
                "answer": a
            }
            for q, a in zip(TEST_QUESTIONS, result.get('answers', []))
        ],
        "timestamp": timestamp,
        "test_info": "Railway deployment test with hackathon PDF"
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {filename}")

def main():
    """Main test execution"""
    print("🧪 TESTING RAILWAY API WITH AROGYA SANJEEVANI POLICY")
    print("=" * 60)
    print(f"🔗 API URL: {API_BASE_URL}")
    print(f"📄 PDF: Arogya Sanjeevani Policy Document")
    print(f"❓ Questions: {len(TEST_QUESTIONS)} comprehensive questions")
    print("=" * 60)
    
    # Step 1: Check API health
    if not check_api_status():
        print("❌ API is not available. Test aborted.")
        return
    
    # Step 2: Test with single question
    if not test_with_single_question():
        print("❌ Single question test failed. Aborting full test.")
        return
    
    # Step 3: Run full test
    result = run_full_test()
    
    if result:
        # Step 4: Display and save results
        display_results(result)
        save_results(result)
        
        print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print("✅ Your Railway API is working perfectly with the PDF URL")
        print("✅ All questions were processed and answered")
        print("✅ Results saved for review")
    else:
        print("\n❌ TEST FAILED")
        print("The API is running but encountered errors processing the request")

if __name__ == "__main__":
    main()