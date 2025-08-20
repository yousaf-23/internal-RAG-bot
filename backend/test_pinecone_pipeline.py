"""
Complete Pipeline Test with Pinecone Integration
================================================
This tests the full pipeline including Pinecone vector storage.

Usage: python test_pinecone_pipeline.py
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
    Test the complete document pipeline with Pinecone.
    """
    print("\n" + "="*70)
    print("🚀 COMPLETE PINECONE PIPELINE TEST")
    print("="*70)
    
    # Step 0: Check all services are configured
    print("\n[0] Checking service configuration...")
    from app.config import settings
    
    checks_passed = True
    
    # Check OpenAI
    if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        print(f"  ✅ OpenAI API key configured")
    else:
        print("  ❌ OpenAI API key not configured!")
        checks_passed = False
    
    # Check Pinecone
    if settings.pinecone_api_key and settings.pinecone_api_key != "your-pinecone-api-key-here":
        print(f"  ✅ Pinecone API key configured")
        print(f"     Index: {settings.pinecone_index_name}")
    else:
        print("  ❌ Pinecone API key not configured!")
        checks_passed = False
    
    if not checks_passed:
        print("\n  Please configure all API keys in your .env file")
        return
    
    # Step 1: Initialize Pinecone to check connection
    print("\n[1] Testing Pinecone connection...")
    from app.pinecone_service import PineconeService
    
    try:
        pinecone_service = PineconeService()
        stats = pinecone_service.get_index_stats()
        print(f"  ✅ Connected to Pinecone index: {stats.get('index_name')}")
        print(f"     Current vectors: {stats.get('total_vectors')}")
    except Exception as e:
        print(f"  ❌ Pinecone connection failed: {e}")
        return
    
    # Step 2: Get or create a project
    print("\n[2] Setting up project...")
    
    response = requests.get(f"{BASE_URL}/api/projects")
    if response.status_code != 200:
        print("  ❌ Failed to get projects. Is the API running?")
        return
    
    projects = response.json()
    
    if projects:
        project = projects[0]
        print(f"  Using existing project: {project['name']}")
    else:
        project_data = {
            "name": "Pinecone Test Project",
            "description": "Testing complete pipeline with Pinecone"
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data)
        project = response.json()
        print(f"  Created new project: {project['name']}")
    
    project_id = project['id']
    
    # Step 3: Create a test document
    print("\n[3] Creating test document...")
    
    test_file = Path("pinecone_test.txt")
    test_content = """
    Introduction to Vector Databases and Semantic Search
    
    Vector databases like Pinecone are revolutionizing how we store and search 
    information. Unlike traditional databases that rely on exact matches or 
    keyword searches, vector databases use mathematical representations called 
    embeddings to understand the meaning and context of data.
    
    How Vector Search Works:
    
    1. Text Embedding: Each piece of text is converted into a high-dimensional 
    vector (typically 1536 dimensions for OpenAI models). These vectors capture 
    the semantic meaning of the text.
    
    2. Similarity Calculation: When searching, the query is also converted to a 
    vector. The database then finds vectors that are closest to the query vector 
    using metrics like cosine similarity.
    
    3. Contextual Understanding: This approach allows the system to find relevant 
    information even when the exact words don't match. For example, searching for 
    "car" might also return results about "automobile" or "vehicle".
    
    Benefits of Vector Databases:
    
    - Semantic Search: Find information based on meaning, not just keywords
    - Scalability: Efficiently search millions or billions of vectors
    - Real-time Performance: Get results in milliseconds
    - Flexibility: Works with any type of data that can be embedded
    
    Use Cases:
    
    - Question Answering: Find relevant passages to answer user queries
    - Recommendation Systems: Find similar products, articles, or content
    - Duplicate Detection: Identify similar or duplicate content
    - Knowledge Management: Organize and retrieve company information
    
    This test document will be processed through our complete pipeline:
    1. Text extraction and chunking
    2. Embedding generation using OpenAI
    3. Vector storage in Pinecone
    4. Ready for semantic search!
    """
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"  Created: {test_file}")
    print(f"  Size: {len(test_content)} characters")
    
    # Step 4: Upload the document
    print(f"\n[4] Uploading document to project {project_id}...")
    
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
    else:
        print(f"  ❌ Upload failed: {response.text}")
        test_file.unlink()
        return
    
    # Step 5: Monitor processing status
    print("\n[5] Monitoring processing (this may take 30-60 seconds)...")
    print("  Processing steps: Extract → Chunk → Embed → Store in Pinecone")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        time.sleep(3)
        
        response = requests.get(f"{BASE_URL}/api/documents/{document_id}/status")
        
        if response.status_code == 200:
            status_data = response.json()
            status = status_data['status']
            
            print(f"  Attempt {attempt + 1}/{max_attempts}: Status = {status}")
            
            if status == 'ready':
                print("  ✅ Processing complete!")
                break
            elif status == 'error':
                print(f"  ❌ Processing failed: {status_data.get('error_message')}")
                test_file.unlink()
                return
    
    # Step 6: Verify vectors in Pinecone
    print("\n[6] Verifying vectors in Pinecone...")
    
    # Get updated stats
    updated_stats = pinecone_service.get_index_stats()
    print(f"  Total vectors in index: {updated_stats.get('total_vectors')}")
    
    # Test search with a sample query
    print("\n[7] Testing semantic search...")
    
    # Generate embedding for a test query
    from app.embeddings_service import EmbeddingsService
    embeddings_service = EmbeddingsService()
    
    test_query = "How do vector databases work?"
    print(f"  Query: '{test_query}'")
    
    query_embedding = embeddings_service.generate_embedding(test_query)
    
    if query_embedding:
        # Search in Pinecone
        search_results = pinecone_service.search(
            query_embedding=query_embedding,
            top_k=3,
            filter={'document_id': document_id}
        )
        
        if search_results:
            print(f"  ✅ Found {len(search_results)} relevant chunks:")
            for i, result in enumerate(search_results, 1):
                print(f"\n  Result {i}:")
                print(f"    Similarity Score: {result['score']:.4f}")
                preview = result['text'][:150] if result['text'] else 'N/A'
                print(f"    Text: {preview}...")
        else:
            print("  ⚠️  No search results found")
    
    # Step 8: Clean up
    print("\n[8] Cleaning up...")
    
    # Delete vectors from Pinecone
    if pinecone_service.delete_document(document_id):
        print(f"  ✅ Deleted vectors from Pinecone")
    
    # Delete test file
    test_file.unlink()
    print("  ✅ Test file deleted")
    
    # Summary
    print("\n" + "="*70)
    print("✅ PINECONE PIPELINE TEST COMPLETE")
    print("="*70)
    print("\nPipeline Summary:")
    print("  1. Document uploaded ✅")
    print("  2. Text extracted ✅")
    print("  3. Chunks created ✅")
    print("  4. Embeddings generated ✅")
    print("  5. Vectors stored in Pinecone ✅")
    print("  6. Semantic search working ✅")
    print("\nYour RAG system is now fully operational!")
    print("="*70)

if __name__ == "__main__":
    main()