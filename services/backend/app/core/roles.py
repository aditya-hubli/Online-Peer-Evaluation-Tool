"""Role-based access control definitions."""
from enum import Enum
from typing import List


class UserRole(str, Enum):
    """User roles in the system."""
    STUDENT = "student"
    INSTRUCTOR = "instructor"


class Permission(str, Enum):
    """Permissions for different actions."""
    # User management
    CREATE_USER = "create:user"
    READ_USER = "read:user"
    UPDATE_USER = "update:user"
    DELETE_USER = "delete:user"

    # Project management
    CREATE_PROJECT = "create:project"
    READ_PROJECT = "read:project"
    UPDATE_PROJECT = "update:project"
    DELETE_PROJECT = "delete:project"

    # Team management
    CREATE_TEAM = "create:team"
    READ_TEAM = "read:team"
    UPDATE_TEAM = "update:team"
    DELETE_TEAM = "delete:team"

    # Evaluation management
    CREATE_EVALUATION = "create:evaluation"
    READ_EVALUATION = "read:evaluation"
    UPDATE_EVALUATION = "update:evaluation"
    DELETE_EVALUATION = "delete:evaluation"

    # Form management
    CREATE_FORM = "create:form"
    READ_FORM = "read:form"
    UPDATE_FORM = "update:form"
    DELETE_FORM = "delete:form"


# Role-Permission mapping
ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.STUDENT: [
        Permission.READ_USER,
        Permission.UPDATE_USER,  # Own profile only
        Permission.READ_PROJECT,
        Permission.READ_TEAM,
        Permission.CREATE_EVALUATION,
        Permission.READ_EVALUATION,
        Permission.READ_FORM,
    ],
    UserRole.INSTRUCTOR: [
        Permission.CREATE_USER,
        Permission.READ_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.CREATE_PROJECT,
        Permission.READ_PROJECT,
        Permission.UPDATE_PROJECT,
        Permission.DELETE_PROJECT,
        Permission.CREATE_TEAM,
        Permission.READ_TEAM,
        Permission.UPDATE_TEAM,
        Permission.DELETE_TEAM,
        Permission.CREATE_EVALUATION,
        Permission.READ_EVALUATION,
        Permission.UPDATE_EVALUATION,
        Permission.DELETE_EVALUATION,
        Permission.CREATE_FORM,
        Permission.READ_FORM,
        Permission.UPDATE_FORM,
        Permission.DELETE_FORM,
    ],
}


def get_role_permissions(role: UserRole) -> List[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, [])
