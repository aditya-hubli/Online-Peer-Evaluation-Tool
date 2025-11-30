"""Least-privilege access control enforcement - OPETSE-29 (SRS S26)."""
from fastapi import HTTPException, status, Header
from typing import Optional, Dict, Any
from app.core.jwt_handler import verify_token
from app.core.roles import UserRole, Permission, has_permission


class CurrentUser:
    """Represents the currently authenticated user with their context."""

    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = UserRole(role)

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return has_permission(self.role, permission)

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.INSTRUCTOR

    def is_resource_owner(self, resource_owner_id: str) -> bool:
        """Check if user owns a resource."""
        return self.user_id == resource_owner_id


async def get_current_user(authorization: Optional[str] = Header(None)) -> CurrentUser:
    """
    Extract and verify current user from JWT token in Authorization header.

    Usage in endpoints:
        @router.get("/protected", dependencies=[Depends(get_current_user)])

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        CurrentUser object with user context

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>"
        )

    token = parts[1]

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return CurrentUser(
        user_id=payload.get("user_id"),
        email=payload.get("email"),
        role=payload.get("role")
    )


def require_permission(permission: Permission):
    """
    Dependency to require a specific permission.

    Usage:
        @router.post("/create", dependencies=[Depends(require_permission(Permission.CREATE_PROJECT))])
    """
    async def permission_checker(current_user: CurrentUser = Header(None)):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission.value}"
            )
        return current_user

    return permission_checker


def require_role(*roles: UserRole):
    """
    Dependency to require specific roles.

    Usage:
        @router.delete("/users/{id}", dependencies=[Depends(require_role(UserRole.INSTRUCTOR))])
    """
    async def role_checker(current_user: CurrentUser):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return current_user

    return role_checker


def resource_owner_or_admin(current_user: CurrentUser, resource_owner_id: str) -> bool:
    """
    Check if user is the resource owner or admin.

    Usage:
        if not resource_owner_or_admin(current_user, user_id):
            raise HTTPException(status_code=403, detail="Access denied")

    Args:
        current_user: Current user context
        resource_owner_id: ID of the resource owner

    Returns:
        True if user is owner or admin, False otherwise
    """
    return current_user.is_resource_owner(resource_owner_id) or current_user.is_admin()


def enforce_least_privilege(current_user: CurrentUser, required_permission: Permission, resource_owner_id: Optional[int] = None) -> bool:
    """
    Enforce least-privilege access: user must have permission AND (be owner or admin for resource-specific actions).

    Args:
        current_user: Current user context
        required_permission: Permission required for the action
        resource_owner_id: Optional resource owner ID for ownership check

    Returns:
        True if access is allowed, raises HTTPException if denied

    Raises:
        HTTPException: If access is denied
    """
    # Check permission
    if not current_user.has_permission(required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Missing permission: {required_permission.value}"
        )

    # For resource-specific actions, check ownership or admin status
    if resource_owner_id is not None:
        if not resource_owner_or_admin(current_user, resource_owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to access this resource."
            )

    return True
