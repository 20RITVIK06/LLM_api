#!/usr/bin/env python3
"""
Vercel-optimized FastAPI application for Document Query Assistant
Serverless deployment with optimized cold start performance
"""

import os
import sys
import json
import tempfile
import asyncio
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import requests
import google.generativeai as genai

# Import our models and services
from models import Clause
from config import config

# Vercel-specific optimizations
app = FastAPI(
    title="Document Query Assistant - Vercel",
    version="1.0.0",
    description="Serverless document analysis API optimized for Vercel"
)

# CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for service instances (initialized on first request)
_gemini_configured = False
_pinecone_service = None

# Hackathon-specific models
class HackRXRequest(BaseModel):
    documents: str  # URL to the PDF document
    questions: List[str]  # List of questions to ask

class HackRXResponse(BaseModel):
    answers: List[str]  # List of direct answers

def configure_gemini():
    """Configure Gemini API (lazy initialization)"""
    global _gemini_configured
    
    if not _gemini_configured:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        _gemini_configured = True
        print("✅ Gemini API configured")

def get_pinecone_service():
    """Get Pinecone service with lazy initialization"""
    global _pinecone_service
    
    if _pinecone_service is None:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=config.PINECONE_API_KEY)
            _pinecone_service = pc.Index(config.PINECONE_INDEX_NAME)
            print("✅ Pinecone service initialized")
        except Exception as e:
            print(f"❌ Pinecone initialization failed: {e}")
            _pinecone_service = False
    
    return _pinecone_service if _pinecone_service is not False else None

