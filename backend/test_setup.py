"""
Test script to verify the backend setup is working correctly.
Run this to ensure all dependencies are installed and configuration is valid.
"""

import sys
import os

print("="*50)
print("🧪 Testing Backend Setup")
print("="*50)

# Test 1: Python version
print("\n1. Checking Python version...")
print(f"   Python version: {sys.version}")
if sys.version_info >= (3, 8):
    print("   ✅ Python version is compatible")
else:
    print("   ❌ Python 3.8 or higher is required")

# Test 2: Import dependencies
print("\n2. Testing imports...")
try:
    import fastapi
    print(f"   ✅ FastAPI {fastapi.__version__}")
    
    import uvicorn
    print(f"   ✅ Uvicorn imported")
    
    import openai
    print(f"   ✅ OpenAI {openai.__version__}")
    
    import pinecone
    print(f"   ✅ Pinecone imported")
    
    import sqlalchemy
    print(f"   ✅ SQLAlchemy {sqlalchemy.__version__}")
    
    import pydantic
    print(f"   ✅ Pydantic {pydantic.__version__}")
    
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("   Run: pip install -r requirements.txt")

# Test 3: Configuration
print("\n3. Testing configuration...")
try:
    from app.config import settings
    
    # Check if API keys are set (don't print them!)
    if settings.openai_api_key:
        print(f"   ✅ OpenAI API key is set ({len(settings.openai_api_key)} characters)")
    else:
        print("   ⚠️  OpenAI API key is not set")
    
    if settings.pinecone_api_key:
        print(f"   ✅ Pinecone API key is set ({len(settings.pinecone_api_key)} characters)")
    else:
        print("   ⚠️  Pinecone API key is not set")
    
    print(f"   ✅ Database URL: {settings.database_url}")
    print(f"   ✅ Frontend URL: {settings.frontend_url}")
    
except Exception as e:
    print(f"   ❌ Configuration error: {e}")

# Test 4: Models
print("\n4. Testing Pydantic models...")
try:
    from app.models import ProjectCreate, ChatRequest
    
    # Test creating a model
    test_project = ProjectCreate(name="Test", description="Test project")
    print(f"   ✅ Models working: {test_project.name}")
    
except Exception as e:
    print(f"   ❌ Model error: {e}")

print("\n" + "="*50)
print("🎉 Setup test complete!")
print("="*50)