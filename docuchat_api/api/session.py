from fastapi import APIRouter, HTTPException, Request, Body, Depends
from typing import Dict, Any, List, Optional
import asyncio
import os
import traceback
from ..config import validate_session_config
from ..session import session_manager
from ..db.engine import test_db_connection

router = APIRouter(
    prefix="/session",
    tags=["session"],
    responses={404: {"description": "Not found"}},
)


@router.post("/create")
async def create_session(request: Request, config: Dict[str, Any] = Body(...)):
    """
    Create a new session with the provided configuration (db_path is now internal)
    Args:
        config: Session configuration dictionary (no db_path)
    Returns:
        Dictionary with session ID
    """
    try:
        # Validate configuration (no db_path)
        validated_config = validate_session_config(config)

        # Test database connection and get embedding dimensions using global db_path
        db_path = request.app.state.db_path
        from ..db.engine import test_db_connection
        DEFAULT_EMBEDDING_DIMENSIONS = 384
        try:
            print(f"Testing database connection to: {db_path}")
            db_dims = await test_db_connection(db_path, validated_config.get("embedding_dimensions"))
        except Exception as e:
            print(f"Database connection test failed: {e}")
            import traceback; traceback.print_exc()
            # Continue anyway with default dimensions
            print(f"Using default embedding dimensions: {DEFAULT_EMBEDDING_DIMENSIONS}")
            db_dims = DEFAULT_EMBEDDING_DIMENSIONS
        # Set dimensions in config
        validated_config["embedding_dimensions"] = db_dims

        # Create session
        session_id = session_manager.create_session(validated_config)
        return {"session_id": session_id, "vector_search": True}
    except Exception as e:
        import traceback; traceback.print_exc()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
async def list_sessions():
    """
    List all active sessions
    
    Returns:
        Dictionary of session IDs to session metadata
    """
    return session_manager.list_sessions()


@router.post("/update/{session_id}")
async def update_session(request: Request, session_id: str, config: Dict[str, Any] = Body(...)):
    """
    Update an existing session with new configuration (db_path is now internal)
    Args:
        session_id: Session ID to update
        config: New configuration dictionary (no db_path)
    Returns:
        Dictionary with success status
    """
    if not session_manager.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        validated_config = validate_session_config(config)
        # Optionally, test DB connection as above if needed
        success = session_manager.update_session(session_id, validated_config)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/expire/{session_id}")
async def expire_session(session_id: str):
    """
    Delete an existing session
    
    Args:
        session_id: Session ID to delete
        
    Returns:
        Dictionary with success status
    """
    if not session_manager.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
        
    success = session_manager.delete_session(session_id)
    return {"success": success}


@router.get("/config/{session_id}")
async def get_session_config_endpoint(session_id: str):
    """
    Public endpoint to view the config of a session by session_id
    """
    config = session_manager.get_config(session_id)
    if not config:
        raise HTTPException(status_code=404, detail="Session not found")
    return config


def get_session_config(session_id: str) -> Dict[str, Any]:
    """
    Get session configuration for dependency injection
    
    Args:
        session_id: Session ID
        
    Returns:
        Session configuration dictionary
        
    Raises:
        HTTPException: If session ID is invalid
    """
    config = session_manager.get_config(session_id)
    if not config:
        raise HTTPException(status_code=401, detail="Invalid session ID")
    return config 