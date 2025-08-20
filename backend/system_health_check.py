"""
Complete System Health Check
============================
Purpose: Verify all components of your RAG system are operational
Author: RAG System Development
Date: 2024

This script checks:
1. Database connectivity
2. OpenAI API access
3. Pinecone vector database
4. Document processing pipeline
5. Chat system functionality
"""

import sys
import os
from datetime import datetime
import requests
import json
from colorama import init, Fore, Style

# Initialize colorama for colored output in Windows
init(autoreset=True)

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header for each section"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}{title}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")

def print_success(message):
    """Print success message in green"""
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print error message in red"""
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

def print_warning(message):
    """Print warning message in yellow"""
    print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")

def print_info(message):
    """Print info message in blue"""
    print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

def check_database():
    """Check database connectivity and structure"""
    print_header("1. DATABASE CHECK")
    
    try:
        # Import database modules
        from app.database import engine, SessionLocal, Project, Document, Message
        from sqlalchemy import text, inspect
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print_success("Database connection successful")
            
            # Check tables exist
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            required_tables = ['projects', 'documents', 'document_chunks', 'messages']
            
            for table in required_tables:
                if table in tables:
                    # Get row count for each table
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    print_success(f"Table '{table}' exists with {count} rows")
                else:
                    print_error(f"Table '{table}' missing")
            
            # Check for message_metadata column (our recent fix)
            columns = inspector.get_columns('messages')
            column_names = [col['name'] for col in columns]
            if 'message_metadata' in column_names:
                print_success("Message metadata column configured correctly")
            elif 'metadata' in column_names:
                print_warning("Using old 'metadata' column - run fix_metadata_column.py")
            
        return True
        
    except Exception as e:
        print_error(f"Database check failed: {e}")
        print_info("Fix: Check PostgreSQL is running and credentials are correct")
        return False

def check_openai():
    """Check OpenAI API connectivity"""
    print_header("2. OPENAI API CHECK")
    
    try:
        from app.config import settings
        from app.embeddings_service import EmbeddingsService
        
        # Check API key is configured
        if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
            print_error("OpenAI API key not configured")
            print_info("Fix: Set OPENAI_API_KEY in your .env file")
            return False
        
        print_success(f"OpenAI API key configured (starts with: {settings.openai_api_key[:7]}...)")
        
        # Test embeddings generation
        service = EmbeddingsService()
        test_embedding = service.generate_embedding("Test connection")
        
        if test_embedding:
            print_success(f"Embedding generation working (dimension: {len(test_embedding)})")
            print_info(f"Model: {settings.embedding_model}")
            print_info(f"Chat model: {settings.openai_model}")
            return True
        else:
            print_error("Failed to generate test embedding")
            return False
            
    except Exception as e:
        print_error(f"OpenAI check failed: {e}")
        print_info("Fix: Verify API key and check quota at platform.openai.com")
        return False

def check_pinecone():
    """Check Pinecone vector database connectivity"""
    print_header("3. PINECONE VECTOR DATABASE CHECK")
    
    try:
        from app.config import settings
        from app.pinecone_service import PineconeService
        
        # Check API key is configured
        if not settings.pinecone_api_key or settings.pinecone_api_key == "your-pinecone-api-key-here":
            print_error("Pinecone API key not configured")
            print_info("Fix: Set PINECONE_API_KEY in your .env file")
            return False
        
        print_success(f"Pinecone API key configured (starts with: {settings.pinecone_api_key[:8]}...)")
        
        # Test Pinecone connection
        service = PineconeService()
        stats = service.get_index_stats()
        
        if 'error' not in stats:
            print_success(f"Connected to index: {stats.get('index_name')}")
            print_info(f"Total vectors: {stats.get('total_vectors', 0)}")
            print_info(f"Dimension: {stats.get('dimension', 'N/A')}")
            print_info(f"Index fullness: {stats.get('index_fullness', 0)*100:.2f}%")
            return True
        else:
            print_error(f"Pinecone connection failed: {stats.get('error')}")
            return False
            
    except Exception as e:
        print_error(f"Pinecone check failed: {e}")
        print_info("Fix: Verify API key at app.pinecone.io")
        return False

def check_document_processor():
    """Check document processing capabilities"""
    print_header("4. DOCUMENT PROCESSOR CHECK")
    
    try:
        from app.document_processor import DocumentProcessor
        from pathlib import Path
        
        processor = DocumentProcessor()
        
        # Check supported formats
        supported = list(processor.supported_extensions.keys())
        print_success(f"Supported formats: {', '.join(supported)}")
        
        # Create and process a test file
        test_file = Path("test_health_check.txt")
        test_content = "This is a test document for health check."
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Process the test file
        result = processor.process_document(str(test_file))
        
        # Clean up test file
        test_file.unlink()
        
        if result['success']:
            print_success("Document processing working")
            print_info(f"Text extraction: ✓")
            print_info(f"Chunking: ✓ ({len(result.get('chunks', []))} chunks created)")
            return True
        else:
            print_error(f"Processing failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print_error(f"Document processor check failed: {e}")
        return False

def check_api_endpoints():
    """Check FastAPI endpoints are responding"""
    print_header("5. API ENDPOINTS CHECK")
    
    base_url = "http://localhost:8000"
    
    # List of endpoints to check
    endpoints = [
        ("GET", "/health", "Health check"),
        ("GET", "/api/projects", "Projects endpoint"),
        ("GET", "/api/chat/test", "Chat service test"),
        ("GET", "/docs", "API documentation")
    ]
    
    all_working = True
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 307]:  # 307 is redirect for /docs
                print_success(f"{description}: {endpoint}")
            else:
                print_warning(f"{description}: {endpoint} (Status: {response.status_code})")
                all_working = False
                
        except requests.exceptions.ConnectionError:
            print_error(f"Cannot connect to API at {base_url}")
            print_info("Fix: Make sure FastAPI server is running:")
            print_info("     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return False
        except Exception as e:
            print_warning(f"{description}: {endpoint} ({e})")
            all_working = False
    
    return all_working

def check_complete_workflow():
    """Test a complete workflow: upload → process → chat"""
    print_header("6. COMPLETE WORKFLOW TEST")
    
    try:
        base_url = "http://localhost:8000"
        
        # Step 1: Get or create a project
        print_info("Testing project creation...")
        projects_response = requests.get(f"{base_url}/api/projects")
        
        if projects_response.status_code != 200:
            print_error("Cannot get projects")
            return False
        
        projects = projects_response.json()
        
        if projects:
            project = projects[0]
            print_success(f"Using existing project: {project['name']}")
        else:
            # Create a test project
            create_response = requests.post(
                f"{base_url}/api/projects",
                json={"name": "Health Check Project", "description": "System health check"}
            )
            if create_response.status_code == 200:
                project = create_response.json()
                print_success(f"Created test project: {project['name']}")
            else:
                print_error("Cannot create project")
                return False
        
        # Step 2: Test chat endpoint
        print_info("Testing chat functionality...")
        
        chat_request = {
            "project_id": project['id'],
            "query": "What is the purpose of this system?",
            "include_sources": True
        }
        
        chat_response = requests.post(
            f"{base_url}/api/chat/query",
            json=chat_request,
            timeout=30
        )
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            if result['success']:
                print_success("Chat system operational")
                print_info(f"Response length: {len(result['response'])} characters")
                print_info(f"Sources found: {len(result.get('sources', []))}")
                return True
            else:
                print_warning("Chat responded but with error")
                return False
        else:
            print_error(f"Chat endpoint error: {chat_response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Workflow test failed: {e}")
        return False

def main():
    """Run all health checks and provide summary"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🏥 RAG SYSTEM HEALTH CHECK")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    checks = {
        "Database": check_database(),
        "OpenAI API": check_openai(),
        "Pinecone": check_pinecone(),
        "Document Processor": check_document_processor(),
        "API Endpoints": check_api_endpoints(),
        "Complete Workflow": check_complete_workflow()
    }
    
    # Summary
    print_header("HEALTH CHECK SUMMARY")
    
    total_checks = len(checks)
    passed_checks = sum(1 for passed in checks.values() if passed)
    
    print(f"\n{Fore.CYAN}Component Status:{Style.RESET_ALL}")
    for component, passed in checks.items():
        status = f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}" if passed else f"{Fore.RED}❌ FAIL{Style.RESET_ALL}"
        print(f"  {component:20} : {status}")
    
    print(f"\n{Fore.CYAN}Overall Health: {passed_checks}/{total_checks} components operational{Style.RESET_ALL}")
    
    if passed_checks == total_checks:
        print_success("\n🎉 ALL SYSTEMS OPERATIONAL! Your RAG system is ready to use.")
    elif passed_checks >= 4:
        print_warning("\n⚠️  PARTIALLY OPERATIONAL. Some components need attention.")
    else:
        print_error("\n❌ SYSTEM NOT READY. Please fix the issues above.")
    
    # Provide next steps
    print_header("NEXT STEPS")
    
    if passed_checks == total_checks:
        print("1. Upload documents via API: POST /api/documents/upload")
        print("2. Wait for processing to complete (check status)")
        print("3. Ask questions via chat: POST /api/chat/query")
        print("4. Access API docs at: http://localhost:8000/docs")
    else:
        print("1. Fix any failed components above")
        print("2. Re-run this health check")
        print("3. Check server logs for detailed errors")

if __name__ == "__main__":
    # Install colorama if not available
    try:
        import colorama
    except ImportError:
        print("Installing colorama for colored output...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
        from colorama import init, Fore, Style
        init(autoreset=True)
    
    main()