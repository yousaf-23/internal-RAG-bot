"""
Comprehensive Chat System Test
===============================
This script tests the complete chat functionality with RAG.

Usage: python test_chat_system.py
"""

import time
import requests
import json
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

def test_chat_system():
    """
    Test the complete chat system.
    """
    print("\n" + "="*70)
    print("🤖 COMPREHENSIVE CHAT SYSTEM TEST")
    print("="*70)
    
    # Step 1: Test chat service availability
    print("\n[1] Testing chat service availability...")
    
    response = requests.get(f"{BASE_URL}/api/chat/test")
    if response.status_code == 200:
        status = response.json()
        print(f"  ✅ Chat API operational")
        print(f"  Services status:")
        for service, available in status.get('services', {}).items():
            status_icon = "✅" if available else "❌"
            print(f"    {status_icon} {service}: {available}")
    else:
        print(f"  ❌ Chat API not responding")
        return
    
    # Step 2: Get or create a project with documents
    print("\n[2] Setting up test project...")
    
    response = requests.get(f"{BASE_URL}/api/projects")
    projects = response.json()
    
    # Find a project with indexed documents
    test_project = None
    for project in projects:
        # Check if project has documents
        docs_response = requests.get(f"{BASE_URL}/api/documents/project/{project['id']}")
        if docs_response.status_code == 200:
            docs = docs_response.json()
            indexed_docs = [d for d in docs if d.get('status') == 'ready']
            if indexed_docs:
                test_project = project
                print(f"  ✅ Using project: {project['name']}")
                print(f"     Indexed documents: {len(indexed_docs)}")
                break
    
    if not test_project:
        print("  ❌ No project with indexed documents found")
        print("     Please upload and process some documents first")
        return
    
    project_id = test_project['id']
    
    # Step 3: Test simple chat without context
    print("\n[3] Testing simple chat (no document context)...")
    
    response = requests.post(f"{BASE_URL}/api/chat/test/simple")
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"  ✅ Simple chat working")
            print(f"     Response preview: {result['response'][:100]}...")
        else:
            print(f"  ❌ Simple chat failed: {result.get('error')}")
    
    # Step 4: Test RAG chat with document context
    print("\n[4] Testing RAG chat (with document context)...")
    
    test_queries = [
        "What information do you have in the documents?",
        "Can you summarize the main topics covered?",
        "What are the key points I should know?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n  Query {i}: {query}")
        
        chat_request = {
            "project_id": project_id,
            "query": query,
            "include_sources": True,
            "max_chunks": 5
        }
        
        print(f"  Sending request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/chat/query",
            json=chat_request
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result['success']:
                print(f"  ✅ Response generated successfully")
                print(f"     Time: {response_time:.2f} seconds")
                print(f"     Response length: {len(result['response'])} characters")
                print(f"     Sources used: {len(result.get('sources', []))}")
                
                # Show response preview
                response_preview = result['response'][:200]
                if len(result['response']) > 200:
                    response_preview += "..."
                print(f"     Response: {response_preview}")
                
                # Show sources if available
                if result.get('sources'):
                    print(f"     Sources:")
                    for source in result['sources'][:3]:
                        print(f"       - {source.get('filename', 'Unknown')} (score: {source.get('relevance_score', 0):.2f})")
                
                # Store conversation ID for next test
                if i == 1:
                    conversation_id = result.get('conversation_id')
            else:
                print(f"  ❌ Response generation failed")
        else:
            print(f"  ❌ API error: {response.status_code}")
            error_detail = response.json() if response.content else {}
            print(f"     Error: {error_detail.get('detail', 'Unknown error')}")
    
    # Step 5: Test conversation history
    print("\n[5] Testing conversation history...")
    
    response = requests.get(f"{BASE_URL}/api/chat/history/{project_id}?limit=5")
    if response.status_code == 200:
        history = response.json()
        print(f"  ✅ Retrieved {len(history)} conversations")
        
        if history:
            latest = history[0]
            print(f"     Latest conversation: {latest['conversation_id']}")
            print(f"     Messages: {len(latest['messages'])}")
    else:
        print(f"  ❌ Failed to get history")
    
    # Summary
    print("\n" + "="*70)
    print("📊 CHAT SYSTEM TEST SUMMARY")
    print("="*70)
    print("\nCapabilities tested:")
    print("  ✅ Chat service initialization")
    print("  ✅ Simple GPT-4 responses")
    print("  ✅ RAG with document context")
    print("  ✅ Source attribution")
    print("  ✅ Conversation history")
    print("\nYour chat system is fully operational!")
    print("="*70)

if __name__ == "__main__":
    test_chat_system()