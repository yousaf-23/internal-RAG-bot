"""
Database Viewer Script
----------------------
This script displays the current state of all tables in your RAG database.
Run this anytime to see what data is stored.

Usage: python view_database.py
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import tabulate with error handling
try:
    from tabulate import tabulate
except ImportError:
    print("Installing tabulate for better table display...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
    print("Tabulate installed! Re-running script...\n")
    from tabulate import tabulate

from app.config import settings

def view_database():
    """
    Display all data from all tables in a formatted way
    """
    print("\n" + "="*80)
    print("📊 RAG DATABASE VIEWER")
    print("="*80)
    
    # Handle database URL display
    try:
        if hasattr(settings, 'database_url'):
            if '@' in settings.database_url:
                db_display = settings.database_url.split('@')[1]
            else:
                db_display = 'local database'
        else:
            db_display = 'unknown'
    except:
        db_display = 'configuration error'
    
    print(f"Connected to: {db_display}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        # Create database connection
        # Use the database URL directly if settings failed
        if hasattr(settings, 'database_url'):
            db_url = settings.database_url
        else:
            # Fallback to hardcoded URL if config failed
            db_url = "postgresql://rag_user:rag_password123@localhost:5432/rag_database"
            print(f"[Debug] Using fallback database URL")
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Test connection first
            result = conn.execute(text("SELECT 1"))
            print("[Debug] Database connection successful\n")
            
            # 1. PROJECTS TABLE
            print("\n📁 PROJECTS")
            print("-" * 40)
            
            result = conn.execute(text("""
                SELECT 
                    id,
                    name,
                    description,
                    created_at,
                    updated_at
                FROM projects
                ORDER BY created_at DESC
            """))
            
            projects = result.fetchall()
            
            if projects:
                # Convert to list of lists for tabulate
                project_data = []
                for p in projects:
                    # Handle different data formats safely
                    project_id = str(p[0])[:12] + "..." if len(str(p[0])) > 12 else str(p[0])
                    project_name = str(p[1])[:30] if p[1] else "N/A"
                    project_desc = str(p[2])[:40] if p[2] else "N/A"
                    
                    # Handle datetime formatting
                    try:
                        created = p[3].strftime('%Y-%m-%d %H:%M') if p[3] else "N/A"
                    except:
                        created = str(p[3])[:16] if p[3] else "N/A"
                    
                    try:
                        updated = p[4].strftime('%Y-%m-%d %H:%M') if p[4] else "N/A"
                    except:
                        updated = str(p[4])[:16] if p[4] else "N/A"
                    
                    project_data.append([
                        project_id,
                        project_name,
                        project_desc,
                        created,
                        updated
                    ])
                
                headers = ["ID", "Name", "Description", "Created", "Updated"]
                print(tabulate(project_data, headers=headers, tablefmt="grid"))
                print(f"\nTotal Projects: {len(projects)}")
            else:
                print("No projects found. Create one using the API at http://localhost:8000/docs")
            
            # 2. DOCUMENTS TABLE
            print("\n📄 DOCUMENTS")
            print("-" * 40)
            
            result = conn.execute(text("""
                SELECT 
                    d.id,
                    d.filename,
                    d.file_type,
                    d.status,
                    d.size,
                    p.name as project_name,
                    d.uploaded_at
                FROM documents d
                LEFT JOIN projects p ON d.project_id = p.id
                ORDER BY d.uploaded_at DESC
                LIMIT 10
            """))
            
            documents = result.fetchall()
            
            if documents:
                doc_data = []
                for d in documents:
                    doc_id = str(d[0])[:12] + "..." if len(str(d[0])) > 12 else str(d[0])
                    filename = str(d[1])[:30] if d[1] else "N/A"
                    file_type = str(d[2]) if d[2] else "N/A"
                    status = str(d[3]) if d[3] else "N/A"
                    
                    # Handle size formatting
                    try:
                        size = f"{d[4]/1024:.1f}KB" if d[4] else "0KB"
                    except:
                        size = "N/A"
                    
                    project = str(d[5])[:20] if d[5] else "N/A"
                    
                    # Handle date formatting
                    try:
                        uploaded = d[6].strftime('%Y-%m-%d') if d[6] else "N/A"
                    except:
                        uploaded = str(d[6])[:10] if d[6] else "N/A"
                    
                    doc_data.append([
                        doc_id,
                        filename,
                        file_type,
                        status,
                        size,
                        project,
                        uploaded
                    ])
                
                headers = ["ID", "Filename", "Type", "Status", "Size", "Project", "Uploaded"]
                print(tabulate(doc_data, headers=headers, tablefmt="grid"))
                
                # Count total documents
                result = conn.execute(text("SELECT COUNT(*) FROM documents"))
                total = result.fetchone()[0]
                print(f"\nTotal Documents: {total}")
            else:
                print("No documents uploaded yet.")
            
            # 3. MESSAGES TABLE
            print("\n💬 RECENT MESSAGES")
            print("-" * 40)
            
            result = conn.execute(text("""
                SELECT 
                    m.id,
                    m.role,
                    LEFT(m.content, 50) as content_preview,
                    p.name as project_name,
                    m.timestamp
                FROM messages m
                LEFT JOIN projects p ON m.project_id = p.id
                ORDER BY m.timestamp DESC
                LIMIT 5
            """))
            
            messages = result.fetchall()
            
            if messages:
                msg_data = []
                for m in messages:
                    msg_id = str(m[0])[:12] + "..." if len(str(m[0])) > 12 else str(m[0])
                    role = str(m[1]) if m[1] else "N/A"
                    content = str(m[2]) + "..." if m[2] and len(str(m[2])) == 50 else str(m[2]) if m[2] else "N/A"
                    project = str(m[3])[:20] if m[3] else "N/A"
                    
                    try:
                        time = m[4].strftime('%H:%M:%S') if m[4] else "N/A"
                    except:
                        time = str(m[4])[:8] if m[4] else "N/A"
                    
                    msg_data.append([msg_id, role, content, project, time])
                
                headers = ["ID", "Role", "Content Preview", "Project", "Time"]
                print(tabulate(msg_data, headers=headers, tablefmt="grid"))
                
                # Count total messages
                result = conn.execute(text("SELECT COUNT(*) FROM messages"))
                total = result.fetchone()[0]
                print(f"\nTotal Messages: {total}")
            else:
                print("No messages yet. Start chatting!")
            
            # 4. DATABASE STATISTICS
            print("\n📈 DATABASE STATISTICS")
            print("-" * 40)
            
            result = conn.execute(text("""
                SELECT 
                    'Projects' as table_name, COUNT(*) as count FROM projects
                UNION ALL
                SELECT 'Documents', COUNT(*) FROM documents
                UNION ALL
                SELECT 'Document Chunks', COUNT(*) FROM document_chunks
                UNION ALL
                SELECT 'Messages', COUNT(*) FROM messages
            """))
            
            stats = result.fetchall()
            
            stats_data = [[s[0], s[1]] for s in stats]
            headers = ["Table", "Row Count"]
            print(tabulate(stats_data, headers=headers, tablefmt="grid"))
            
            # Database size
            try:
                result = conn.execute(text("""
                    SELECT pg_database_size('rag_database') as size
                """))
                size = result.fetchone()[0]
                print(f"\nTotal Database Size: {size/1024/1024:.2f} MB")
            except Exception as e:
                print(f"\nCouldn't get database size: {e}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"[Debug] Error type: {type(e).__name__}")
        
        # More detailed debugging
        import traceback
        print("\n[Debug] Full traceback:")
        traceback.print_exc()
        
        print("\nDebugging steps:")
        print("1. Check PostgreSQL is running: Get-Service -Name 'postgresql*'")
        print("2. Verify database exists: psql -U postgres -c '\\l'")
        print("3. Check credentials in .env file")
        print("4. Test connection manually: psql -U rag_user -d rag_database -h localhost")
        return False
    
    print("\n" + "="*80)
    print("✅ Database view complete!")
    print("="*80)
    return True

if __name__ == "__main__":
    view_database()