"""
Database Migration: Add conversation_id to messages table
=========================================================
This script adds the conversation_id column to the existing messages table.

Usage: python migrate_add_conversation_id.py

Author: RAG System Development
Date: 2024
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.exc import OperationalError, ProgrammingError
from app.config import settings

def add_conversation_id_column():
    """
    Add conversation_id column to messages table if it doesn't exist.
    """
    print("\n" + "="*70)
    print("DATABASE MIGRATION: Adding conversation_id to messages table")
    print("="*70)
    
    # Create database connection
    print(f"\n[1] Connecting to database...")
    print(f"    Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT 1"))
            print(f"    ✅ Connected successfully")
            
            # Check if column already exists
            print(f"\n[2] Checking if conversation_id column exists...")
            
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'messages' 
                AND column_name = 'conversation_id'
            """)
            
            result = conn.execute(check_query)
            column_exists = result.fetchone() is not None
            
            if column_exists:
                print(f"    ✅ Column 'conversation_id' already exists - no migration needed")
                
                # Show current messages table structure
                print(f"\n[3] Current messages table structure:")
                structure_query = text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'messages'
                    ORDER BY ordinal_position
                """)
                
                result = conn.execute(structure_query)
                columns = result.fetchall()
                
                print(f"    Columns in messages table:")
                for col_name, data_type, nullable in columns:
                    null_info = "NULL" if nullable == 'YES' else "NOT NULL"
                    print(f"      - {col_name}: {data_type} ({null_info})")
                
            else:
                print(f"    ⚠️  Column 'conversation_id' does not exist")
                print(f"\n[3] Adding conversation_id column...")
                
                # Add the column
                alter_query = text("""
                    ALTER TABLE messages 
                    ADD COLUMN conversation_id VARCHAR NULL
                """)
                
                conn.execute(alter_query)
                conn.commit()
                print(f"    ✅ Column added successfully")
                
                # Add index for better performance
                print(f"\n[4] Adding index on conversation_id...")
                index_query = text("""
                    CREATE INDEX IF NOT EXISTS ix_messages_conversation_id 
                    ON messages(conversation_id)
                """)
                
                conn.execute(index_query)
                conn.commit()
                print(f"    ✅ Index added successfully")
                
                # Verify the column was added
                print(f"\n[5] Verifying migration...")
                result = conn.execute(check_query)
                if result.fetchone():
                    print(f"    ✅ Migration completed successfully!")
                else:
                    print(f"    ❌ Migration verification failed")
                    return False
            
            # Show statistics
            print(f"\n[6] Database statistics:")
            
            # Count messages
            count_query = text("SELECT COUNT(*) FROM messages")
            result = conn.execute(count_query)
            message_count = result.fetchone()[0]
            print(f"    Total messages: {message_count}")
            
            # Count conversations (distinct conversation_ids)
            conv_query = text("""
                SELECT COUNT(DISTINCT conversation_id) 
                FROM messages 
                WHERE conversation_id IS NOT NULL
            """)
            result = conn.execute(conv_query)
            conv_count = result.fetchone()[0]
            print(f"    Total conversations: {conv_count}")
            
            print("\n" + "="*70)
            print("✅ MIGRATION COMPLETE")
            print("="*70)
            return True
            
    except OperationalError as e:
        print(f"\n❌ Database connection error: {e}")
        print("\nDebugging steps:")
        print("1. Check PostgreSQL is running: Get-Service -Name 'postgresql*'")
        print("2. Verify database exists: psql -U postgres -c '\\l'")
        print("3. Check connection string in .env file")
        return False
        
    except ProgrammingError as e:
        print(f"\n❌ SQL error: {e}")
        print("\nThis might mean the table doesn't exist or has issues.")
        print("Try running: python init_database.py")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_existing_messages():
    """
    Optional: Update existing messages with conversation IDs.
    Groups messages by timestamp proximity.
    """
    print("\n[Optional] Updating existing messages with conversation IDs...")
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Get messages without conversation_id
            query = text("""
                SELECT id, project_id, timestamp 
                FROM messages 
                WHERE conversation_id IS NULL
                ORDER BY project_id, timestamp
            """)
            
            result = conn.execute(query)
            messages = result.fetchall()
            
            if messages:
                print(f"    Found {len(messages)} messages without conversation_id")
                
                # Group messages by project and time proximity (within 1 hour)
                from datetime import timedelta
                
                conversations_created = 0
                current_project = None
                current_conv_id = None
                last_timestamp = None
                
                for msg_id, project_id, timestamp in messages:
                    # Check if we need a new conversation
                    if (current_project != project_id or 
                        last_timestamp is None or 
                        (timestamp - last_timestamp) > timedelta(hours=1)):
                        
                        # Create new conversation ID
                        current_conv_id = f"conv_legacy_{conversations_created:04d}"
                        current_project = project_id
                        conversations_created += 1
                    
                    # Update message with conversation_id
                    update_query = text("""
                        UPDATE messages 
                        SET conversation_id = :conv_id 
                        WHERE id = :msg_id
                    """)
                    
                    conn.execute(update_query, {
                        'conv_id': current_conv_id,
                        'msg_id': msg_id
                    })
                    
                    last_timestamp = timestamp
                
                conn.commit()
                print(f"    ✅ Updated {len(messages)} messages")
                print(f"    ✅ Created {conversations_created} conversation groups")
            else:
                print(f"    No messages need updating")
                
    except Exception as e:
        print(f"    ⚠️  Could not update existing messages: {e}")
        print(f"    This is optional - new messages will have conversation_id")

if __name__ == "__main__":
    # Run the migration
    success = add_conversation_id_column()
    
    if success:
        # Optionally update existing messages
        response = input("\nDo you want to update existing messages with conversation IDs? (y/n): ")
        if response.lower() == 'y':
            update_existing_messages()
        
        print("\n✅ Migration completed successfully!")
        print("You can now restart the FastAPI server.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")