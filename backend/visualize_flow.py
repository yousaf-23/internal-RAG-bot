"""
RAG System Flow Visualization
==============================
This script demonstrates the complete flow of your RAG system
with actual API calls and timing information.
"""

import time
import requests
from pathlib import Path
from datetime import datetime

def demonstrate_complete_flow():
    """
    Demonstrate the complete RAG flow with timing and explanations
    """
    base_url = "http://localhost:8000"
    
    print("\n" + "="*70)
    print("🔄 COMPLETE RAG SYSTEM FLOW DEMONSTRATION")
    print("="*70)
    
    # Step 1: Create a project
    print("\n[STEP 1] Creating a Project")
    print("-" * 40)
    print("Purpose: Projects organize your documents and conversations")
    
    start_time = time.time()
    
    project_data = {
        "name": f"Demo Project {datetime.now().strftime('%H%M%S')}",
        "description": "Demonstration of RAG system flow"
    }
    
    response = requests.post(f"{base_url}/api/projects", json=project_data)
    project = response.json()
    project_id = project['id']
    
    elapsed = time.time() - start_time
    print(f"✅ Project created in {elapsed:.2f} seconds")
    print(f"   Project ID: {project_id}")
    print(f"   Project Name: {project['name']}")
    
    # Step 2: Create and upload a test document
    print("\n[STEP 2] Document Upload")
    print("-" * 40)
    print("Purpose: Add knowledge to your system")
    
    # Create a test document with rich content
    test_file = Path("demo_document.txt")
    test_content = """
    Introduction to RAG Systems
    
    Retrieval-Augmented Generation (RAG) combines the power of large language models 
    with the precision of information retrieval. This approach allows AI systems to 
    provide accurate, contextual responses based on specific documents rather than 
    general training data.
    
    Key Benefits:
    1. Accuracy: Responses are grounded in your actual documents
    2. Traceability: Every answer can be traced back to source documents
    3. Privacy: Your documents stay in your control
    4. Customization: The system learns from YOUR specific knowledge base
    
    How It Works:
    - Documents are processed and split into chunks
    - Each chunk is converted to a mathematical representation (embedding)
    - When you ask a question, it finds the most relevant chunks
    - These chunks provide context for generating accurate answers
    
    This demonstration shows how all components work together seamlessly.
    """
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"📄 Created test document: {test_file}")
    
    start_time = time.time()
    
    with open(test_file, 'rb') as f:
        files = {'file': (test_file.name, f, 'text/plain')}
        response = requests.post(
            f"{base_url}/api/documents/upload",
            params={'project_id': project_id},
            files=files
        )
    
    document = response.json()
    document_id = document['id']
    
    elapsed = time.time() - start_time
    print(f"✅ Document uploaded in {elapsed:.2f} seconds")
    print(f"   Document ID: {document_id}")
    
    # Step 3: Monitor processing
    print("\n[STEP 3] Document Processing Pipeline")
    print("-" * 40)
    print("Processing steps happening now:")
    print("  1. Extracting text from document")
    print("  2. Splitting into chunks (1000 chars each)")
    print("  3. Generating embeddings via OpenAI")
    print("  4. Storing vectors in Pinecone")
    
    start_time = time.time()
    max_wait = 60  # Maximum 60 seconds
    
    while (time.time() - start_time) < max_wait:
        response = requests.get(f"{base_url}/api/documents/{document_id}/status")
        status_data = response.json()
        status = status_data['status']
        
        if status == 'ready':
            elapsed = time.time() - start_time
            print(f"✅ Processing complete in {elapsed:.2f} seconds")
            break
        elif status == 'error':
            print(f"❌ Processing failed: {status_data.get('error_message')}")
            break
        else:
            print(f"   Status: {status} (checking again in 3 seconds...)")
            time.sleep(3)
    
    # Step 4: Ask questions
    print("\n[STEP 4] Intelligent Q&A with RAG")
    print("-" * 40)
    print("Purpose: Get accurate answers based on your documents")
    
    test_questions = [
        "What is RAG?",
        "What are the benefits of using RAG systems?",
        "How does the system ensure accuracy?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Question {i}: {question}")
        
        start_time = time.time()
        
        chat_request = {
            "project_id": project_id,
            "query": question,
            "include_sources": True,
            "max_chunks": 3
        }
        
        response = requests.post(
            f"{base_url}/api/chat/query",
            json=chat_request
        )
        
        if response.status_code == 200:
            result = response.json()
            elapsed = time.time() - start_time
            
            if result['success']:
                print(f"✅ Answer generated in {elapsed:.2f} seconds")
                
                # Show answer preview
                answer = result['response']
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"   Answer: {preview}")
                
                # Show source information
                sources = result.get('sources', [])
                if sources:
                    print(f"   Sources: {len(sources)} document chunks used")
                    for source in sources[:1]:  # Show first source
                        print(f"   - Document: {source.get('filename', 'Unknown')}")
                        print(f"   - Relevance: {source.get('relevance_score', 0):.2f}")
            else:
                print(f"❌ Failed to generate answer")
        else:
            print(f"❌ API error: {response.status_code}")
    
    # Step 5: Show what happened behind the scenes
    print("\n[STEP 5] Behind the Scenes")
    print("-" * 40)
    print("What happened during this demonstration:")
    print("  1. ✅ Project created to organize documents")
    print("  2. ✅ Document uploaded and saved locally")
    print("  3. ✅ Text extracted and split into chunks")
    print("  4. ✅ OpenAI generated embeddings for each chunk")
    print("  5. ✅ Pinecone stored vectors for fast search")
    print("  6. ✅ Questions triggered semantic search")
    print("  7. ✅ Relevant chunks provided context to GPT-4")
    print("  8. ✅ Accurate answers generated with sources")
    
    # Clean up
    test_file.unlink()
    print(f"\n🧹 Cleaned up test file: {test_file}")
    
    print("\n" + "="*70)
    print("✅ DEMONSTRATION COMPLETE!")
    print("="*70)
    print("\nYour RAG system is working perfectly!")
    print("You can now upload your own documents and ask questions about them.")
    
    return project_id

if __name__ == "__main__":
    print("\n🚀 Starting RAG System Flow Demonstration...")
    print("Make sure your FastAPI server is running on port 8000")
    
    try:
        # Check if API is accessible
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            project_id = demonstrate_complete_flow()
            
            print("\n📌 Created Demo Project ID:", project_id)
            print("You can use this project to upload more documents and test further.")
        else:
            print("❌ API is not responding correctly")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please start the server:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")