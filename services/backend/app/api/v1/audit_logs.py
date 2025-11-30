"""Audit logs API endpoints for OPETSE-15."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.supabase import supabase
from app.utils.audit import (
    log_audit_action,
    get_audit_logs,
    get_user_activity,
    get_resource_history,
    get_action_summary,
    AuditAction
)

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


# Pydantic models
class AuditLogCreate(BaseModel):
    action: str
    user_id: Optional[int] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class AuditLogQuery(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 100
    offset: int = 0


class AuditLogResponse(BaseModel):
    id: int
    action: str
    user_id: Optional[int]
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: str
    action_summary: Optional[str] = None


@router.get("/")
async def list_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List audit logs with optional filters.
    Requires admin role for full access.
    """
    try:
        result = await get_audit_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        # Add human-readable action summaries
        for log in result["logs"]:
            log["action_summary"] = get_action_summary(log["action"])

        return {
            "logs": result["logs"],
            "count": result["count"],
            "offset": offset,
            "limit": limit,
            "message": "Audit logs retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/{log_id}")
async def get_audit_log(log_id: int):
    """Get a specific audit log entry by ID."""
    try:
        result = supabase.table("audit_logs").select("*").eq("id", log_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )

        log = result.data[0]

        # Enrich with user information
        if log.get("user_id"):
            user_result = supabase.table("users").select("id, name, email, role").eq("id", log["user_id"]).execute()
            if user_result.data:
                log["user"] = user_result.data[0]

        log["action_summary"] = get_action_summary(log["action"])

        return {
            "log": log,
            "message": "Audit log retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit log: {str(e)}"
        )


@router.get("/user/{user_id}")
async def get_user_audit_logs(user_id: str, limit: int = 50):
    """Get audit logs for a specific user's actions."""
    try:
        # Verify user exists
        user = supabase.table("users").select("*").eq("id", user_id).execute()

        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        result = await get_user_activity(user_id, limit)

        # Add action summaries
        for log in result["logs"]:
            log["action_summary"] = get_action_summary(log["action"])

        return {
            "user": user.data[0],
            "logs": result["logs"],
            "count": result["count"],
            "message": f"Activity logs for user {user_id} retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user activity: {str(e)}"
        )


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_audit_logs(resource_type: str, resource_id: int, limit: int = 50):
    """Get audit logs (change history) for a specific resource."""
    try:
        result = await get_resource_history(resource_type, resource_id, limit)

        # Add action summaries
        for log in result["logs"]:
            log["action_summary"] = get_action_summary(log["action"])

        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "logs": result["logs"],
            "count": result["count"],
            "message": f"Change history for {resource_type} #{resource_id} retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resource history: {str(e)}"
        )


@router.get("/actions/types")
async def list_action_types():
    """Get list of all possible audit action types."""
    actions = [
        {"value": AuditAction.USER_CREATED, "label": get_action_summary(AuditAction.USER_CREATED)},
        {"value": AuditAction.USER_UPDATED, "label": get_action_summary(AuditAction.USER_UPDATED)},
        {"value": AuditAction.USER_DELETED, "label": get_action_summary(AuditAction.USER_DELETED)},
        {"value": AuditAction.USER_LOGIN, "label": get_action_summary(AuditAction.USER_LOGIN)},
        {"value": AuditAction.USER_LOGOUT, "label": get_action_summary(AuditAction.USER_LOGOUT)},
        {"value": AuditAction.ROLE_CHANGED, "label": get_action_summary(AuditAction.ROLE_CHANGED)},
        {"value": AuditAction.FORM_CREATED, "label": get_action_summary(AuditAction.FORM_CREATED)},
        {"value": AuditAction.FORM_UPDATED, "label": get_action_summary(AuditAction.FORM_UPDATED)},
        {"value": AuditAction.FORM_DELETED, "label": get_action_summary(AuditAction.FORM_DELETED)},
        {"value": AuditAction.EVALUATION_SUBMITTED, "label": get_action_summary(AuditAction.EVALUATION_SUBMITTED)},
        {"value": AuditAction.EVALUATION_UPDATED, "label": get_action_summary(AuditAction.EVALUATION_UPDATED)},
        {"value": AuditAction.EVALUATION_DELETED, "label": get_action_summary(AuditAction.EVALUATION_DELETED)},
        {"value": AuditAction.PROJECT_CREATED, "label": get_action_summary(AuditAction.PROJECT_CREATED)},
        {"value": AuditAction.TEAM_CREATED, "label": get_action_summary(AuditAction.TEAM_CREATED)},
        {"value": AuditAction.MEMBER_ADDED, "label": get_action_summary(AuditAction.MEMBER_ADDED)},
        {"value": AuditAction.REPORT_VIEWED, "label": get_action_summary(AuditAction.REPORT_VIEWED)},
    ]

    return {
        "actions": actions,
        "count": len(actions),
        "message": "Action types retrieved successfully"
    }


@router.get("/stats/summary")
async def get_audit_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get summary statistics of audit logs."""
    try:
        query = supabase.table("audit_logs").select("action")

        if start_date:
            query = query.gte("timestamp", start_date)
        if end_date:
            query = query.lte("timestamp", end_date)

        result = query.execute()
        logs = result.data or []

        # Count by action type
        action_counts = {}
        for log in logs:
            action = log.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        # Sort by count
        action_summary = [
            {
                "action": action,
                "count": count,
                "label": get_action_summary(action)
            }
            for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        # Get unique user count
        unique_users_query = supabase.table("audit_logs").select("user_id", count="exact")
        if start_date:
            unique_users_query = unique_users_query.gte("timestamp", start_date)
        if end_date:
            unique_users_query = unique_users_query.lte("timestamp", end_date)

        unique_users_result = unique_users_query.execute()
        unique_users = len(set(log["user_id"] for log in (unique_users_result.data or []) if log.get("user_id")))

        return {
            "total_logs": len(logs),
            "unique_users": unique_users,
            "action_breakdown": action_summary,
            "start_date": start_date,
            "end_date": end_date,
            "message": "Audit statistics retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit statistics: {str(e)}"
        )


@router.delete("/{log_id}")
async def delete_audit_log(log_id: int):
    """
    Delete a specific audit log (admin only, use with caution).
    Note: Deleting audit logs defeats the purpose of auditability.
    This should only be used in exceptional circumstances.
    """
    try:
        # Check if log exists
        existing = supabase.table("audit_logs").select("*").eq("id", log_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )

        # Delete the log
        supabase.table("audit_logs").delete().eq("id", log_id).execute()

        return {
            "message": f"Audit log {log_id} deleted",
            "deleted_log": existing.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete audit log: {str(e)}"
        )
