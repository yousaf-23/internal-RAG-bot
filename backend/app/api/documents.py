"""
Document Management API Endpoints
----------------------------------
This module handles:
1. File uploads from the frontend
2. Document processing initiation
3. Document status tracking
4. Document deletion

Author: RAG Bot Development
Date: 2024
"""

import os
import uuid
import shutil
from typing import List, Optional
from datetime import datetime
from pathlib import Path

# FastAPI imports
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    UploadFile, 
    File,
    BackgroundTasks
)
from fastapi.responses import FileResponse

# SQLAlchemy for database operations
from sqlalchemy.orm import Session
from sqlalchemy import and_

# Import our modules
from app.database import get_db, Document as DocumentModel, Project, DocumentChunk
from app.models import DocumentResponse, DocumentStatus, SuccessResponse
from app.config import settings
# from app.document_processor import DocumentProcessor  # We'll create this next

# Create router for document endpoints
router = APIRouter()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(exist_ok=True)
print(f"[Documents API] Upload directory: {UPLOAD_DIR.absolute()}")

# Initialize document processor (we'll create this class next)
# doc_processor = DocumentProcessor()  # Uncomment when we create the processor

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_file_type(filename: str) -> bool:
    """
    Validate if the uploaded file type is allowed.
    
    Args:
        filename: Name of the uploaded file
        
    Returns:
        True if file type is allowed, False otherwise
    """
    # Extract file extension
    file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    # Check against allowed extensions
    allowed = file_ext in settings.allowed_extensions
    
    print(f"[Documents API] File validation: {filename}")
    print(f"  Extension: {file_ext}")
    print(f"  Allowed: {allowed}")
    print(f"  Allowed types: {settings.allowed_extensions}")
    
    return allowed

def validate_file_size(file_size: int) -> bool:
    """
    Validate if the file size is within limits.
    
    Args:
        file_size: Size of the file in bytes
        
    Returns:
        True if size is acceptable, False otherwise
    """
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
    
    print(f"[Documents API] Size validation:")
    print(f"  File size: {file_size / 1024 / 1024:.2f} MB")
    print(f"  Max allowed: {settings.max_file_size_mb} MB")
    print(f"  Valid: {file_size <= max_size_bytes}")
    
    return file_size <= max_size_bytes

def save_upload_file(upload_file: UploadFile, destination: Path) -> int:
    """
    Save an uploaded file to disk.
    
    Args:
        upload_file: The file uploaded by the user
        destination: Where to save the file
        
    Returns:
        File size in bytes
    """
    try:
        print(f"[Documents API] Saving file to: {destination}")
        
        # Open destination file in binary write mode
        with destination.open("wb") as buffer:
            # Copy file contents
            shutil.copyfileobj(upload_file.file, buffer)
        
        # Get file size
        file_size = destination.stat().st_size
        print(f"[Documents API] File saved successfully: {file_size} bytes")
        
        return file_size
        
    except Exception as e:
        print(f"[Documents API] Error saving file: {e}")
        # Clean up partial file if it exists
        if destination.exists():
            destination.unlink()
        raise


