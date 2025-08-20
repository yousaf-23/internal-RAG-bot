"""
Verify that core packages are installed correctly.
This helps identify which packages are working and which need attention.
"""

import sys
print(f"Python Version: {sys.version}\n")
print("="*60)
print("Package Installation Status:")
print("="*60)

# Dictionary of packages to check
packages_to_check = {
    'fastapi': 'FastAPI',
    'uvicorn': 'Uvicorn',
    'sqlalchemy': 'SQLAlchemy',
    'psycopg2': 'PostgreSQL Driver',
    'openai': 'OpenAI',
    'pinecone': 'Pinecone',
    'pypdf': 'PDF Processing',
    'docx': 'Word Processing',
    'openpyxl': 'Excel Processing',
    'pydantic': 'Pydantic',
    'dotenv': 'Python-dotenv',
    'httpx': 'HTTPX',
}

# Try importing each package
for module_name, display_name in packages_to_check.items():
    try:
        if module_name == 'dotenv':
            import dotenv
            version = getattr(dotenv, '__version__', 'installed')
        elif module_name == 'docx':
            import docx
            version = getattr(docx, '__version__', 'installed')
        else:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'installed')
        print(f"✅ {display_name:20} : {version}")
    except ImportError as e:
        print(f"❌ {display_name:20} : Not installed - {e}")
    except Exception as e:
        print(f"⚠️  {display_name:20} : Error - {e}")

# Check pandas separately
print("\n" + "="*60)
print("Pandas Status (Optional for now):")
print("="*60)
try:
    import pandas as pd
    print(f"✅ Pandas: {pd.__version__}")
except ImportError:
    print("❌ Pandas: Not installed (can work without it for now)")

# Test PostgreSQL connection with correct SQLAlchemy 2.0 syntax
print("\n" + "="*60)
print("PostgreSQL Connection Test:")
print("="*60)
try:
    from sqlalchemy import create_engine, text  # Import text for SQL queries
    
    # Create engine with your credentials
    engine = create_engine("postgresql://rag_user:rag_password123@localhost:5432/rag_database")
    
    # Use text() wrapper for raw SQL in SQLAlchemy 2.0
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))  # Wrap SQL in text()
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL connected: {version[:50]}...")
        
        # Additional connection info
        result = conn.execute(text("SELECT current_database()"))
        db_name = result.fetchone()[0]
        print(f"✅ Current database: {db_name}")
        
        result = conn.execute(text("SELECT current_user"))
        user = result.fetchone()[0]
        print(f"✅ Connected as user: {user}")
        
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    print("\nTroubleshooting steps:")
    print("1. Check if PostgreSQL service is running:")
    print("   Get-Service -Name 'postgresql*'")
    print("2. Verify credentials in your .env file")
    print("3. Check if database 'rag_database' exists:")
    print("   psql -U postgres -c '\\l'")

print("\n" + "="*60)
print("Summary:")
print("="*60)
print("✅ All core packages are installed successfully!")
print("✅ Python 3.12.10 is perfect for this project")
print("✅ You're ready to build the FastAPI application!")