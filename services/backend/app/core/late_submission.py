"""Late submission management for OPETSE-10.

Allows instructors to grant late submission permission for evaluation forms
in special cases, offering flexibility beyond the standard deadline (SRS S7).
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from app.core.config import settings
from app.core.supabase import supabase

# In-memory late submission permissions store
# Format: {form_id: {user_id: permission_data}}
_late_submission_permissions: Dict[int, Dict[str, Dict[str, Any]]] = {}


class LateSubmissionPermission(BaseModel):
    """Model for late submission permission."""
    form_id: int
    user_id: str
    allowed_until: str  # ISO format datetime
    granted_by: str  # Instructor user_id
    reason: Optional[str] = None
    granted_at: str  # ISO format datetime
    is_active: bool = True


def grant_late_submission(
    form_id: int,
    user_id: str,
    allowed_until: str,
    granted_by: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """Grant late submission permission to a user for a form.
    
    Args:
        form_id: ID of the evaluation form
        user_id: ID of the user granted permission
        allowed_until: ISO format datetime when late submission expires
        granted_by: ID of instructor granting permission
        reason: Optional reason for late submission
        
    Returns:
        Permission data dictionary
    """
    if form_id not in _late_submission_permissions:
        _late_submission_permissions[form_id] = {}
    
    permission_data = {
        "form_id": form_id,
        "user_id": user_id,
        "allowed_until": allowed_until,
        "granted_by": granted_by,
        "reason": reason,
        "granted_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    _late_submission_permissions[form_id][user_id] = permission_data
    
    # Store in database for persistence
    try:
        supabase.table("late_submission_permissions").insert({
            "form_id": form_id,
            "user_id": user_id,
            "allowed_until": allowed_until,
            "granted_by": granted_by,
            "reason": reason,
            "granted_at": permission_data["granted_at"]
        }).execute()
    except Exception as e:
        print(f"Warning: Failed to store late submission permission in database: {e}")
    
    return permission_data


def revoke_late_submission(form_id: int, user_id: str) -> bool:
    """Revoke late submission permission for a user.
    
    Args:
        form_id: ID of the evaluation form
        user_id: ID of the user
        
    Returns:
        True if permission was revoked, False if didn't exist
    """
    if form_id not in _late_submission_permissions:
        return False
    
    if user_id not in _late_submission_permissions[form_id]:
        return False
    
    _late_submission_permissions[form_id][user_id]["is_active"] = False
    
    # Update in database
    try:
        supabase.table("late_submission_permissions").update(
            {"is_active": False}
        ).eq("form_id", form_id).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Warning: Failed to revoke late submission permission in database: {e}")
    
    return True


def is_late_submission_allowed(form_id: int, user_id: str) -> bool:
    """Check if a user has permission for late submission.
    
    Args:
        form_id: ID of the evaluation form
        user_id: ID of the user
        
    Returns:
        True if late submission is allowed and hasn't expired, False otherwise
    """
    if form_id not in _late_submission_permissions:
        return False
    
    if user_id not in _late_submission_permissions[form_id]:
        return False
    
    permission = _late_submission_permissions[form_id][user_id]
    
    # Check if permission is active
    if not permission["is_active"]:
        return False
    
    # Check if allowed_until has passed
    try:
        allowed_until = datetime.fromisoformat(
            permission["allowed_until"].replace('Z', '+00:00')
        )
        now = datetime.now(timezone.utc)
        return now <= allowed_until
    except (ValueError, AttributeError):
        return False


def get_late_submission_permission(form_id: int, user_id: str) -> Optional[Dict[str, Any]]:
    """Get late submission permission details for a user.
    
    Args:
        form_id: ID of the evaluation form
        user_id: ID of the user
        
    Returns:
        Permission data if exists and active, None otherwise
    """
    if not is_late_submission_allowed(form_id, user_id):
        return None
    
    return _late_submission_permissions[form_id][user_id].copy()


def get_all_late_submissions_for_form(form_id: int) -> Dict[int, Dict[str, Any]]:
    """Get all active late submission permissions for a form.
    
    Args:
        form_id: ID of the evaluation form
        
    Returns:
        Dictionary mapping user_id to permission data for all active permissions
    """
    if form_id not in _late_submission_permissions:
        return {}
    
    now = datetime.now(timezone.utc)
    active_permissions = {}
    
    for user_id, permission in _late_submission_permissions[form_id].items():
        if permission["is_active"]:
            try:
                allowed_until = datetime.fromisoformat(
                    permission["allowed_until"].replace('Z', '+00:00')
                )
                if now <= allowed_until:
                    active_permissions[user_id] = permission.copy()
            except (ValueError, AttributeError):
                pass
    
    return active_permissions


def get_all_late_submissions_for_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all active late submission permissions for a user across forms.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of permission data dictionaries
    """
    user_permissions = []
    now = datetime.now(timezone.utc)
    
    for form_id, form_permissions in _late_submission_permissions.items():
        if user_id in form_permissions:
            permission = form_permissions[user_id]
            if permission["is_active"]:
                try:
                    allowed_until = datetime.fromisoformat(
                        permission["allowed_until"].replace('Z', '+00:00')
                    )
                    if now <= allowed_until:
                        user_permissions.append(permission.copy())
                except (ValueError, AttributeError):
                    pass
    
    return user_permissions


def get_all_expired_permissions() -> List[Dict[str, Any]]:
    """Get all expired late submission permissions.
    
    Useful for cleanup and auditing.
    
    Returns:
        List of expired permission data dictionaries
    """
    expired_permissions = []
    now = datetime.now(timezone.utc)
    
    for form_id, form_permissions in _late_submission_permissions.items():
        for user_id, permission in form_permissions.items():
            if permission["is_active"]:
                try:
                    allowed_until = datetime.fromisoformat(
                        permission["allowed_until"].replace('Z', '+00:00')
                    )
                    if now > allowed_until:
                        expired_permissions.append(permission.copy())
                except (ValueError, AttributeError):
                    pass
    
    return expired_permissions


def cleanup_expired_permissions() -> int:
    """Deactivate all expired late submission permissions.
    
    Returns:
        Number of permissions cleaned up
    """
    now = datetime.now(timezone.utc)
    cleaned_count = 0
    
    for form_id, form_permissions in _late_submission_permissions.items():
        for user_id, permission in form_permissions.items():
            if permission["is_active"]:
                try:
                    allowed_until = datetime.fromisoformat(
                        permission["allowed_until"].replace('Z', '+00:00')
                    )
                    if now > allowed_until:
                        permission["is_active"] = False
                        cleaned_count += 1
                except (ValueError, AttributeError):
                    pass
    
    return cleaned_count


def clear_all_permissions() -> int:
    """Clear all late submission permissions (for testing).
    
    Returns:
        Number of permissions cleared
    """
    total = sum(len(perms) for perms in _late_submission_permissions.values())
    _late_submission_permissions.clear()
    return total
