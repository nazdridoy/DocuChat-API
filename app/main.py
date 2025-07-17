import os
import uvicorn
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Optional

from .api.router import api_router
from .session import session_manager

# Create FastAPI application
app = FastAPI(
    title="DocuChat API",
    description="A Python REST API for DocuChat that enables document chat with RAG",
    version="0.1.0",
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can be set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths that don't require authentication
PUBLIC_PATHS = [
    "/",
    "/health",
    "/api/session/create",
    "/api/session/list",
    "/api/session/update/",
    "/api/session/expire/",
    "/docs",
    "/redoc",
    "/openapi.json"
]

# Add authentication middleware
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    """Middleware to authenticate requests using session ID header"""
    path = request.url.path
    
    # Skip authentication for public paths
    if any(path == public_path for public_path in PUBLIC_PATHS) or \
       any(path.startswith(prefix) for prefix in ["/api/session/update/", "/api/session/expire/"]):
        return await call_next(request)
    
    # Check for session ID header
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return JSONResponse(
            status_code=401, 
            content={"detail": "X-Session-ID header required"}
        )
    
    # Validate session
    session = session_manager.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=401, 
            content={"detail": "Invalid session ID"}
        )
    
    # Proceed with the request
    return await call_next(request)


# Add request/response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and responses with timing information"""
    start_time = time.time()
    
    # Get request details
    method = request.method
    url = request.url.path
    
    # Process request
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Log request details
        process_time = time.time() - start_time
        print(f"{method} {url} - {status_code} - {process_time:.4f}s")
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        print(f"{method} {url} - ERROR: {str(e)} - {process_time:.4f}s")
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


# Include API router
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint that returns basic API information"""
    return {
        "name": "DocuChat API",
        "version": "0.1.0",
        "description": "A Python REST API for document chat with RAG"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "healthy"}


# Run the application when executed directly
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    ) 