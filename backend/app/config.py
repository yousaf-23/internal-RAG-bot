"""
Configuration module for the RAG application.
Loads environment variables and provides centralized configuration.
FIXED: Proper handling of allowed_extensions field mapping.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print to see what's being loaded
print("[Config] Loading environment variables...")
print(f"[Config] .env file exists: {os.path.exists('.env')}")

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type checking.
    """
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Pinecone Configuration
    pinecone_api_key: str = Field(default="", env="PINECONE_API_KEY")
    pinecone_environment: str = Field(default="", env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="internal-rag-index", env="PINECONE_INDEX_NAME")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./rag_app.db", 
        env="DATABASE_URL"
    )
    
    # Application Configuration
    app_name: str = Field(default="Internal RAG Bot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug_mode: bool = Field(default=True, env="DEBUG_MODE")
    
    # CORS Configuration
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # File Upload Configuration
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    
    # FIX: Use alias to map environment variable to field name
    allowed_extensions_str: str = Field(
        default="pdf,docx,doc,xlsx,xls,txt", 
        alias="ALLOWED_EXTENSIONS"  # This maps ALLOWED_EXTENSIONS env var to allowed_extensions_str field
    )
    
    # Document Processing Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # Embedding Configuration
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1536, env="EMBEDDING_DIMENSION")
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
        # FIX: Allow population by field name (for alias usage)
        populate_by_name = True
        # FIX: Don't allow extra fields to prevent the error
        extra = 'forbid'
    
    @property
    def allowed_extensions(self) -> List[str]:
        """
        Convert the comma-separated string to a list.
        This property makes it easy to use in the rest of the code.
        """
        if self.allowed_extensions_str:
            # Split by comma and strip whitespace
            extensions = [ext.strip() for ext in self.allowed_extensions_str.split(',')]
            print(f"[Config] Parsed allowed extensions: {extensions}")
            return extensions
        return ["pdf", "docx", "doc", "xlsx", "xls", "txt"]  # Default list
    
    @validator('debug_mode', pre=True)
    def parse_debug_mode(cls, v):
        """
        Parse debug_mode from string to boolean.
        Handles various string representations of boolean.
        """
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @validator('max_file_size_mb', pre=True)
    def parse_max_file_size(cls, v):
        """
        Ensure max_file_size_mb is an integer.
        """
        try:
            return int(v)
        except (ValueError, TypeError):
            return 10  # Default value
    
    @validator('chunk_size', 'chunk_overlap', 'embedding_dimension', pre=True)
    def parse_integers(cls, v):
        """
        Parse integer fields from environment variables.
        """
        try:
            return int(v)
        except (ValueError, TypeError):
            return None  # Will use default value
    
    def validate_config(self) -> bool:
        """
        Validate that all required configuration is present.
        Returns True if valid, raises exception if not.
        """
        errors = []
        
        # Check required API keys (make them optional for initial testing)
        if not self.openai_api_key:
            print("[Config] ⚠️  WARNING: OpenAI API key is not set")
        
        if not self.pinecone_api_key:
            print("[Config] ⚠️  WARNING: Pinecone API key is not set")
        
        if not self.pinecone_environment and self.pinecone_api_key:
            errors.append("Pinecone environment is required when API key is set")
        
        # Check database URL
        if not self.database_url:
            errors.append("Database URL is missing")
        
        if errors:
            error_msg = "Configuration errors:\n" + "\n".join(f"- {e}" for e in errors)
            raise ValueError(error_msg)
        
        print("[Config] ✅ Configuration validated successfully")
        return True

# Create global settings instance with error handling
try:
    print("[Config] Creating settings instance...")
    settings = Settings()
    
    # Debug: Print loaded configuration (hide sensitive data)
    if settings.debug_mode:
        print("\n" + "="*50)
        print("🔧 RAG Application Configuration")
        print("="*50)
        print(f"App Name: {settings.app_name}")
        print(f"App Version: {settings.app_version}")
        print(f"Debug Mode: {settings.debug_mode}")
        
        # Safely handle database URL display
        if '@' in settings.database_url:
            db_parts = settings.database_url.split('@')
            db_display = db_parts[0].split('://')[0] + '://***:***@' + db_parts[1]
        else:
            db_display = settings.database_url
        print(f"Database: {db_display}")
        
        print(f"Frontend URL: {settings.frontend_url}")
        print(f"OpenAI Model: {settings.openai_model}")
        print(f"OpenAI API Key Set: {bool(settings.openai_api_key)}")
        print(f"Pinecone API Key Set: {bool(settings.pinecone_api_key)}")
        print(f"Embedding Model: {settings.embedding_model}")
        print(f"Pinecone Index: {settings.pinecone_index_name}")
        print(f"Chunk Size: {settings.chunk_size}")
        print(f"Chunk Overlap: {settings.chunk_overlap}")
        print(f"Max File Size: {settings.max_file_size_mb} MB")
        print(f"Allowed Extensions: {settings.allowed_extensions}")
        print("="*50 + "\n")
        
    # Run validation
    settings.validate_config()
        
except Exception as e:
    print(f"[Config] ❌ Error creating settings: {e}")
    print("\n[Config] Debugging info:")
    print(f"[Config] Error type: {type(e).__name__}")
    
    # Print environment variables for debugging
    print("\n[Config] Environment variables related to our app:")
    for key in os.environ:
        if any(x in key for x in ['APP_', 'DATABASE_', 'OPENAI_', 'PINECONE_', 'ALLOWED_', 'CHUNK_', 'DEBUG_']):
            if 'KEY' in key or 'PASSWORD' in key:
                print(f"  {key}: ***HIDDEN***")
            else:
                print(f"  {key}: {os.environ[key]}")
    
    print("\n[Config] Using fallback configuration...")
    
    # Create settings with defaults only
    class DefaultSettings:
        """Fallback settings if .env parsing fails"""
        openai_api_key = ""
        openai_model = "gpt-4-turbo-preview"
        pinecone_api_key = ""
        pinecone_environment = ""
        pinecone_index_name = "internal-rag-index"
        database_url = "postgresql://rag_user:rag_password123@localhost:5432/rag_database"
        app_name = "Internal RAG Bot"
        app_version = "1.0.0"
        debug_mode = True
        frontend_url = "http://localhost:3000"
        max_file_size_mb = 10
        allowed_extensions = ["pdf", "docx", "doc", "xlsx", "xls","txt"]
        allowed_extensions_str = "pdf,docx,doc,xlsx,xls,txt"
        chunk_size = 1000
        chunk_overlap = 200
        embedding_model = "text-embedding-3-small"
        embedding_dimension = 1536
        
        def validate_config(self):
            return True
    
    settings = DefaultSettings()
    print("[Config] ✅ Fallback settings loaded")