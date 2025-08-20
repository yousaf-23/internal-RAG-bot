"""
Fix Metadata Column Name Conflict
==================================
This script renames the 'metadata' column to 'message_metadata' in the messages table
to avoid SQLAlchemy's reserved word conflict.

Usage: python fix_metadata_column.py

Author: RAG System Development
Date: 2024
"""

import sys
import os
from datetime import datetime

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from app.config import settings

def fix_metadata_column():
    """
    Rename metadata column to message_metadata if it exists,
    or create message_metadata if neither exists.
    """
    print("\n" + "="*70)
    print("DATABASE FIX: Renaming metadata column to avoid conflict")
    print("="*70)
    
    # Create database connection
    print(f"\n[1] Connecting to database...")
    
    try:
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT 1"))
            print(f"    ✅ Connected successfully")
            
            # Step 1: Check what columns exist in messages table
            print(f"\n[2] Checking current messages table structure...")
            
            check_query = text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'messages'
                ORDER BY ordinal_position
            """)
            
            result = conn.execute(check_query)
            columns = result.fetchall()
            
            if not columns:
                print(f"    ⚠️  Messages table doesn't exist")
                print(f"    Run: python init_database.py")
                return False
            
            # Print current columns
            print(f"    Current columns in messages table:")
            column_names = []
            for col_name, data_type in columns:
                print(f"      - {col_name}: {data_type}")
                column_names.append(col_name)
            
            # Step 2: Determine what action to take
            has_metadata = 'metadata' in column_names
            has_message_metadata = 'message_metadata' in column_names
            
            print(f"\n[3] Determining required action...")
            
            if has_message_metadata:
                print(f"    ✅ Column 'message_metadata' already exists - no action needed")
                
                # If old metadata column still exists, we can drop it
                if has_metadata:
                    print(f"    ⚠️  Old 'metadata' column still exists")
                    response = input("    Do you want to drop the old 'metadata' column? (y/n): ")
                    
                    if response.lower() == 'y':
                        drop_query = text("ALTER TABLE messages DROP COLUMN metadata")
                        conn.execute(drop_query)
                        conn.commit()
                        print(f"    ✅ Old 'metadata' column dropped")
                
            elif has_metadata:
                # Rename metadata to message_metadata
                print(f"    ⚠️  Found 'metadata' column - renaming to 'message_metadata'")
                
                print(f"\n[4] Renaming column...")
                rename_query = text("""
                    ALTER TABLE messages 
                    RENAME COLUMN metadata TO message_metadata
                """)
                
                conn.execute(rename_query)
                conn.commit()
                print(f"    ✅ Column renamed successfully")
                
            else:
                # Neither column exists - create message_metadata
                print(f"    ⚠️  No metadata column found - creating 'message_metadata'")
                
                print(f"\n[4] Adding message_metadata column...")
                add_query = text("""
                    ALTER TABLE messages 
                    ADD COLUMN message_metadata JSON NULL
                """)
                
                conn.execute(add_query)
                conn.commit()
                print(f"    ✅ Column added successfully")
            
            # Step 3: Verify final structure
            print(f"\n[5] Verifying final table structure...")
            
            result = conn.execute(check_query)
            final_columns = result.fetchall()
            
            print(f"    Final columns in messages table:")
            for col_name, data_type in final_columns:
                if col_name in ['message_metadata', 'metadata']:
                    print(f"      - {col_name}: {data_type} ⭐")  # Highlight metadata columns
                else:
                    print(f"      - {col_name}: {data_type}")
            
            # Verify message_metadata exists
            final_column_names = [col[0] for col in final_columns]
            if 'message_metadata' in final_column_names:
                print(f"\n    ✅ Success! 'message_metadata' column is ready")
            else:
                print(f"\n    ❌ Failed to create/rename column")
                return False
            
            # Show statistics
            print(f"\n[6] Database statistics:")
            
            # Count messages
            count_query = text("SELECT COUNT(*) FROM messages")
            result = conn.execute(count_query)
            message_count = result.fetchone()[0]
            print(f"    Total messages: {message_count}")
            
            # Count messages with metadata
            metadata_query = text("""
                SELECT COUNT(*) 
                FROM messages 
                WHERE message_metadata IS NOT NULL
            """)
            result = conn.execute(metadata_query)
            metadata_count = result.fetchone()[0]
            print(f"    Messages with metadata: {metadata_count}")
            
            print("\n" + "="*70)
            print("✅ DATABASE FIX COMPLETE")
            print("="*70)
            return True
            
    except OperationalError as e:
        print(f"\n❌ Database connection error: {e}")
        print("\nDebugging steps:")
        print("1. Check PostgreSQL is running:")
        print("   Get-Service -Name 'postgresql*'")
        print("2. Verify database exists:")
        print("   psql -U postgres -c '\\l'")
        return False
        
    except ProgrammingError as e:
        print(f"\n❌ SQL error: {e}")
        print("\nThis might mean the table structure is different than expected.")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run the fix when script is executed
if __name__ == "__main__":
    success = fix_metadata_column()
    
    if success:
        print("\n✅ You can now restart the FastAPI server!")
        print("   uvicorn app.main:app --reload")
    else:
        print("\n❌ Fix failed. Please check the errors above.")