"""Audit logging utilities for OPETSE-15."""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.core.supabase import supabase


class AuditAction:
    """Enumeration of auditable actions."""
    # User actions
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"

    # Role/Permission actions
    ROLE_CHANGED = "role.changed"
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"

    # Form actions
    FORM_CREATED = "form.created"
    FORM_UPDATED = "form.updated"
    FORM_DELETED = "form.deleted"
    CRITERION_ADDED = "criterion.added"
    CRITERION_UPDATED = "criterion.updated"
    CRITERION_DELETED = "criterion.deleted"

    # Evaluation actions
    EVALUATION_SUBMITTED = "evaluation.submitted"
    EVALUATION_UPDATED = "evaluation.updated"
    EVALUATION_DELETED = "evaluation.deleted"

    # Project actions
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"

    # Team actions
    TEAM_CREATED = "team.created"
    TEAM_UPDATED = "team.updated"
    TEAM_DELETED = "team.deleted"
    MEMBER_ADDED = "team.member_added"
    MEMBER_REMOVED = "team.member_removed"

    # Report actions
    REPORT_VIEWED = "report.viewed"
    REPORT_EXPORTED = "report.exported"

    # CSV Upload actions
    CSV_UPLOAD_STARTED = "csv.upload_started"
    CSV_UPLOAD_COMPLETED = "csv.upload_completed"
    CSV_UPLOAD_FAILED = "csv.upload_failed"


async def log_audit_action(
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log an audit action to the database.

    Args:
        action: Action type (use AuditAction constants)
        user_id: ID of user performing the action (None for anonymous)
        resource_type: Type of resource affected (e.g., 'user', 'form', 'evaluation')
        resource_id: ID of the affected resource
        details: Additional details as JSON object
        ip_address: IP address of the user
        user_agent: User agent string

    Returns:
        Created audit log entry
    """
    try:
        audit_entry = {
            "action": action,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        result = supabase.table("audit_logs").insert(audit_entry).execute()

        if result.data:
            return result.data[0]
        return audit_entry

    except Exception as e:
        # Don't let audit logging failures break the main operation
        # Log to console/monitoring system instead
        print(f"Audit logging failed: {str(e)}")
        return {}


async def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieve audit logs with optional filters.

    Args:
        user_id: Filter by user who performed the action
        action: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by specific resource ID
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum number of records to return
        offset: Number of records to skip

    Returns:
        Dictionary with logs and count
    """
    try:
        query = supabase.table("audit_logs").select("*")

        # Apply filters
        if user_id is not None:
            query = query.eq("user_id", user_id)
        if action:
            query = query.eq("action", action)
        if resource_type:
            query = query.eq("resource_type", resource_type)
        if resource_id is not None:
            query = query.eq("resource_id", resource_id)
        if start_date:
            query = query.gte("timestamp", start_date)
        if end_date:
            query = query.lte("timestamp", end_date)

        # Order by timestamp descending (newest first)
        query = query.order("timestamp", desc=True)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        result = query.execute()

        # Enrich with user information
        logs = result.data or []
        for log in logs:
            if log.get("user_id"):
                user_result = supabase.table("users").select("id, name, email, role").eq("id", log["user_id"]).execute()
                if user_result.data:
                    log["user"] = user_result.data[0]

        return {
            "logs": logs,
            "count": len(logs),
            "offset": offset,
            "limit": limit
        }

    except Exception as e:
        raise Exception(f"Failed to retrieve audit logs: {str(e)}")


async def get_user_activity(user_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get recent activity for a specific user.

    Args:
        user_id: User ID
        limit: Maximum number of records

    Returns:
        User's recent activity logs
    """
    return await get_audit_logs(user_id=user_id, limit=limit)


async def get_resource_history(resource_type: str, resource_id: int, limit: int = 50) -> Dict[str, Any]:
    """
    Get change history for a specific resource.

    Args:
        resource_type: Type of resource (e.g., 'form', 'evaluation')
        resource_id: Resource ID
        limit: Maximum number of records

    Returns:
        Resource's change history
    """
    return await get_audit_logs(resource_type=resource_type, resource_id=resource_id, limit=limit)


def get_action_summary(action: str) -> str:
    """
    Get human-readable summary for an action.

    Args:
        action: Action type

    Returns:
        Human-readable description
    """
    action_map = {
        AuditAction.USER_CREATED: "User account created",
        AuditAction.USER_UPDATED: "User account updated",
        AuditAction.USER_DELETED: "User account deleted",
        AuditAction.USER_LOGIN: "User logged in",
        AuditAction.USER_LOGOUT: "User logged out",
        AuditAction.USER_REGISTER: "User registered",
        AuditAction.ROLE_CHANGED: "User role changed",
        AuditAction.FORM_CREATED: "Evaluation form created",
        AuditAction.FORM_UPDATED: "Evaluation form updated",
        AuditAction.FORM_DELETED: "Evaluation form deleted",
        AuditAction.EVALUATION_SUBMITTED: "Evaluation submitted",
        AuditAction.EVALUATION_UPDATED: "Evaluation updated",
        AuditAction.EVALUATION_DELETED: "Evaluation deleted",
        AuditAction.PROJECT_CREATED: "Project created",
        AuditAction.PROJECT_UPDATED: "Project updated",
        AuditAction.PROJECT_DELETED: "Project deleted",
        AuditAction.TEAM_CREATED: "Team created",
        AuditAction.TEAM_UPDATED: "Team updated",
        AuditAction.TEAM_DELETED: "Team deleted",
        AuditAction.MEMBER_ADDED: "Team member added",
        AuditAction.MEMBER_REMOVED: "Team member removed",
        AuditAction.REPORT_VIEWED: "Report viewed",
        AuditAction.CSV_UPLOAD_COMPLETED: "CSV upload completed"
    }

    return action_map.get(action, action)
