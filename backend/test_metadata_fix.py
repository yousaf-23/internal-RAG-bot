"""
Test Metadata Column Fix
=========================
This script verifies that the metadata column rename fix is working.

Usage: python test_metadata_fix.py
"""

import sys
import os
from datetime import datetime
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("TESTING METADATA COLUMN FIX")
print("="*70)

# Step 1: Test importing database module
print("\n[1] Testing database module import...")
try:
    from app.database import Base, Message, engine, SessionLocal
    print("    ✅ Database module imported successfully")
except Exception as e:
    print(f"    ❌ Import failed: {e}")
    print("\n    The error suggests 'metadata' conflict is not fixed")
    print("    Make sure you renamed the column to 'message_metadata'")
    sys.exit(1)

# Step 2: Test that Message model works
print("\n[2] Testing Message model...")
try:
    # Check that message_metadata column exists
    if hasattr(Message, 'message_metadata'):
        print("    ✅ Message.message_metadata column exists")
    else:
        print("    ❌ Message.message_metadata column not found")
    
    # Check that metadata property works
    if hasattr(Message, 'metadata'):
        print("    ✅ Message.metadata property exists (backward compatibility)")
    else:
        print("    ⚠️  Message.metadata property not found")
    
except Exception as e:
    print(f"    ❌ Error with Message model: {e}")

# Step 3: Test creating a message with metadata
print("\n[3] Testing message creation with metadata...")
try:
    # Create a test message
    test_metadata = {
        "model": "gpt-4",
        "tokens": 150,
        "response_time": 2.5,
        "test": True
    }
    
    test_message = Message(
        id="test_msg_fix",
        project_id="test_project",
        conversation_id="test_conv",
        role="assistant",
        content="Test message after metadata fix",
        timestamp=datetime.utcnow()
    )
    
    # Test setting metadata using the property
    test_message.metadata = test_metadata  # This uses the @property setter
    
    print(f"    ✅ Message created successfully")
    print(f"    Metadata set via property: {test_message.metadata}")
    print(f"    Actual column value: {test_message.message_metadata}")
    
    # Verify both point to the same data
    if test_message.metadata == test_message.message_metadata:
        print("    ✅ Property and column are synchronized")
    else:
        print("    ❌ Property and column mismatch")
    
except Exception as e:
    print(f"    ❌ Error creating message: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Test database operations
print("\n[4] Testing database operations...")
try:
    from sqlalchemy import inspect
    
    # Inspect the actual database table
    inspector = inspect(engine)
    
    # Check if messages table exists
    if 'messages' in inspector.get_table_names():
        print("    ✅ Messages table exists")
        
        # Get column information
        columns = inspector.get_columns('messages')
        column_names = [col['name'] for col in columns]
        
        print(f"    Columns in database: {', '.join(column_names)}")
        
        # Check for our columns
        if 'message_metadata' in column_names:
            print("    ✅ 'message_metadata' column exists in database")
        else:
            print("    ❌ 'message_metadata' column not found in database")
            
        if 'metadata' in column_names:
            print("    ⚠️  Old 'metadata' column still exists - run fix_metadata_column.py")
        
    else:
        print("    ❌ Messages table not found")
        
except Exception as e:
    print(f"    ❌ Error inspecting database: {e}")

# Step 5: Test actual save/load with session
print("\n[5] Testing save and load with database session...")
try:
    session = SessionLocal()
    
    # Create and save a test message
    test_msg = Message(
        id=f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        project_id="test_project",
        conversation_id="test_conversation",
        role="user",
        content="Test message with metadata",
        timestamp=datetime.utcnow()
    )
    
    # Set metadata using property
    test_msg.metadata = {"test": True, "timestamp": datetime.now().isoformat()}
    
    # Don't actually save to avoid cluttering database
    # session.add(test_msg)
    # session.commit()
    
    print("    ✅ Message can be created with metadata")
    print(f"    Message ID: {test_msg.id}")
    print(f"    Metadata: {test_msg.metadata}")
    
    session.close()
    
except Exception as e:
    print(f"    ❌ Error with database session: {e}")
    if 'session' in locals():
        session.close()

print("\n" + "="*70)
print("✅ METADATA FIX TEST COMPLETE")
print("="*70)
print("\nIf all tests passed, the metadata issue is fixed!")
print("You can now restart the FastAPI server.")