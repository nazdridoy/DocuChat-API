import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


class SessionManager:
    """
    Session management for DocuChat API
    Manages user sessions and their configurations
    """
    
    def __init__(self, session_timeout_minutes: int = 60):
        """
        Initialize SessionManager with configurable timeout
        
        Args:
            session_timeout_minutes: Minutes after which inactive sessions expire
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout_minutes = session_timeout_minutes
        self.cleanup_task = None
    
    def create_session(self, config: Dict[str, Any]) -> str:
        """
        Create a new session with the provided configuration
        
        Args:
            config: Session configuration dictionary
            
        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "config": config,
            "created_at": datetime.now(),
            "last_accessed": datetime.now()
        }
        
        # Start cleanup task if not running
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID and update last accessed time
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session object or None if not found
        """
        if session_id in self.sessions:
            self.sessions[session_id]["last_accessed"] = datetime.now()
            return self.sessions[session_id]
        return None
    
    def get_config(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration dictionary for a session
        
        Args:
            session_id: Session ID to retrieve config for
            
        Returns:
            Configuration dictionary or None if session not found
        """
        session = self.get_session(session_id)
        if session:
            return session["config"]
        return None
    
    def update_session(self, session_id: str, config: Dict[str, Any]) -> bool:
        """
        Update an existing session with new configuration
        
        Args:
            session_id: Session ID to update
            config: New configuration dictionary
            
        Returns:
            True if session was updated, False otherwise
        """
        if session_id in self.sessions:
            self.sessions[session_id]["config"] = config
            self.sessions[session_id]["last_accessed"] = datetime.now()
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if session was deleted, False otherwise
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active sessions with basic information
        
        Returns:
            Dictionary of session IDs to session metadata
        """
        return {
            sid: {
                "created_at": session["created_at"],
                "last_accessed": session["last_accessed"]
            } for sid, session in self.sessions.items()
        }
    
    async def _cleanup_expired_sessions(self):
        """
        Periodically clean up expired sessions
        This is an internal method that runs as a background task
        """
        while True:
            await asyncio.sleep(60)  # Check every minute
            current_time = datetime.now()
            expired_sessions = []
            
            for sid, session in self.sessions.items():
                if (current_time - session["last_accessed"]) > timedelta(minutes=self.session_timeout_minutes):
                    expired_sessions.append(sid)
            
            for sid in expired_sessions:
                print(f"Session {sid} expired and removed")
                del self.sessions[sid]
                
            if not self.sessions:
                break  # Stop cleanup if no sessions remain


# Create global session manager instance
session_manager = SessionManager() 