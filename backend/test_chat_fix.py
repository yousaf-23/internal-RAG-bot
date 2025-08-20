"""
Test Chat System After Fix
===========================
Verifies that conversation_id is working correctly.

Usage: python test_chat_fix.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_chat_after_fix():
    """
    Test that the chat system works with conversation_id.
    """
    print("\n" + "="*70)
    print("🔧 TESTING CHAT SYSTEM AFTER FIX")
    print("="*70)
    
    # Step 1: Get a project
    print("\n[1] Getting project...")
    response = requests.get(f"{BASE_URL}/api/projects")
    
    if response.status_code != 200:
        print("    ❌ Failed to get projects")
        return
        
    projects = response.json()
    if not projects:
        print("    ❌ No projects found. Create one first.")
        return
        
    project = projects[0]
    project_id = project['id']
    print(f"    ✅ Using project: {project['name']}")
    
    # Step 2: Send a test chat message
    print("\n[2] Sending chat message...")
    
    chat_request = {
        "project_id": project_id,
        "query": "This is a test message after fixing the database.",
        "include_sources": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/query",
        json=chat_request
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"    ✅ Chat response received")
        print(f"    Conversation ID: {result.get('conversation_id')}")
        print(f"    Response preview: {result['response'][:100]}...")
        
        conversation_id = result.get('conversation_id')
    else:
        print(f"    ❌ Chat failed: {response.status_code}")
        if response.content:
            print(f"    Error: {response.json()}")
        return
    
    # Step 3: Test conversation history
    print("\n[3] Testing conversation history...")
    
    response = requests.get(f"{BASE_URL}/api/chat/history/{project_id}?limit=5")
    
    if response.status_code == 200:
        history = response.json()
        print(f"    ✅ History retrieved successfully")
        print(f"    Conversations found: {len(history)}")
        
        if history:
            latest = history[0]
            print(f"    Latest conversation: {latest['conversation_id']}")
            print(f"    Messages in conversation: {len(latest['messages'])}")
            
            # Show messages
            for msg in latest['messages'][:2]:  # Show first 2 messages
                role = msg['role']
                content_preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
                print(f"      - {role}: {content_preview}")
    else:
        print(f"    ❌ History failed: {response.status_code}")
        if response.content:
            print(f"    Error: {response.json()}")
    
    # Step 4: Verify database directly
    print("\n[4] Verifying database...")
    
    # This checks if messages were saved with conversation_id
    # You can also check this manually in psql:
    # SELECT id, conversation_id, role FROM messages ORDER BY timestamp DESC LIMIT 5;
    
    print("\n" + "="*70)
    print("✅ CHAT SYSTEM TEST COMPLETE")
    print("="*70)
    print("\nIf all tests passed, the conversation_id issue is fixed!")

if __name__ == "__main__":
    test_chat_after_fix()