#!/usr/bin/env python3
"""
Vercel-optimized serverless function for Document Query Assistant
"""

import os
import sys
import json
import tempfile
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import requests

# Initialize FastAPI app
app = FastAPI(
    title="Document Query Assistant",
    version="1.0.0",
    description="Serverless document analysis API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Clause(BaseModel):
    clause_id: str
    content: str
    score: float

class HackRXRequest(BaseModel):
    documents: str
    questions: List[str]

class HackRXResponse(BaseModel):
    answers: List[str]

# Configuration from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "document-clauses")

# Global service instances
_gemini_configured = False
_pinecone_service = None

def configure_gemini():
    """Configure Gemini API"""
    global _gemini_configured
    
    if not _gemini_configured and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_configured = True
            print("✅ Gemini configured")
        except Exception as e:
            print(f"❌ Gemini configuration failed: {e}")
            raise

def get_pinecone_service():
    """Get Pinecone service"""
    global _pinecone_service
    
    if _pinecone_service is None and PINECONE_API_KEY:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=PINECONE_API_KEY)
            _pinecone_service = pc.Index(PINECONE_INDEX_NAME)
            print("✅ Pinecone configured")
        except Exception as e:
            print(f"❌ Pinecone configuration failed: {e}")
            _pinecone_service = False
    
    return _pinecone_service if _pinecone_service is not False else None

def extract_text_from_pdf_url(pdf_url: str) -> str:
    """Extract text from PDF URL"""
    try:
        import PyPDF2
        
        # Download PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        text = ""
        
        try:
            # Extract text using PyPDF2
            with open(temp_file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PAGE {page_num + 1} ---\n"
                        text += page_text + "\n"
            
            return text.strip()
        
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        raise

def split_text_into_clauses(text: str, document_name: str) -> List[Dict[str, Any]]:
    """Split text into clauses"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    clauses = []
    for i, paragraph in enumerate(paragraphs):
        if len(paragraph) < 100:
            continue
            
        clause = {
            "id": f"{document_name}_clause_{i+1:03d}",
            "content": paragraph,
            "document": document_name,
            "section": i + 1
        }
        clauses.append(clause)
    
    return clauses

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using Gemini"""
    try:
        import google.generativeai as genai
        
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return None

def upload_to_pinecone(clauses: List[Dict[str, Any]]) -> bool:
    """Upload clauses to Pinecone"""
    pinecone_service = get_pinecone_service()
    
    if not pinecone_service:
        return False
    
    vectors = []
    for clause in clauses:
        embedding = generate_embedding(clause['content'])
        if embedding:
            vectors.append({
                "id": clause['id'],
                "values": embedding,
                "metadata": {
                    "content": clause['content'],
                    "document": clause['document']
                }
            })
    
    if vectors:
        try:
            pinecone_service.upsert(vectors=vectors)
            return True
        except Exception as e:
            print(f"❌ Pinecone upload failed: {e}")
    
    return False

async def generate_answer(question: str, clauses: List[Clause]) -> str:
    """Generate answer using Gemini"""
    try:
        import google.generativeai as genai
        
        context = "\n".join([f"Clause {i+1}: {clause.content}" for i, clause in enumerate(clauses)])
        
        prompt = f"""Based on the policy clauses below, answer the question directly and concisely.

Policy Clauses:
{context}

Question: "{question}"

Provide a direct, factual answer based only on the provided clauses. If information is not available, say so.

Answer:"""

        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        return f"Error processing question: {str(e)}"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Document Query Assistant - Vercel",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Document Query Assistant",
        "platform": "Vercel"
    }

@app.post("/hackrx/run", response_model=HackRXResponse)
async def hackrx_run(request: HackRXRequest):
    """Main HackRX endpoint"""
    try:
        print(f"🚀 Processing {len(request.questions)} questions")
        
        # Configure services
        configure_gemini()
        pinecone_service = get_pinecone_service()
        
        if not pinecone_service:
            raise HTTPException(status_code=503, detail="Pinecone service not available")
        
        document_name = "hackrx_policy"
        
        # Extract text from PDF
        print("📄 Extracting text from PDF...")
        text = extract_text_from_pdf_url(request.documents)
        
        # Split into clauses
        print("📝 Splitting into clauses...")
        clauses = split_text_into_clauses(text, document_name)
        
        # Upload to Pinecone
        print("🔄 Uploading to Pinecone...")
        success = upload_to_pinecone(clauses)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to upload to vector database")
        
        # Process questions
        answers = []
        
        for i, question in enumerate(request.questions):
            try:
                print(f"🔍 Processing question {i+1}/{len(request.questions)}")
                
                # Generate embedding for question
                import google.generativeai as genai
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=question,
                    task_type="retrieval_query"
                )
                query_embedding = result['embedding']
                
                # Search Pinecone
                search_results = pinecone_service.query(
                    vector=query_embedding,
                    top_k=5,
                    include_metadata=True,
                    filter={"document": document_name}
                )
                
                if search_results.matches:
                    # Convert to Clause objects
                    relevant_clauses = [
                        Clause(
                            clause_id=match.id,
                            content=match.metadata.get('content', ''),
                            score=match.score
                        )
                        for match in search_results.matches
                    ]
                    
                    # Generate answer
                    answer = await generate_answer(question, relevant_clauses)
                    answers.append(answer)
                else:
                    answers.append("No relevant information found in the document")
                    
            except Exception as e:
                print(f"❌ Error processing question {i+1}: {e}")
                answers.append(f"Error processing question: {str(e)}")
        
        print(f"✅ Completed processing {len(answers)} questions")
        return HackRXResponse(answers=answers)
        
    except Exception as e:
        print(f"❌ HackRX processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Vercel handler
from mangum import Mangum
handler = Mangum(app, lifespan="off")
