"""Session timeout management for OPETSE-30.

Implements automatic session timeout after 15 minutes of inactivity (SRS S27).
Tracks active sessions server-side and validates session expiration.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from app.core.config import settings

# In-memory session store: {user_id: session_data}
_active_sessions: Dict[str, Dict[str, Any]] = {}


def create_session(user_id: str, email: str, role: str, token: str) -> Dict[str, Any]:
    """Create a new session for a user.
    
    Args:
        user_id: User ID
        email: User email
        role: User role
        token: JWT token
        
    Returns:
        Session data dictionary
    """
    session_data = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "token": token,
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "timeout_minutes": settings.SESSION_TIMEOUT_MINUTES,
    }
    _active_sessions[user_id] = session_data
    return session_data


def update_session_activity(user_id: str) -> bool:
    """Update the last activity timestamp for a session.
    
    Extends the session timeout by updating the last_activity timestamp.
    Only updates if session exists and is not expired.
    
    Args:
        user_id: User ID
        
    Returns:
        True if updated successfully, False if session doesn't exist or is expired
    """
    if user_id not in _active_sessions:
        return False
    
    session = _active_sessions[user_id]
    
    # Check if already expired
    if is_session_expired(user_id):
        return False
    
    session["last_activity"] = datetime.utcnow()
    return True


def is_session_expired(user_id: str) -> bool:
    """Check if a user's session has expired.
    
    Session expires if:
    1. Session doesn't exist, or
    2. Time since last activity exceeds SESSION_TIMEOUT_MINUTES
    
    Args:
        user_id: User ID
        
    Returns:
        True if session is expired or doesn't exist, False otherwise
    """
    if user_id not in _active_sessions:
        return True
    
    session = _active_sessions[user_id]
    timeout_delta = timedelta(minutes=session["timeout_minutes"])
    time_since_activity = datetime.utcnow() - session["last_activity"]
    
    return time_since_activity > timeout_delta


def get_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Get session data for a user if it exists and hasn't expired.
    
    Args:
        user_id: User ID
        
    Returns:
        Session data if valid, None if doesn't exist or is expired
    """
    if is_session_expired(user_id):
        # Clean up expired session
        _active_sessions.pop(user_id, None)
        return None
    
    return _active_sessions.get(user_id)


def destroy_session(user_id: str) -> bool:
    """Destroy a user's session (logout).
    
    Args:
        user_id: User ID
        
    Returns:
        True if session was destroyed, False if it didn't exist
    """
    if user_id in _active_sessions:
        del _active_sessions[user_id]
        return True
    return False


def get_session_info(user_id: str) -> Optional[Dict[str, Any]]:
    """Get information about a session without checking expiration.
    
    Returns raw session data for inspection/debugging. Does not modify session.
    
    Args:
        user_id: User ID
        
    Returns:
        Session data dictionary or None if doesn't exist
    """
    return _active_sessions.get(user_id)


def cleanup_expired_sessions() -> int:
    """Remove all expired sessions from the store.
    
    Scans all active sessions and removes those that have expired.
    Useful for periodic cleanup to prevent memory leaks.
    
    Returns:
        Number of sessions cleaned up
    """
    expired_user_ids = []
    
    for user_id in list(_active_sessions.keys()):
        if is_session_expired(user_id):
            expired_user_ids.append(user_id)
    
    for user_id in expired_user_ids:
        _active_sessions.pop(user_id, None)
    
    return len(expired_user_ids)


def get_all_active_sessions() -> Dict[int, Dict[str, Any]]:
    """Get all currently active (non-expired) sessions.
    
    Returns a copy to prevent external modification of the session store.
    
    Returns:
        Dictionary mapping user_id to session data for all active sessions
    """
    active = {}
    for user_id in list(_active_sessions.keys()):
        if not is_session_expired(user_id):
            active[user_id] = _active_sessions[user_id].copy()
    
    return active


def clear_all_sessions() -> int:
    """Clear all sessions (for testing/maintenance).
    
    Returns:
        Number of sessions cleared
    """
    count = len(_active_sessions)
    _active_sessions.clear()
    return count
