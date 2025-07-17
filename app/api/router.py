from fastapi import APIRouter, Request, Depends, Header, HTTPException
from typing import Optional
from . import session

# Main router that will include all other routers
api_router = APIRouter(prefix="/api")


# Session header dependency function
async def validate_session(x_session_id: Optional[str] = Header(None)) -> str:
    """
    Validate session ID from X-Session-ID header
    
    Args:
        x_session_id: Session ID from header
        
    Returns:
        Validated session ID
        
    Raises:
        HTTPException: If session ID is missing or invalid
    """
    if not x_session_id:
        raise HTTPException(status_code=401, detail="X-Session-ID header is required")
    return x_session_id


# Include all routers
api_router.include_router(session.router)

# Add more routers here as they're created
# api_router.include_router(documents.router)
# api_router.include_router(chat.router) 