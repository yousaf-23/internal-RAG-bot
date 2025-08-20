"""
Test Document Upload Functionality
-----------------------------------
This script tests the document upload API endpoints.

Usage: python test_document_upload.py
"""

import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

print("="*60)
print("📄 DOCUMENT UPLOAD TEST")
print("="*60)

# Step 1: Get a project to upload to
print("\n1. Getting existing projects...")
response = requests.get(f"{BASE_URL}/api/projects")

if response.status_code == 200:
    projects = response.json()
    
    if projects:
        project = projects[0]  # Use first project
        project_id = project['id']
        print(f"   ✅ Using project: {project['name']} (ID: {project_id})")
    else:
        # Create a project if none exist
        print("   No projects found. Creating test project...")
        
        create_response = requests.post(
            f"{BASE_URL}/api/projects",
            json={"name": "Test Project", "description": "For testing uploads"}
        )
        
        if create_response.status_code == 200:
            project = create_response.json()
            project_id = project['id']
            print(f"   ✅ Created project: {project['name']}")
        else:
            print(f"   ❌ Failed to create project: {create_response.text}")
            exit(1)
else:
    print(f"   ❌ Failed to get projects: {response.text}")
    exit(1)

# Step 2: Create a test file
print("\n2. Creating test file...")
test_file = Path("test_upload.doc")
test_content = """This is a test document for the RAG system.
It contains multiple lines of text.
The document processor should be able to extract this text.
We can then ask questions about this content."""

with open(test_file, "w") as f:
    f.write(test_content)

print(f"   ✅ Created test file: {test_file}")

# Step 3: Upload the file
print(f"\n3. Uploading file to project {project_id}...")

with open(test_file, "rb") as f:
    files = {"file": (test_file.name, f, "text/plain")}
    
    upload_response = requests.post(
        f"{BASE_URL}/api/documents/upload",
        params={"project_id": project_id},
        files=files
    )

if upload_response.status_code == 200:
    document = upload_response.json()
    document_id = document['id']
    
    print(f"   ✅ File uploaded successfully!")
    print(f"   Document ID: {document_id}")
    print(f"   Filename: {document['filename']}")
    print(f"   Status: {document['status']}")
    print(f"   Size: {document['size']} bytes")
else:
    print(f"   ❌ Upload failed: {upload_response.text}")
    test_file.unlink()  # Clean up
    exit(1)

# Step 4: Check document status
print(f"\n4. Checking document status...")
import time

for i in range(5):  # Check status 5 times
    time.sleep(1)  # Wait 1 second
    
    status_response = requests.get(
        f"{BASE_URL}/api/documents/{document_id}/status"
    )
    
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"   Attempt {i+1}: Status = {status['status']}")
        
        if status['status'] == 'ready':
            print(f"   ✅ Document processing complete!")
            break
        elif status['status'] == 'error':
            print(f"   ❌ Processing error: {status.get('error_message')}")
            break
    else:
        print(f"   ❌ Failed to get status: {status_response.text}")

# Step 5: Get all documents for the project
print(f"\n5. Getting all documents for project...")
docs_response = requests.get(
    f"{BASE_URL}/api/documents/project/{project_id}"
)

if docs_response.status_code == 200:
    documents = docs_response.json()
    print(f"   ✅ Found {len(documents)} document(s) in project")
    
    for doc in documents:
        print(f"      - {doc['filename']} ({doc['status']})")
else:
    print(f"   ❌ Failed to get documents: {docs_response.text}")

# Clean up test file
test_file.unlink()
print(f"\n✅ Test file cleaned up")

print("\n" + "="*60)
print("✅ Document upload test complete!")
print("="*60)