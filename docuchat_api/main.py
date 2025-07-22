import os
import uvicorn
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Optional
# Remove tomllib and pyproject.toml logic
try:
    from importlib.metadata import version as get_version
except ImportError:
    from importlib_metadata import version as get_version

def get_app_version():
    try:
        return get_version("docuchat-api")
    except Exception:
        return "unknown"

from .api.router import api_router
from .session import session_manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    db_path = os.environ.get('DOCUCHAT_DB_PATH')
    if not db_path:
        raise RuntimeError("Database path not set. Please start the server with --database <path>.")
    app.state.db_path = db_path
    yield

# Create FastAPI application
app = FastAPI(
    title="DocuChat API",
    description="A Python REST API for DocuChat that enables document chat with RAG",
    version=get_app_version(),
    lifespan=lifespan,
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
    "/api/session/config/",
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
       any(path.startswith(prefix) for prefix in ["/api/session/update/", "/api/session/expire/", "/api/session/config/"]):
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
        "version": app.version,
        "description": app.description
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {"status": "healthy"}


def main():
    import argparse
    import uvicorn
    parser = argparse.ArgumentParser(description="Run the DocuChat API server.")
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind the server to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    parser.add_argument('--log-level', type=str, default='info', help='Uvicorn log level')
    parser.add_argument('--database', type=str, required=True, help='Path to the SQLite database file')
    args = parser.parse_args()

    # Store db_path in a file for uvicorn reloads (since app.state is not preserved)
    import os
    os.environ['DOCUCHAT_DB_PATH'] = args.database

    uvicorn.run(
        "docuchat_api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

# Set db_path on app startup
# The lifespan handler now manages this.

if __name__ == "__main__":
    main() 