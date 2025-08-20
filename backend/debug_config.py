"""
Debug script to test configuration loading.
Run this to diagnose configuration issues.
"""

import os
import sys

print("="*60)
print("🔍 Configuration Debug Tool")
print("="*60)

# Step 1: Check Python environment
print("\n1. Python Environment:")
print(f"   Python version: {sys.version}")
print(f"   Current directory: {os.getcwd()}")
print(f"   Virtual env: {sys.prefix}")

# Step 2: Check .env file
print("\n2. Checking .env file:")
env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    print(f"   ✅ .env file found at: {env_path}")
    print(f"   File size: {os.path.getsize(env_path)} bytes")
    
    # Read and display .env content (hide sensitive values)
    print("\n   .env contents (sensitive values hidden):")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if 'KEY' in key or 'PASSWORD' in key:
                        print(f"   Line {line_num}: {key}=***HIDDEN***")
                    else:
                        print(f"   Line {line_num}: {key}={value}")
else:
    print(f"   ❌ .env file NOT found at: {env_path}")
    print("   Creating a template .env file...")
    
    template = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=rag-documents

# Database Configuration - PostgreSQL
DATABASE_URL=postgresql://rag_user:rag_password123@localhost:5432/rag_database

# Application Configuration
APP_NAME=Internal RAG Bot
APP_VERSION=1.0.0
DEBUG_MODE=true

# CORS Configuration
FRONTEND_URL=http://localhost:3000

# File Upload Configuration
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,docx,doc,xlsx,xls,txt

# Chunking Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Embedding Configuration
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(template)
    print("   ✅ Created template .env file")

# Step 3: Test dotenv loading
print("\n3. Testing python-dotenv:")
try:
    from dotenv import load_dotenv
    
    # Load .env file
    result = load_dotenv(override=True)
    print(f"   ✅ dotenv loaded: {result}")
    
    # Check specific environment variables
    test_vars = ['DATABASE_URL', 'APP_NAME', 'ALLOWED_EXTENSIONS', 'DEBUG_MODE']
    for var in test_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'KEY' in var:
                print(f"   {var}: ***HIDDEN***")
            else:
                print(f"   {var}: {value[:50]}..." if len(value) > 50 else f"   {var}: {value}")
        else:
            print(f"   {var}: NOT SET")
            
except ImportError as e:
    print(f"   ❌ python-dotenv not installed: {e}")

# Step 4: Test Pydantic settings
print("\n4. Testing Pydantic Settings:")
try:
    # Import without loading the full config
    from pydantic import BaseSettings, Field
    print("   ✅ Pydantic imported successfully")
    
    # Try to import our config
    try:
        from app.config import settings
        print(f"   ✅ Settings loaded successfully")
        print(f"   App Name: {settings.app_name}")
        print(f"   Debug Mode: {settings.debug_mode}")
        print(f"   Allowed Extensions: {settings.allowed_extensions if hasattr(settings, 'allowed_extensions') else 'N/A'}")
    except Exception as e:
        print(f"   ❌ Error loading settings: {e}")
        print(f"   Error type: {type(e).__name__}")
        
except ImportError as e:
    print(f"   ❌ Pydantic not installed: {e}")

# Step 5: Test database URL parsing
print("\n5. Testing Database URL:")
db_url = os.getenv('DATABASE_URL', 'not set')
if db_url != 'not set':
    # Parse and validate PostgreSQL URL
    if db_url.startswith('postgresql://'):
        try:
            # Extract components
            parts = db_url.replace('postgresql://', '').split('@')
            if len(parts) == 2:
                user_pass = parts[0].split(':')
                host_db = parts[1].split('/')
                print(f"   ✅ Valid PostgreSQL URL structure")
                print(f"   User: {user_pass[0]}")
                print(f"   Host: {host_db[0].split(':')[0]}")
                print(f"   Port: {host_db[0].split(':')[1] if ':' in host_db[0] else '5432'}")
                print(f"   Database: {host_db[1] if len(host_db) > 1 else 'unknown'}")
        except Exception as e:
            print(f"   ❌ Error parsing database URL: {e}")
else:
    print("   ❌ DATABASE_URL not set in environment")

print("\n" + "="*60)
print("Debug complete!")
print("="*60)