"""
Test PostgreSQL connection and database operations.
Run this to verify PostgreSQL is properly configured.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, test_connection, get_db, Project, Document
from app.config import settings
import uuid
from datetime import datetime

print("\n" + "="*60)
print("🐘 PostgreSQL Connection and Operations Test")
print("="*60)

# Step 1: Test connection
print("\n1. Testing database connection...")
if test_connection():
    print("   ✅ Connection successful")
else:
    print("   ❌ Connection failed - check PostgreSQL installation and credentials")
    sys.exit(1)

# Step 2: Initialize database tables
print("\n2. Initializing database tables...")
try:
    init_db()
    print("   ✅ Tables created/verified")
except Exception as e:
    print(f"   ❌ Failed to create tables: {e}")
    sys.exit(1)

# Step 3: Test CRUD operations
print("\n3. Testing CRUD operations...")
try:
    # Get a database session
    db = next(get_db())
    
    # Create a test project
    test_project = Project(
        id=str(uuid.uuid4()),
        name="Test Project",
        description="Testing PostgreSQL operations",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add to session and commit
    db.add(test_project)
    db.commit()
    print(f"   ✅ Created project: {test_project.name}")
    
    # Query the project
    queried_project = db.query(Project).filter_by(name="Test Project").first()
    if queried_project:
        print(f"   ✅ Queried project: {queried_project.name}")
    
    # Create a test document
    test_document = Document(
        id=str(uuid.uuid4()),
        project_id=test_project.id,
        filename="test.pdf",
        file_type="pdf",
        size=1024,
        status="ready",
        uploaded_at=datetime.utcnow()
    )
    
    db.add(test_document)
    db.commit()
    print(f"   ✅ Created document: {test_document.filename}")
    
    # Count documents for project
    doc_count = db.query(Document).filter_by(project_id=test_project.id).count()
    print(f"   ✅ Document count for project: {doc_count}")
    
    # Clean up - delete test data
    db.delete(test_project)  # This will cascade delete the document
    db.commit()
    print("   ✅ Cleaned up test data")
    
    # Close session
    db.close()
    
except Exception as e:
    print(f"   ❌ CRUD operations failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("🎉 All PostgreSQL tests passed successfully!")
print("="*60)
print("\nYour PostgreSQL setup is working correctly!")
print("You can now proceed with building the FastAPI application.")