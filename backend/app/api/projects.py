"""
Project management API endpoints.
Handles creating, reading, updating, and deleting projects.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from datetime import datetime
from app.pinecone_service import PineconeService


# Import our database models and schemas
from app.database import get_db, Project, Document
from app.models import (
    ProjectCreate, 
    ProjectResponse, 
    ProjectUpdate,
    SuccessResponse
)

# Create a router for project endpoints
# This groups all project-related endpoints together
router = APIRouter()

@router.get("", response_model=List[ProjectResponse])
async def get_all_projects(
    db: Session = Depends(get_db)  # Inject database session
):
    """
    Get all projects with their file counts.
    
    Returns:
        List of all projects in the database
    """
    try:
        # Query all projects from database
        projects = db.query(Project).all()
        
        # Add file count for each project
        project_responses = []
        for project in projects:
            # Count documents for this project
            file_count = db.query(Document).filter(
                Document.project_id == project.id
            ).count()
            
            # Create response with file count
            response = ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                updated_at=project.updated_at,
                file_count=file_count
            )
            project_responses.append(response)
        
        print(f"[API] Retrieved {len(project_responses)} projects")
        return project_responses
        
    except Exception as e:
        print(f"[API] Error getting projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,  # Request body (JSON)
    db: Session = Depends(get_db)
):
    """
    Create a new project.
    
    Args:
        project_data: Project name and description
        
    Returns:
        Created project with generated ID
    """
    try:
        # Generate unique ID for the project
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        
        # Create database model instance
        new_project = Project(
            id=project_id,
            name=project_data.name,
            description=project_data.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add to database
        db.add(new_project)
        db.commit()
        db.refresh(new_project)  # Get the created object
        
        print(f"[API] Created project: {new_project.name} (ID: {project_id})")
        
        # Return response
        return ProjectResponse(
            id=new_project.id,
            name=new_project.name,
            description=new_project.description,
            created_at=new_project.created_at,
            updated_at=new_project.updated_at,
            file_count=0  # New project has no files
        )
        
    except Exception as e:
        db.rollback()  # Undo changes if error
        print(f"[API] Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,  # Path parameter from URL
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID.
    
    Args:
        project_id: The project's unique identifier
        
    Returns:
        Project details with file count
    """
    try:
        # Find project in database
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found"
            )
        
        # Get file count
        file_count = db.query(Document).filter(
            Document.project_id == project_id
        ).count()
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            file_count=file_count
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"[API] Error getting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}"
        )

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a project's name or description.
    
    Args:
        project_id: The project to update
        project_update: New name and/or description
        
    Returns:
        Updated project details
    """
    try:
        # Find project
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found"
            )
        
        # Update fields if provided
        if project_update.name is not None:
            project.name = project_update.name
        if project_update.description is not None:
            project.description = project_update.description
        
        project.updated_at = datetime.utcnow()
        
        # Save changes
        db.commit()
        db.refresh(project)
        
        # Get file count
        file_count = db.query(Document).filter(
            Document.project_id == project_id
        ).count()
        
        print(f"[API] Updated project: {project.name}")
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            file_count=file_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[API] Error updating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a project and all its documents.
    
    Args:
        project_id: The project to delete
        
    Returns:
        Success message
    """
    try:
        # Find project
        project = db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found"
            )
        
        project_name = project.name
        
        # Delete project (cascade will delete documents)
        db.delete(project)
        db.commit()
        
        print(f"[API] Deleted project from DB: {project_name}")

        # Deleteing project namespace from Pinecone.
        pinecone_service = PineconeService()

        pinecone_service.delete_namespace(namespace=project_id)

        print(f"[API] Deleted Project '{project_name}' entirely")
        
        return SuccessResponse(
            success=True,
            message=f"Project '{project_name}' deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[API] Error deleting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )