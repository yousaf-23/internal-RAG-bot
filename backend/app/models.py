"""
Pydantic models for request/response validation.
These models ensure type safety and automatic validation for all API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

# Enums for constrained fields
class FileType(str, Enum):
    """Supported file types for document upload"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    XLSX = "xlsx"
    XLS = "xls"
    TXT = "txt"

class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class MessageRole(str, Enum):
    """Chat message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Project Models
class ProjectBase(BaseModel):
    """Base project model with common fields"""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")

class ProjectCreate(ProjectBase):
    """Model for creating a new project"""
    pass

class ProjectUpdate(BaseModel):
    """Model for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ProjectResponse(ProjectBase):
    """Model for project responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True  # Enable ORM mode

# Document Models
class DocumentBase(BaseModel):
    """Base document model"""
    filename: str
    file_type: FileType
    project_id: str

class DocumentCreate(DocumentBase):
    """Model for creating a document record"""
    size: int = Field(..., gt=0, description="File size in bytes")
    
    @validator('size')
    def validate_size(cls, v):
        """Validate file size is within limits"""
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if v > max_size:
            raise ValueError(f"File size exceeds maximum of {max_size} bytes")
        return v

class DocumentResponse(DocumentBase):
    """Model for document responses"""
    id: str
    uploaded_at: datetime
    size: int
    status: DocumentStatus
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

# Chat Models

class ChatRequest(BaseModel):
    """
    Model for chat request from frontend.
    This is what the frontend sends when asking a question.
    """
    project_id: str  # Which project's documents to search
    query: str  # The user's question
    conversation_id: Optional[str] = None  # For maintaining context
    include_sources: bool = True  # Whether to return source documents
    max_chunks: Optional[int] = 5  # How many document chunks to use
    
    class Config:
        # This provides example data for API documentation
        json_schema_extra = {
            "example": {
                "project_id": "proj_abc123",
                "query": "What are the main features of the product?",
                "conversation_id": None,
                "include_sources": True,
                "max_chunks": 5
            }
        }

class ChatResponse(BaseModel):
    """
    Model for chat response sent back to frontend.
    This contains the AI's answer and metadata.
    """
    success: bool  # Whether the request was successful
    response: str  # The AI's answer
    conversation_id: str  # ID for maintaining conversation context
    sources: Optional[List[Dict[str, Any]]] = None  # Documents used
    message_metadata: Optional[Dict[str, Any]] = None  # Additional info (tokens, time, etc.)
    error: Optional[str] = None  # Error message if something went wrong
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "Based on the documents, the main features include...",
                "conversation_id": "conv_123456",
                "sources": [
                    {
                        "document_id": "doc_789",
                        "filename": "product_guide.pdf",
                        "relevance_score": 0.92
                    }
                ],
                "message_metadata": {
                    "response_time": 2.5,
                    "chunks_used": 3,
                    "model": "gpt-4-turbo-preview",
                    "tokens_used": 850
                }
            }
        }

class ConversationHistory(BaseModel):
    """
    Model for conversation history.
    Used to retrieve past conversations.
    """
    conversation_id: str  # Unique conversation identifier
    project_id: str  # Which project this conversation belongs to
    messages: List[Dict[str, Any]]  # List of all messages
    created_at: datetime  # When conversation started
    updated_at: datetime  # Last message time
    message_count: Optional[int] = 0  # Total number of messages
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123456",
                "project_id": "proj_abc123",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is machine learning?",
                        "timestamp": "2024-01-15T10:30:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Machine learning is a subset of AI...",
                        "timestamp": "2024-01-15T10:30:05Z"
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:05Z",
                "message_count": 2
            }
        }

class MessageRequest(BaseModel):
    """
    Model for individual message in chat.
    Represents a single message from user or assistant.
    """
    role: str  # Either "user" or "assistant"
    content: str  # The actual message text
    message_metadata: Optional[Dict[str, Any]] = None  # Additional data
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What are vectors in the context of AI?",
                "message_metadata": {
                    "source": "web_ui",
                    "user_id": "user_123"
                }
            }
        }

# Debug print to confirm models are loaded
print("[Models] Chat models loaded: ChatRequest, ChatResponse, ConversationHistory, MessageRequest")

# File Upload Response
class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    document_id: str
    filename: str
    status: str
    message: Optional[str] = None

# Generic Response Models
class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    
# Batch Operations
class BatchDocumentUpload(BaseModel):
    """Model for uploading multiple documents"""
    project_id: str
    documents: List[DocumentCreate]

class QueryMetrics(BaseModel):
    """Metrics for query performance"""
    query_time_ms: float
    embedding_time_ms: float
    search_time_ms: float
    generation_time_ms: float
    total_chunks_searched: int
    relevant_chunks_found: int

# Health Check
class HealthStatus(BaseModel):
    """Health check response model"""
    status: str = Field(default="healthy")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str
    services: Dict[str, bool] = Field(
        default_factory=lambda: {
            "database": False,
            "pinecone": False,
            "openai": False
        }
    )
    
# Debugging helper
if __name__ == "__main__":
    # Test model creation
    print("Testing Pydantic models...")
    
    # Test ProjectCreate
    project = ProjectCreate(name="Test Project", description="Test description")
    print(f"✅ ProjectCreate: {project.model_dump()}")
    
    # Test ChatRequest
    chat_req = ChatRequest(
        project_id="test-123",
        query="What is the main topic?",
        max_results=5
    )
    print(f"✅ ChatRequest: {chat_req.model_dump()}")
    
    print("\n✅ All models validated successfully!")