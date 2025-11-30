"""RBAC dependency functions for FastAPI."""
from fastapi import Depends, HTTPException, status
from typing import Callable
from app.core.roles import UserRole, Permission, has_permission


def get_current_user_role() -> UserRole:
    """
    Get the current user's role from the request.
    This is a placeholder - in production, extract from JWT token.
    """
    # TODO: Extract from JWT token in Authorization header
    # For now, return a default role for development
    return UserRole.STUDENT


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Dependency to require specific roles.

    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_role(UserRole.INSTRUCTOR))])
    """
    def role_checker(current_role: UserRole = Depends(get_current_user_role)) -> UserRole:
        if current_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_role

    return role_checker


def require_permission(*required_permissions: Permission) -> Callable:
    """
    Dependency to require specific permissions.

    Usage:
        @router.post("/projects", dependencies=[Depends(require_permission(Permission.CREATE_PROJECT))])
    """
    def permission_checker(current_role: UserRole = Depends(get_current_user_role)) -> UserRole:
        for perm in required_permissions:
            if not has_permission(current_role, perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Missing permission: {perm.value}"
                )
        return current_role

    return permission_checker


# Convenience decorators for common role checks
def require_instructor(current_role: UserRole = Depends(get_current_user_role)) -> UserRole:
    """Require instructor role."""
    if current_role != UserRole.INSTRUCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Instructor role required."
        )
    return current_role


def require_student(current_role: UserRole = Depends(get_current_user_role)) -> UserRole:
    """Require student role."""
    if current_role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student role required."
        )
    return current_role
