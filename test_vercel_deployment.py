#!/usr/bin/env python3
"""
Test script for Vercel deployment
"""

import requests
import json
import time
from typing import List

# Update this URL after deployment
VERCEL_URL = "https://your-app.vercel.app"  # Replace with your actual Vercel URL
HACKRX_ENDPOINT = f"{VERCEL_URL}/hackrx/run"

# Test PDF URL
PDF_URL = "https://hackrx.blob.core.windows.net/assets/Arogya%20Sanjeevani%20Policy%20-%20CIN%20-%20U10200WB1906GOI001713%201.pdf?sv=2023-01-03&st=2025-07-21T08%3A29%3A02Z&se=2025-09-22T08%3A29%3A00Z&sr=b&sp=r&sig=nzrz1K9Iurt%2BBXom%2FB%2BMPTFMFP3PRnIvEsipAX10Ig4%3D"

# Test questions
TEST_QUESTIONS = [
    "What is the maximum sum insured available under this policy?",
    "What is the waiting period for pre-existing diseases?",
    "What are the key exclusions in this policy?",
    "What is the minimum entry age for this policy?",
    "What is the maximum entry age for this policy?"
]

def test_vercel_deployment():
    """Test the Vercel deployment"""
    
    print("🧪 Testing Vercel Deployment")
    print("=" * 50)
    print(f"🔗 URL: {VERCEL_URL}")
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{VERCEL_URL}/health", timeout=10)
        print(f"Health check: {health_response.status_code}")
        
        if health_response.status_code == 200:
            print(f"✅ Health: {health_response.json()}")
        else:
            print(f"❌ Health failed: {health_response.text}")
            return
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test HackRX endpoint
    payload = {
        "documents": PDF_URL,
        "questions": TEST_QUESTIONS
    }
    
    try:
        print(f"\n🚀 Testing HackRX endpoint with {len(TEST_QUESTIONS)} questions...")
        start_time = time.time()
        
        response = requests.post(
            HACKRX_ENDPOINT,
            json=payload,
            timeout=300,  # 5 minutes
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answers = result.get('answers', [])
            
            print(f"✅ SUCCESS! Received {len(answers)} answers")
            
            # Display results
            print("\n" + "="*60)
            print("🎯 RESULTS")
            print("="*60)
            
            for i, (question, answer) in enumerate(zip(TEST_QUESTIONS, answers), 1):
                print(f"\n📋 Question {i}:")
                print(f"❓ {question}")
                print(f"💡 {answer}")
                print("-" * 40)
            
            # Save results
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"vercel_test_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "vercel_url": VERCEL_URL,
                    "pdf_url": PDF_URL,
                    "questions": TEST_QUESTIONS,
                    "answers": answers,
                    "processing_time": processing_time,
                    "timestamp": timestamp
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: {filename}")
            print("🎉 Vercel deployment test completed successfully!")
            
        else:
            print(f"❌ Request failed: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Update VERCEL_URL with your actual deployment URL")
    print("📝 After deployment, run: python test_vercel_deployment.py")
    print()
    
    if "your-app.vercel.app" in VERCEL_URL:
        print("❌ Please update VERCEL_URL in this script with your actual Vercel URL")
    else:
        test_vercel_deployment()