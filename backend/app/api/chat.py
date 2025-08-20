"""
Chat API Endpoints
==================
Purpose: Handle chat interactions through REST API
Author: RAG System Development
Date: 2024

This module provides:
1. Chat endpoint for Q&A
2. Conversation history management
3. Source document retrieval
4. Chat session management

API Endpoints:
- POST /api/chat/query - Send a question and get a response
- GET /api/chat/history/{project_id} - Get chat history
- DELETE /api/chat/history/{conversation_id} - Clear conversation
"""

# ============================================================================
# IMPORTS
# ============================================================================
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import our modules - Models are now imported from models.py
from app.database import get_db, Message, Project, Document
from app.chat_service import ChatService
from app.models import ChatRequest, ChatResponse, ConversationHistory 

# ============================================================================
# API ROUTER
# ============================================================================

router = APIRouter()

# Initialize chat service (singleton pattern)
_chat_service = None

def get_chat_service() -> ChatService:
    """
    Get or create the chat service instance.
    Using singleton pattern to avoid reinitializing services.
    """
    global _chat_service
    if _chat_service is None:
        print("[Chat API] Initializing chat service...")
        _chat_service = ChatService()
    return _chat_service

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process a chat query using RAG.
    
    This endpoint:
    1. Validates the project exists
    2. Searches for relevant document chunks
    3. Generates a response using GPT-4
    4. Saves the interaction to database
    5. Returns the response with sources
    
    Args:
        request: Chat query request
        db: Database session
        
    Returns:
        Chat response with answer and sources
    """
    print(f"\n[Chat API] Received query for project: {request.project_id}")
    print(f"[Chat API] Query: {request.query[:100]}...")
    
    try:
        # Step 1: Validate project exists and has documents
        project = db.query(Project).filter(
            Project.id == request.project_id
        ).first()
        
        if not project:
            print(f"[Chat API] ❌ Project not found: {request.project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{request.project_id}' not found"
            )
        
        # Check if project has any indexed documents
        indexed_docs = db.query(Document).filter(
            Document.project_id == request.project_id,
            Document.indexed == True
        ).count()
        
        if indexed_docs == 0:
            print(f"[Chat API] ⚠️  No indexed documents in project")
            # Can still proceed but warn the user
        
        print(f"[Chat API] Project '{project.name}' has {indexed_docs} indexed documents")
        
        # Step 2: Generate or use existing conversation ID
        conversation_id = request.conversation_id or f"conv_{uuid4().hex[:12]}"
        print(f"[Chat API] Conversation ID: {conversation_id}")
        
        # Step 3: Get chat service and process query
        chat_service = get_chat_service()
        
        # Override max_chunks if specified
        if request.max_chunks:
            chat_service.max_context_chunks = request.max_chunks
        
        # Process the chat query
        result = chat_service.chat(
            project_id=request.project_id,
            query=request.query,
            conversation_id=conversation_id,
            save_to_db=True
        )
        
        # Step 4: Save to database
        if result['success']:
            try:
                # Save user message
                user_message = Message(
                    id=f"msg_{uuid4().hex[:12]}",
                    project_id=request.project_id,
                    conversation_id=conversation_id,
                    role="user",
                    content=request.query,
                    timestamp=datetime.utcnow()
                )
                db.add(user_message)
                
                # Save assistant response
                assistant_message = Message(
                    id=f"msg_{uuid4().hex[:12]}",
                    project_id=request.project_id,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=result['response'],
                    timestamp=datetime.utcnow(),
                    message_metadata=result.get('metadata', {})
                )
                db.add(assistant_message)
                
                db.commit()
                print(f"[Chat API] ✅ Messages saved to database")
                
            except Exception as e:
                print(f"[Chat API] ⚠️  Failed to save messages: {e}")
                db.rollback()
                # Continue - the response was still generated
        
        # Step 5: Format response
        response = ChatResponse(
            success=result['success'],
            response=result['response'],
            conversation_id=conversation_id,
            sources=result.get('sources', []) if request.include_sources else None,
            message_metadata=result.get('metadata', {})
        )
        
        print(f"[Chat API] ✅ Query processed successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Chat API] ❌ Error processing query: {e}")
        
        # Log detailed error for debugging
        import traceback
        print("[Chat API] Detailed error:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )

@router.get("/history/{project_id}", response_model=List[ConversationHistory])
async def get_chat_history(
    project_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a project.
    
    Args:
        project_id: Project ID
        limit: Maximum number of conversations to return
        db: Database session
        
    Returns:
        List of conversations with messages
    """
    print(f"[Chat API] Getting chat history for project: {project_id}")
    
    try:
        # Validate project exists
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found"
            )
        
        # Get unique conversations
        conversations = db.query(Message.conversation_id).filter(
            Message.project_id == project_id
        ).distinct().limit(limit).all()
        
        print(f"[Chat API] Found {len(conversations)} conversations")
        
        # Build response
        history = []
        for (conv_id,) in conversations:
            # Get messages for this conversation
            messages = db.query(Message).filter(
                Message.conversation_id == conv_id
            ).order_by(Message.timestamp).all()
            
            if messages:
                history.append(ConversationHistory(
                    conversation_id=conv_id,
                    project_id=project_id,
                    messages=[
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat()
                        }
                        for msg in messages
                    ],
                    created_at=messages[0].timestamp,
                    updated_at=messages[-1].timestamp
                ))
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Chat API] ❌ Error getting history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )

@router.delete("/history/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: Conversation ID to delete
        db: Database session
        
    Returns:
        Success message
    """
    print(f"[Chat API] Deleting conversation: {conversation_id}")
    
    try:
        # Delete all messages in the conversation
        deleted_count = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()
        
        db.commit()
        
        print(f"[Chat API] ✅ Deleted {deleted_count} messages")
        
        return {
            "success": True,
            "message": f"Deleted conversation with {deleted_count} messages"
        }
        
    except Exception as e:
        print(f"[Chat API] ❌ Error deleting conversation: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

@router.get("/test")
async def test_chat_endpoint():
    """
    Test endpoint to verify chat API is working.
    """
    try:
        # Try to initialize chat service
        chat_service = get_chat_service()
        
        return {
            "status": "operational",
            "services": {
                "openai": chat_service.client is not None,
                "embeddings": chat_service.embeddings_service is not None,
                "pinecone": chat_service.pinecone_service is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Debug endpoint for testing
@router.post("/test/simple")
async def test_simple_chat():
    """
    Simple test endpoint that doesn't require a project.
    Useful for testing the chat service is working.
    """
    try:
        chat_service = get_chat_service()
        
        # Test with a simple query
        test_query = "What is machine learning?"
        
        # Generate a simple response without context
        response_data = chat_service.generate_response(
            query=test_query,
            context_chunks=[],  # No context
            conversation_history=None
        )
        
        return {
            "success": response_data['success'],
            "query": test_query,
            "response": response_data.get('response', 'No response generated'),
            "metadata": response_data.get('metadata', {})
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }