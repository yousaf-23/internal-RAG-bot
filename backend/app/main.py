"""
Main FastAPI application entry point.
This file sets up the FastAPI app, middleware, and includes all routers.
FIXED: Better error handling for configuration import.
"""

import sys
import os

# Add debugging for import issues
print(f"[Main] Python path: {sys.path}")
print(f"[Main] Current directory: {os.getcwd()}")
print(f"[Main] Loading application...")

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from contextlib import asynccontextmanager
    import time
    import logging
    from typing import Dict, Any
    from sqlalchemy import text  # Add this import for SQL queries

    # Import our modules with error handling
    from app.config import settings
    from app.database import init_db, test_connection, engine
    from app.models import HealthStatus

    # Import API routers (we'll create these next)
    # from app.api import projects, documents, chat

    print("[Main] ✅ All imports successful")

except ImportError as e:
    print(f"[Main] ❌ Import error: {e}")
    print("\nDebugging steps:")
    print("1. Make sure you're in the backend directory")
    print("2. Check that venv is activated: (venv) should appear in prompt")
    print("3. Verify all files exist in app/ directory")
    sys.exit(1)

# Import API routers (we'll create these next)
from app.api import projects, documents, chat


# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug_mode else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifespan manager (replaces deprecated startup/shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Runs code at startup and shutdown.
    """
    # Startup
    logger.info("="*60)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info("="*60)
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        
        # Test connection
        if test_connection():
            logger.info("✅ Database ready")
        else:
            logger.error("❌ Database connection failed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise - allow app to start for debugging
    
    # Initialize Pinecone (we'll implement this later)
    try:
        logger.info("Initializing Pinecone...")
        # TODO: Initialize Pinecone connection
        logger.info("✅ Pinecone ready (mock)")
    except Exception as e:
        logger.error(f"Pinecone initialization failed: {e}")
    
    # Test OpenAI connection
    try:
        logger.info("Testing OpenAI connection...")
        # TODO: Test OpenAI API
        logger.info("✅ OpenAI ready (mock)")
    except Exception as e:
        logger.error(f"OpenAI connection failed: {e}")
    
    logger.info("="*60)
    logger.info("✅ Application started successfully!")
    logger.info(f"📍 API documentation: http://localhost:8000/docs")
    logger.info("="*60)
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down application...")
    # Close database connections
    engine.dispose()
    logger.info("✅ Application shut down cleanly")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Internal RAG Bot API for document Q&A",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    lifespan=lifespan  # Use lifespan manager
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],  # Allow React frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time to response headers.
    Useful for performance monitoring.
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
    
    return response

# Exception handler for better error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unhandled errors.
    Returns consistent error format.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug_mode else "An unexpected error occurred"
        }
    )

# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint - returns API information.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check() -> HealthStatus:
    """
    Health check endpoint for monitoring.
    Returns status of all services.
    """
    health = HealthStatus(
        status="healthy",
        version=settings.app_version,
        services={}
    )
    
    # Check database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health.services["database"] = True
    except Exception as e:
        health.services["database"] = False
        health.status = "degraded"
        logger.error(f"Database health check failed: {e}")
    
    # Check Pinecone (mock for now)
    try:
        # TODO: Add actual Pinecone health check
        health.services["pinecone"] = True
    except Exception as e:
        health.services["pinecone"] = False
        health.status = "degraded"
    
    # Check OpenAI (mock for now)
    try:
        # TODO: Add actual OpenAI health check
        health.services["openai"] = True
    except Exception as e:
        health.services["openai"] = False
        health.status = "degraded"
    
    return health

# Include API routers
# We'll uncomment these as we create the router files
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

# Test endpoints for debugging
if settings.debug_mode:
    @app.get("/test/db", tags=["Test"])
    async def test_database():
        """Test database connection."""
        try:
            from app.database import get_db
            from sqlalchemy import text
            
            db = next(get_db())
            result = db.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            db.close()
            
            return {
                "success": True,
                "database": db_name,
                "message": "Database connection successful"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/test/echo/{message}", tags=["Test"])
    async def echo(message: str):
        """Echo test endpoint."""
        return {"echo": message, "timestamp": time.time()}

# Run the application (for development only)
if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info" if settings.debug_mode else "warning"
    )