async def process_document_background(document_id: str, file_path: str, db: Session):
    """
    Background task to process a document after upload.
    Complete pipeline with Pinecone integration!
    
    Processing pipeline:
    1. Extract text from document
    2. Create chunks
    3. Generate embeddings for each chunk
    4. Store embeddings in Pinecone ← NEW!
    5. Store chunks in PostgreSQL
    6. Mark document as ready and indexed
    
    Args:
        document_id: ID of the document in database
        file_path: Path to the uploaded file
        db: Database session
    """
    print(f"\n{'='*70}")
    print(f"[Background Task] Starting processing for document: {document_id}")
    print(f"[Background Task] File path: {file_path}")
    print(f"{'='*70}")
    
    try:
        # Step 1: Update status to processing
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
        
        if not document:
            print(f"[Background Task] ❌ Document {document_id} not found!")
            return
            
        document.status = "processing"
        db.commit()
        print("[Background Task] Status updated to 'processing'")
        
        # Step 2: Initialize document processor
        from app.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Step 3: Process the document (extract text and create chunks)
        print("[Background Task] Starting text extraction...")
        result = processor.process_document(file_path)
        
        if result['success']:
            print(f"[Background Task] ✅ Text extraction successful")
            
            # Extract metadata and chunks
            metadata = result.get('metadata', {})
            chunks = result.get('chunks', [])
            
            # Update document with extracted information
            document.page_count = metadata.get('page_count')
            document.word_count = metadata.get('word_count')
            document.chunk_count = len(chunks)
            
            print(f"[Background Task] Document stats:")
            print(f"  - Pages: {document.page_count}")
            print(f"  - Words: {document.word_count}")
            print(f"  - Chunks: {document.chunk_count}")
            
            # Step 4: Initialize embeddings service
            print("\n[Background Task] Initializing embeddings service...")
            from app.embeddings_service import EmbeddingsService
            
            embeddings_generated = False
            vectors_stored = False
            
            try:
                embeddings_service = EmbeddingsService()
                
                # Step 5: Generate embeddings for all chunks
                print(f"[Background Task] Generating embeddings for {len(chunks)} chunks...")
                
                # Extract just the text from chunks
                chunk_texts = [chunk['text'] for chunk in chunks]
                
                # Generate embeddings in batches
                embeddings = embeddings_service.generate_embeddings_batch(
                    chunk_texts, 
                    batch_size=20  # Process 20 chunks at a time
                )
                
                # Check if embeddings were generated successfully
                successful_embeddings = sum(1 for e in embeddings if e is not None)
                print(f"[Background Task] Generated {successful_embeddings}/{len(chunks)} embeddings")
                
                if successful_embeddings > 0:
                    embeddings_generated = True
                    
                    # Step 6: Store embeddings in Pinecone
                    print("\n[Background Task] Storing embeddings in Pinecone...")
                    from app.pinecone_service import PineconeService
                    
                    try:
                        pinecone_service = PineconeService()
                        
                        # Add document metadata to chunks for Pinecone
                        for chunk in chunks:
                            chunk['document_id'] = document_id
                            chunk['filename'] = document.filename
                            chunk['project_id'] = document.project_id
                        
                        # Store in Pinecone
                        pinecone_result = pinecone_service.upsert_embeddings(
                            document_id=document_id,
                            chunks=chunks,
                            embeddings=embeddings
                        )
                        
                        if pinecone_result['success']:
                            vectors_stored = True
                            print(f"[Background Task] ✅ Stored {pinecone_result['upserted']} vectors in Pinecone")
                            print(f"[Background Task] Total vectors in index: {pinecone_result['total_vectors_in_index']}")
                        else:
                            print(f"[Background Task] ⚠️  Pinecone storage failed: {pinecone_result.get('error')}")
                            
                    except Exception as e:
                        print(f"[Background Task] ⚠️  Pinecone error (non-fatal): {e}")
                        # Continue even if Pinecone fails - document is still useful
                
                # Step 7: Store chunks in PostgreSQL database
                from app.database import DocumentChunk
                
                chunks_stored = 0
                for i, chunk_data in enumerate(chunks):
                    chunk = DocumentChunk(
                        id=f"{document_id}_chunk_{chunk_data['chunk_index']}",
                        document_id=document_id,
                        chunk_index=chunk_data['chunk_index'],
                        chunk_text=chunk_data['text'],
                        char_start=chunk_data.get('start_char'),
                        char_end=chunk_data.get('start_char', 0) + chunk_data['char_count']
                    )
                    
                    # Store metadata about embedding
                    if embeddings_generated and i < len(embeddings) and embeddings[i] is not None:
                        chunk.embedding_model = embeddings_service.embedding_model
                        chunks_stored += 1
                    
                    db.add(chunk)
                
                db.commit()
                print(f"[Background Task] ✅ Stored {chunks_stored} chunks in PostgreSQL")
                
                # Step 8: Calculate final cost
                total_cost = (embeddings_service.total_tokens_used / 1000) * embeddings_service.cost_per_1k_tokens
                print(f"[Background Task] Total embedding cost: ${total_cost:.6f}")
                
            except Exception as e:
                print(f"[Background Task] ⚠️  Embeddings/Pinecone error: {e}")
                # Continue without embeddings - document can still be used
            
            # Step 9: Update document status
            document.status = "ready"
            document.processed_at = datetime.utcnow()
            document.indexed = vectors_stored  # True if vectors stored in Pinecone
            db.commit()
            
            # Print final status
            status_msg = "✅ Document processed successfully!"
            if vectors_stored:
                status_msg += " (Fully indexed in Pinecone)"
            elif embeddings_generated:
                status_msg += " (Embeddings generated, Pinecone storage failed)"
            else:
                status_msg += " (Text extracted, no embeddings)"
            
            print(f"[Background Task] {status_msg}")
            
        else:
            # Processing failed
            error_msg = result.get('error', 'Unknown error')
            print(f"[Background Task] ❌ Processing failed: {error_msg}")
            
            document.status = "error"
            document.error_message = error_msg
            db.commit()
        
    except Exception as e:
        print(f"[Background Task] ❌ Unexpected error: {e}")
        
        # Print detailed error for debugging
        import traceback
        print("\n[Background Task] Detailed error:")
        traceback.print_exc()
        
        # Update document with error status
        try:
            document = db.query(DocumentModel).filter(
                DocumentModel.id == document_id
            ).first()
            if document:
                document.status = "error"
                document.error_message = str(e)
                db.commit()
        except:
            pass  # Don't fail the background task
    
    finally:
        print(f"[Background Task] Completed processing for {document_id}")
        print(f"{'='*70}\n")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    project_id: str,
    background_tasks: BackgroundTasks,  # For async processing
    file: UploadFile = File(...),  # The uploaded file
    db: Session = Depends(get_db)
):
    """
    Upload a document to a project.
    
    This endpoint:
    1. Validates the file type and size
    2. Saves the file to disk
    3. Creates a database record
    4. Initiates background processing
    
    Args:
        project_id: Which project to add the document to
        file: The uploaded file
        background_tasks: FastAPI background task runner
        db: Database session
        
    Returns:
        Document information including upload status
    """
    print(f"\n[Documents API] Upload request received")
    print(f"  Project ID: {project_id}")
    print(f"  Filename: {file.filename}")
    print(f"  Content Type: {file.content_type}")
    
    try:
        # Step 1: Verify project exists
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            print(f"[Documents API] ❌ Project {project_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found"
            )
        
        # Step 2: Validate file type
        if not validate_file_type(file.filename):
            print(f"[Documents API] ❌ Invalid file type: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
            )
        
        # Step 3: Generate unique document ID and file path
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        file_extension = file.filename.split('.')[-1].lower()
        
        # Create project directory if it doesn't exist
        project_dir = UPLOAD_DIR / project_id
        project_dir.mkdir(exist_ok=True)
        
        # Create unique filename to avoid collisions
        safe_filename = f"{document_id}.{file_extension}"
        file_path = project_dir / safe_filename
        
        print(f"[Documents API] Generated document ID: {document_id}")
        print(f"[Documents API] File will be saved as: {file_path}")
        
        # Step 4: Save the file
        file_size = save_upload_file(file, file_path)
        
        # Step 5: Validate file size (after saving to get actual size)
        if not validate_file_size(file_size):
            # Delete the file if too large
            file_path.unlink()
            print(f"[Documents API] ❌ File too large: {file_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum of {settings.max_file_size_mb} MB"
            )
        
        # Step 6: Create database record
        new_document = DocumentModel(
            id=document_id,
            project_id=project_id,
            filename=file.filename,
            file_type=file_extension,
            file_path=str(file_path),
            size=file_size,
            status="uploading",
            uploaded_at=datetime.utcnow()
        )
        
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
        
        print(f"[Documents API] ✅ Document record created in database")
        
        # Step 7: Start background processing
        # This allows the API to return immediately while processing happens
        background_tasks.add_task(
            process_document_background,
            document_id,
            str(file_path),
            db
        )
        
        print(f"[Documents API] ✅ Background processing initiated")
        
        # Step 8: Return response
        return DocumentResponse(
            id=new_document.id,
            project_id=new_document.project_id,
            filename=new_document.filename,
            file_type=new_document.file_type,
            uploaded_at=new_document.uploaded_at,
            size=new_document.size,
            status=new_document.status,
            page_count=None,  # Will be updated during processing
            error_message=None
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"[Documents API] ❌ Unexpected error: {e}")
        db.rollback()
        
        # Clean up file if it was saved
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get information about a specific document.
    
    Args:
        document_id: The document's unique identifier
        db: Database session
        
    Returns:
        Document details including processing status
    """
    print(f"[Documents API] Getting document: {document_id}")
    
    try:
        # Query document from database
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
        
        if not document:
            print(f"[Documents API] ❌ Document not found: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found"
            )
        
        print(f"[Documents API] ✅ Found document: {document.filename}")
        
        return DocumentResponse(
            id=document.id,
            project_id=document.project_id,
            filename=document.filename,
            file_type=document.file_type,
            uploaded_at=document.uploaded_at,
            size=document.size,
            status=document.status,
            page_count=document.page_count,
            error_message=document.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Documents API] ❌ Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )

@router.get("/project/{project_id}", response_model=List[DocumentResponse])
async def get_project_documents(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all documents for a specific project.
    
    Args:
        project_id: The project's unique identifier
        db: Database session
        
    Returns:
        List of documents in the project
    """
    print(f"[Documents API] Getting documents for project: {project_id}")
    
    try:
        # Verify project exists
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            print(f"[Documents API] ❌ Project not found: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found"
            )
        
        # Get all documents for this project
        documents = db.query(DocumentModel).filter(
            DocumentModel.project_id == project_id
        ).order_by(DocumentModel.uploaded_at.desc()).all()
        
        print(f"[Documents API] ✅ Found {len(documents)} documents")
        
        # Convert to response models
        return [
            DocumentResponse(
                id=doc.id,
                project_id=doc.project_id,
                filename=doc.filename,
                file_type=doc.file_type,
                uploaded_at=doc.uploaded_at,
                size=doc.size,
                status=doc.status,
                page_count=doc.page_count,
                error_message=doc.error_message
            )
            for doc in documents
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Documents API] ❌ Error getting project documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project documents: {str(e)}"
        )

@router.delete("/{document_id}", response_model=SuccessResponse)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and its associated data.
    
    This will:
    1. Delete the file from disk
    2. Delete chunks from database
    3. Delete vectors from Pinecone (when implemented)
    4. Delete document record from database
    
    Args:
        document_id: The document to delete
        db: Database session
        
    Returns:
        Success message
    """
    print(f"[Documents API] Deleting document: {document_id}")
    
    try:
        # Find document
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
        
        if not document:
            print(f"[Documents API] ❌ Document not found: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found"
            )
        
        # Step 1: Delete file from disk
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
                print(f"[Documents API] ✅ Deleted file: {document.file_path}")
            except Exception as e:
                print(f"[Documents API] ⚠️  Could not delete file: {e}")
        
        # Step 2: Delete from Pinecone (TODO: implement when we add Pinecone)
        # if document.indexed:
        #     delete_from_pinecone(document_id)
        
        # Step 3: Delete document (chunks will cascade delete)
        filename = document.filename
        db.delete(document)
        db.commit()
        
        print(f"[Documents API] ✅ Document deleted: {filename}")
        
        return SuccessResponse(
            success=True,
            message=f"Document '{filename}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Documents API] ❌ Error deleting document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the processing status of a document.
    
    This is useful for the frontend to poll and check
    if document processing is complete.
    
    Args:
        document_id: The document to check
        db: Database session
        
    Returns:
        Status information
    """
    print(f"[Documents API] Checking status for: {document_id}")
    
    try:
        document = db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found"
            )
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "status": document.status,
            "error_message": document.error_message,
            "uploaded_at": document.uploaded_at,
            "processed_at": document.processed_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Documents API] ❌ Error getting status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status"
        )

# Debug endpoint for testing
if settings.debug_mode:
    @router.get("/test/list-uploads")
    async def list_uploaded_files():
        """
        Debug endpoint to list all uploaded files on disk.
        Only available in debug mode.
        """
        files = []
        for project_dir in UPLOAD_DIR.iterdir():
            if project_dir.is_dir():
                for file_path in project_dir.iterdir():
                    if file_path.is_file():
                        files.append({
                            "project": project_dir.name,
                            "filename": file_path.name,
                            "size": file_path.stat().st_size,
                            "path": str(file_path)
                        })
        
        return {
            "upload_directory": str(UPLOAD_DIR.absolute()),
            "total_files": len(files),
            "files": files
        }