"""
Database configuration and connection management for PostgreSQL.
This module handles all database operations using SQLAlchemy ORM.
Updated for SQLAlchemy 2.0 compatibility.
"""

import os
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float, ForeignKey, Boolean, text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool
from app.config import settings

# Debug: Print database URL (hide password for security)
if settings.debug_mode:
    db_url_parts = settings.database_url.split('@')
    if len(db_url_parts) > 1:
        db_url_debug = db_url_parts[0].split('://')[0] + '://***:***@' + db_url_parts[1]
    else:
        db_url_debug = settings.database_url
    print(f"[Database] Connecting to: {db_url_debug}")

# Create SQLAlchemy engine with PostgreSQL-specific settings
try:
    engine = create_engine(
        settings.database_url,
        # PostgreSQL-specific connection pool settings
        pool_size=10,  # Number of connections to maintain in pool
        max_overflow=20,  # Maximum overflow connections
        pool_pre_ping=True,  # Verify connections before using
        echo=settings.debug_mode,  # Log SQL queries in debug mode
        connect_args={
            # PostgreSQL-specific connection arguments
            "options": "-c timezone=utc"  # Set timezone to UTC
        }
    )
    print("[Database] ✅ Engine created successfully")
except Exception as e:
    print(f"[Database] ❌ Failed to create engine: {e}")
    raise

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit (we'll handle transactions)
    autoflush=False,  # Don't auto-flush to database
    bind=engine
)

# Create base class for declarative models
Base = declarative_base()

# Database Models using SQLAlchemy ORM
class Project(Base):
    """
    Project model - represents a collection of documents.
    Each project can have multiple documents and chat messages.
    """
    __tablename__ = "projects"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Project details
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships (cascade delete means deleting project deletes all related items)
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"

class Document(Base):
    """
    Document model - represents an uploaded file.
    Stores metadata about documents that are processed and indexed.
    """
    __tablename__ = "documents"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key to project
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document details
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, etc.
    file_path = Column(String(500), nullable=True)  # Path to stored file
    size = Column(Integer, nullable=False)  # File size in bytes
    
    # Processing status
    status = Column(String(20), default="uploading", nullable=False, index=True)
    # Status values: uploading, processing, ready, error
    error_message = Column(Text, nullable=True)
    
    # Document metadata
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # Vector store metadata
    chunk_count = Column(Integer, default=0)  # Number of chunks created
    indexed = Column(Boolean, default=False)  # Whether indexed in Pinecone
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"

class DocumentChunk(Base):
    """
    DocumentChunk model - represents a chunk of text from a document.
    Each document is split into chunks for vector embedding and retrieval.
    """
    __tablename__ = "document_chunks"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign key to document
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Chunk details
    chunk_index = Column(Integer, nullable=False)  # Order of chunk in document
    chunk_text = Column(Text, nullable=False)  # The actual text content
    
    # Metadata
    page_number = Column(Integer, nullable=True)  # Page number if applicable
    char_start = Column(Integer, nullable=True)  # Starting character position
    char_end = Column(Integer, nullable=True)  # Ending character position
    
    # Vector store metadata
    vector_id = Column(String, nullable=True, index=True)  # ID in Pinecone
    embedding_model = Column(String, nullable=True)  # Model used for embedding
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"

class Message(Base):
    """
    Represents a chat message in a conversation.
    UPDATED: Added conversation_id for grouping messages into conversations
    """
    __tablename__ = "messages"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Foreign keys
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # NEW FIELD: Conversation ID for grouping messages
    conversation_id = Column(String, nullable=True, index=True)  # Added index for faster queries
    
    # Message content
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Store additional data like tokens, model, etc.
    
    # Relationships
    project = relationship("Project", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation={self.conversation_id})>"

# Debug print to confirm model is updated
print("[Database] Message model updated with conversation_id field")

# Database initialization and utilities
def init_db():
    """
    Initialize the database by creating all tables.
    Run this once when setting up the application.
    """
    try:
        print("[Database] Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("[Database] ✅ All tables created successfully!")
        
        # Test connection with correct SQLAlchemy 2.0 syntax
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))  # Use text() wrapper
            version = result.fetchone()[0]
            print(f"[Database] ✅ Connected to PostgreSQL: {version[:50]}...")
            
    except Exception as e:
        print(f"[Database] ❌ Error initializing database: {e}")
        print("\nDebugging steps:")
        print("1. Check PostgreSQL is running: Get-Service -Name 'postgresql*'")
        print("2. Check database exists: psql -U postgres -c '\\l'")
        print("3. Check user permissions: psql -U rag_user -d rag_database")
        raise

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Used in FastAPI dependency injection.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        # Debug: Log session creation
        if settings.debug_mode:
            print(f"[Database] Creating new session: {id(db)}")
        yield db
    finally:
        # Always close the session
        db.close()
        if settings.debug_mode:
            print(f"[Database] Closed session: {id(db)}")

def test_connection():
    """
    Test database connection and print diagnostic information.
    Useful for debugging connection issues.
    """
    try:
        print("\n" + "="*50)
        print("🔍 Testing PostgreSQL Connection")
        print("="*50)
        
        # Test raw connection with SQLAlchemy 2.0 syntax
        with engine.connect() as conn:
            # Get PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL Version: {version[:50]}...")
            
            # Get current database
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"✅ Current Database: {db_name}")
            
            # Get current user
            result = conn.execute(text("SELECT current_user"))
            user = result.fetchone()[0]
            print(f"✅ Current User: {user}")
            
            # List all tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✅ Tables in database: {tables if tables else 'No tables yet'}")
            
        print("="*50)
        print("✅ Database connection successful!")
        print("="*50 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check PostgreSQL is running: Get-Service -Name 'postgresql*'")
        print("2. Check credentials in .env file")
        print("3. Check database exists: psql -U postgres -c '\\l'")
        print("4. Check user has permissions: psql -U rag_user -d rag_database")
        return False

# Test connection when module is imported (only in debug mode)
if settings.debug_mode:
    print("[Database] Module loaded, testing connection...")
    # Don't test on import to avoid connection issues during startup
    # test_connection()  # Commented out - will test manually