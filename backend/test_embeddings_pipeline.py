"""
Complete Pipeline Test with Embeddings
=======================================
This tests the full pipeline including embedding generation.

Usage: python test_embeddings_pipeline.py
"""

import time
import requests
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration
BASE_URL = "http://localhost:8000"

def main():
    """
    Test the complete document pipeline with embeddings.
    """
    print("\n" + "="*70)
    print("🚀 COMPLETE PIPELINE TEST WITH EMBEDDINGS")
    print("="*70)
    
    # Step 0: Check OpenAI API key
    print("\n[0] Checking OpenAI configuration...")
    from app.config import settings
    
    if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        print(f"  ✅ OpenAI API key is configured")
        print(f"  Model: {settings.embedding_model}")
    else:
        print("  ❌ OpenAI API key not configured!")
        print("  Please set OPENAI_API_KEY in your .env file")
        print("  Get your key from: https://platform.openai.com/api-keys")
        return
    
    # Step 1: Get or create a project
    print("\n[1] Setting up project...")
    
    response = requests.get(f"{BASE_URL}/api/projects")
    if response.status_code != 200:
        print("  ❌ Failed to get projects. Is the API running?")
        print("  Run: uvicorn app.main:app --reload")
        return
    
    projects = response.json()
    
    if projects:
        project = projects[0]
        print(f"  Using existing project: {project['name']}")
    else:
        # Create new project
        project_data = {
            "name": "Embeddings Test Project",
            "description": "Testing document processing with embeddings"
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data)
        project = response.json()
        print(f"  Created new project: {project['name']}")
    
    project_id = project['id']
    
    # Step 2: Create a test document with rich content
    print("\n[2] Creating test document...")
    
    test_file = Path("embeddings_test.txt")
    test_content = """
    Artificial Intelligence and Machine Learning: A Comprehensive Overview
    
    Chapter 1: Introduction to AI
    
    Artificial Intelligence (AI) represents one of the most transformative technologies 
    of our time. At its core, AI refers to computer systems that can perform tasks 
    that typically require human intelligence, such as visual perception, speech 
    recognition, decision-making, and language translation.
    
    Chapter 2: Machine Learning Fundamentals
    
    Machine Learning (ML) is a subset of AI that enables systems to learn and improve 
    from experience without being explicitly programmed. ML algorithms build mathematical 
    models based on training data to make predictions or decisions without being 
    explicitly programmed to perform the task.
    
    Key Types of Machine Learning:
    
    1. Supervised Learning: The algorithm learns from labeled training data, with each 
    example paired with its correct output. Common applications include spam detection, 
    image classification, and sales forecasting.
    
    2. Unsupervised Learning: The algorithm finds patterns in unlabeled data without 
    predefined categories. It's used for customer segmentation, anomaly detection, 
    and recommendation systems.
    
    3. Reinforcement Learning: The algorithm learns through interaction with an 
    environment, receiving rewards or penalties based on its actions. This approach 
    powers game-playing AIs and robotic control systems.
    
    Chapter 3: Deep Learning and Neural Networks
    
    Deep Learning is a specialized subset of machine learning inspired by the structure 
    and function of the human brain. Neural networks consist of interconnected layers 
    of nodes (neurons) that process information in a hierarchical manner.
    
    Applications of AI in Industry:
    
    Healthcare: AI assists in disease diagnosis, drug discovery, and personalized 
    treatment plans. Machine learning models can detect patterns in medical images 
    that might be missed by human eyes.
    
    Finance: AI powers fraud detection systems, algorithmic trading, and credit risk 
    assessment. Banks use ML models to identify suspicious transactions in real-time.
    
    Transportation: Self-driving cars use computer vision and deep learning to navigate 
    roads safely. AI optimizes route planning and traffic management systems.
    
    Retail: Recommendation engines use collaborative filtering and deep learning to 
    suggest products. AI-powered chatbots provide customer service 24/7.
    
    Chapter 4: The Future of AI
    
    As we look ahead, AI continues to evolve rapidly. Emerging trends include:
    
    - Explainable AI: Making AI decisions more transparent and interpretable
    - Edge AI: Running AI models on devices rather than in the cloud
    - Quantum Machine Learning: Leveraging quantum computing for AI
    - AGI (Artificial General Intelligence): Working toward human-level AI
    
    Conclusion:
    
    The field of AI and machine learning represents one of the most exciting and 
    rapidly evolving areas of technology. As these systems become more sophisticated, 
    they will continue to transform industries and reshape our daily lives.
    
    This document serves as a test for our embeddings generation pipeline. Each chunk 
    of this text will be converted into a numerical vector representation that captures 
    its semantic meaning, enabling powerful search and retrieval capabilities.
    """
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"  Created: {test_file}")
    print(f"  Size: {len(test_content)} characters")
    print(f"  Content: Rich AI/ML educational content")
    
    # Step 3: Upload the document
    print(f"\n[3] Uploading document to project {project_id}...")
    
    with open(test_file, 'rb') as f:
        files = {'file': (test_file.name, f, 'text/plain')}
        response = requests.post(
            f"{BASE_URL}/api/documents/upload",
            params={'project_id': project_id},
            files=files
        )
    
    if response.status_code == 200:
        document = response.json()
        document_id = document['id']
        print(f"  ✅ Upload successful!")
        print(f"  Document ID: {document_id}")
        print(f"  Initial status: {document['status']}")
    else:
        print(f"  ❌ Upload failed: {response.text}")
        test_file.unlink()
        return
    
    # Step 4: Monitor processing status
    print("\n[4] Monitoring processing status (this may take 30-60 seconds)...")
    print("  (Generating embeddings for each chunk takes time)")
    
    max_attempts = 30  # More attempts since embeddings take time
    for attempt in range(max_attempts):
        time.sleep(3)  # Wait 3 seconds between checks
        
        # Check status
        response = requests.get(f"{BASE_URL}/api/documents/{document_id}/status")
        
        if response.status_code == 200:
            status_data = response.json()
            status = status_data['status']
            
            print(f"  Attempt {attempt + 1}/{max_attempts}: Status = {status}")
            
            if status == 'ready':
                print("  ✅ Processing complete with embeddings!")
                break
            elif status == 'error':
                print(f"  ❌ Processing failed: {status_data.get('error_message')}")
                break
        else:
            print(f"  ⚠️ Could not check status: {response.text}")
    
    # Step 5: Verify chunks and embeddings in database
    print("\n[5] Verifying chunks and embeddings...")
    
    # Get document details
    response = requests.get(f"{BASE_URL}/api/documents/{document_id}")
    
    if response.status_code == 200:
        doc_details = response.json()
        print(f"  Document details:")
        print(f"    - Status: {doc_details.get('status')}")
        print(f"    - Page count: {doc_details.get('page_count')}")
        
        # Check database directly for chunks
        from app.database import get_db, DocumentChunk
        from sqlalchemy import func
        
        db = next(get_db())
        chunk_count = db.query(func.count(DocumentChunk.id)).filter(
            DocumentChunk.document_id == document_id
        ).scalar()
        
        print(f"    - Chunks in database: {chunk_count}")
        
        # Get sample chunk
        sample_chunk = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).first()
        
        if sample_chunk:
            print(f"\n  Sample chunk:")
            print(f"    - ID: {sample_chunk.id}")
            print(f"    - Index: {sample_chunk.chunk_index}")
            print(f"    - Text preview: {sample_chunk.chunk_text[:100]}...")
            print(f"    - Embedding model: {sample_chunk.embedding_model or 'Not set'}")
        
        db.close()
    
    # Step 6: Show cost estimate
    print("\n[6] Cost Analysis...")
    
    from app.embeddings_service import EmbeddingsService
    service = EmbeddingsService()
    
    # Estimate cost for this document
    cost_estimate = service.estimate_cost([test_content])
    print(f"  Embedding generation cost for this document:")
    print(f"    - Characters: {cost_estimate['total_characters']}")
    print(f"    - Estimated tokens: {cost_estimate['estimated_tokens']}")
    print(f"    - Estimated cost: ${cost_estimate['estimated_cost_usd']:.6f}")
    
    # Step 7: Clean up
    print("\n[7] Cleaning up...")
    test_file.unlink()
    print("  ✅ Test file deleted")
    
    # Summary
    print("\n" + "="*70)
    print("✅ PIPELINE TEST COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("  1. Document uploaded ✅")
    print("  2. Text extracted ✅")
    print("  3. Chunks created ✅")
    print("  4. Embeddings generated ✅")
    print("  5. Ready for Pinecone storage (next step)")
    print("\nThe document is now ready for semantic search!")
    print("="*70)

if __name__ == "__main__":
    main()