def extract_text_from_pdf_url(pdf_url: str) -> str:
    """Extract text from PDF URL using multiple methods"""
    import PyPDF2
    import pdfplumber
    
    # Download PDF
    response = requests.get(pdf_url, timeout=30)
    response.raise_for_status()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(response.content)
        temp_file_path = temp_file.name
    
    text = ""
    
    try:
        # Method 1: Try pdfplumber first
        try:
            with pdfplumber.open(temp_file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PAGE {page_num + 1} ---\n"
                        text += page_text + "\n"
            
            if text.strip():
                print("✅ Text extracted using pdfplumber")
                return clean_pdf_text(text)
        
        except Exception as e:
            print(f"⚠️ pdfplumber failed: {e}")
        
        # Method 2: Fallback to PyPDF2
        try:
            with open(temp_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PAGE {page_num + 1} ---\n"
                        text += page_text + "\n"
            
            if text.strip():
                print("✅ Text extracted using PyPDF2")
                return clean_pdf_text(text)
        
        except Exception as e:
            print(f"❌ PyPDF2 also failed: {e}")
        
        if not text.strip():
            raise ValueError("Could not extract text from PDF")
        
        return clean_pdf_text(text)
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def clean_pdf_text(text: str) -> str:
    """Clean and normalize text extracted from PDF"""
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Remove page headers/footers
    text = re.sub(r'--- PAGE \d+ ---\n', '', text)
    
    # Fix common PDF extraction issues
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\n\2', text)
    
    return text.strip()

def split_text_into_clauses(text: str, document_name: str) -> List[Dict[str, Any]]:
    """Split document text into meaningful clauses"""
    
    # Split by paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    clauses = []
    for i, paragraph in enumerate(paragraphs):
        if len(paragraph) < 100:  # Skip very short paragraphs
            continue
            
        clause_id = f"{document_name}_clause_{i+1:03d}"
        
        clause = {
            "id": clause_id,
            "content": paragraph,
            "document": document_name,
            "section": i + 1,
            "metadata": {
                "word_count": len(paragraph.split()),
                "char_count": len(paragraph)
            }
        }
        clauses.append(clause)
    
    return clauses

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using Gemini"""
    configure_gemini()
    
    try:
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None

def upload_clauses_to_pinecone(clauses: List[Dict[str, Any]]) -> bool:
    """Upload clauses to Pinecone with embeddings"""
    pinecone_service = get_pinecone_service()
    
    if not pinecone_service:
        print("❌ Pinecone service not available")
        return False
    
    print(f"🚀 Processing {len(clauses)} clauses...")
    
    vectors_to_upsert = []
    
    for clause in clauses:
        try:
            embedding = generate_embedding(clause['content'])
            if embedding is None:
                continue
            
            vector = {
                "id": clause['id'],
                "values": embedding,
                "metadata": {
                    "content": clause['content'],
                    "document": clause['document'],
                    "section": clause['section']
                }
            }
            vectors_to_upsert.append(vector)
            
        except Exception as e:
            print(f"❌ Error processing clause {clause['id']}: {e}")
            continue
    
    if not vectors_to_upsert:
        print("❌ No vectors to upload")
        return False
    
    # Upload in batches
    batch_size = 100
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        try:
            pinecone_service.upsert(vectors=batch)
            print(f"✅ Uploaded batch {i//batch_size + 1}")
        except Exception as e:
            print(f"❌ Batch upload failed: {e}")
            return False
    
    return True

async def generate_answer(question: str, clauses: List[Clause]) -> str:
    """Generate answer using Gemini"""
    configure_gemini()
    
    # Prepare context
    clauses_context = "\n".join([
        f"Clause {i+1}: {clause.content}"
        for i, clause in enumerate(clauses)
    ])
    
    prompt = f"""You are an expert insurance policy analyst. Based on the provided policy clauses, answer the question directly and concisely.

Policy Clauses:
{clauses_context}

Question: "{question}"

Instructions:
1. Provide a direct, factual answer based ONLY on the provided clauses
2. Be specific about numbers, timeframes, percentages, and conditions
3. If the information is not in the clauses, say "Information not available in the provided policy document"
4. Keep the answer concise but complete
5. Do not add explanations or interpretations beyond what's stated

Answer:"""

    try:
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        # Clean up formatting
        if answer.startswith('"') and answer.endswith('"'):
            answer = answer[1:-1]
        
        return answer
        
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        return f"Error processing question: {str(e)}"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Document Query Assistant - Vercel Deployment",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Document Query Assistant",
        "platform": "Vercel Serverless"
    }

@app.post("/hackrx/run", response_model=HackRXResponse)
async def hackrx_run(request: HackRXRequest):
    """HackRX endpoint - Process document from URL and answer multiple questions"""
    try:
        print(f"🚀 HackRX request received with {len(request.questions)} questions")
        
        # Initialize services
        configure_gemini()
        pinecone_service = get_pinecone_service()
        
        if not pinecone_service:
            raise HTTPException(status_code=503, detail="Pinecone service not available")
        
        document_name = "hackrx_policy"
        
        print("📥 Processing document from URL...")
        print(f"🔗 URL: {request.documents[:80]}...")
        
        # Extract text from PDF
        text = extract_text_from_pdf_url(request.documents)
        print(f"✅ Extracted {len(text)} characters from PDF")
        
        # Split into clauses
        clauses = split_text_into_clauses(text, document_name)
        print(f"✅ Split into {len(clauses)} clauses")
        
        # Upload to Pinecone
        success = upload_clauses_to_pinecone(clauses)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload document to vector database")
        
        print("✅ Document uploaded to vector database")
        
        # Process questions
        async def process_question(question: str, question_index: int) -> str:
            try:
                print(f"🔍 Processing question {question_index}: {question[:50]}...")
                
                # Generate embedding for question
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=question,
                    task_type="retrieval_query"
                )
                query_embedding = result['embedding']
                
                # Search for relevant clauses
                search_results = pinecone_service.query(
                    vector=query_embedding,
                    top_k=8,
                    include_metadata=True,
                    filter={"document": document_name}
                )
                
                if not search_results.matches:
                    return "No relevant information found in the document"
                
                # Convert to Clause objects
                relevant_clauses = []
                for match in search_results.matches:
                    clause = Clause(
                        clause_id=match.id,
                        content=match.metadata.get('content', ''),
                        score=match.score
                    )
                    relevant_clauses.append(clause)
                
                # Generate answer
                answer = await generate_answer(question, relevant_clauses)
                print(f"✅ Question {question_index} processed")
                return answer
                
            except Exception as e:
                print(f"❌ Error processing question {question_index}: {e}")
                return f"Error processing question: {str(e)}"
        
        # Process questions with concurrency limit
        semaphore = asyncio.Semaphore(3)
        
        async def process_with_semaphore(question: str, index: int) -> str:
            async with semaphore:
                return await process_question(question, index + 1)
        
        # Execute all questions
        tasks = [
            process_with_semaphore(question, i) 
            for i, question in enumerate(request.questions)
        ]
        
        answers = await asyncio.gather(*tasks)
        
        print(f"🎉 All {len(request.questions)} questions processed!")
        return HackRXResponse(answers=answers)
                
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download document: {str(e)}")
    except Exception as e:
        print(f"❌ HackRX processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Vercel handler
def handler(request, response):
    """Vercel serverless handler"""
    return app(request, response)