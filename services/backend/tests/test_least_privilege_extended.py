"""Extended tests for least privilege access control module."""
import pytest
from unittest.mock import Mock
from app.core.least_privilege import (
    enforce_least_privilege,
    resource_owner_or_admin,
    CurrentUser
)
from app.core.roles import UserRole, Permission
from fastapi import HTTPException


def test_enforce_least_privilege_with_permission():
    """Test enforce_least_privilege allows access with correct permission."""
    current_user = CurrentUser(
        user_id=1,
        email="user@test.com",
        role=UserRole.INSTRUCTOR.value
    )
    
    # Should not raise exception for instructor with create_project permission
    try:
        enforce_least_privilege(
            current_user=current_user,
            required_permission=Permission.CREATE_PROJECT
        )
    except HTTPException:
        pytest.fail("Should not raise HTTPException for valid permission")


def test_enforce_least_privilege_without_permission():
    """Test enforce_least_privilege denies access without permission."""
    current_user = CurrentUser(
        user_id=1,
        email="user@test.com",
        role=UserRole.STUDENT.value
    )
    
    with pytest.raises(HTTPException) as exc_info:
        enforce_least_privilege(
            current_user=current_user,
            required_permission=Permission.CREATE_PROJECT
        )
    
    assert exc_info.value.status_code == 403


def test_enforce_least_privilege_with_ownership():
    """Test enforce_least_privilege allows access for resource owner."""
    current_user = CurrentUser(
        user_id=1,
        email="user@test.com",
        role=UserRole.STUDENT.value
    )
    
    # Should not raise exception when user owns the resource
    try:
        enforce_least_privilege(
            current_user=current_user,
            required_permission=Permission.UPDATE_USER,
            resource_owner_id=1
        )
    except HTTPException:
        pytest.fail("Should not raise HTTPException for resource owner")


def test_enforce_least_privilege_without_ownership():
    """Test enforce_least_privilege denies access for non-owner without permission."""
    current_user = CurrentUser(
        user_id=1,
        email="user@test.com",
        role=UserRole.STUDENT.value
    )
    
    with pytest.raises(HTTPException) as exc_info:
        enforce_least_privilege(
            current_user=current_user,
            required_permission=Permission.UPDATE_USER,
            resource_owner_id=2
        )
    
    assert exc_info.value.status_code == 403


def test_enforce_least_privilege_admin_bypass():
    """Test enforce_least_privilege allows instructor (admin) to access any resource."""
    current_user = CurrentUser(
        user_id=1,
        email="admin@test.com",
        role=UserRole.INSTRUCTOR.value
    )
    
    # Instructor (admin) should have access to any resource
    try:
        enforce_least_privilege(
            current_user=current_user,
            required_permission=Permission.UPDATE_USER,
            resource_owner_id=2
        )
    except HTTPException:
        pytest.fail("Should not raise HTTPException for instructor")


def test_resource_owner_or_admin_owner():
    """Test resource_owner_or_admin returns True for owner."""
    current_user = CurrentUser(
        user_id=1,
        email="user@test.com",
        role=UserRole.STUDENT.value
    )
    
    assert resource_owner_or_admin(current_user, 1) is True


def test_resource_owner_or_admin_admin():
    """Test resource_owner_or_admin returns True for instructor (admin)."""
    current_user = CurrentUser(
        user_id=1,
        email="admin@test.com",
        role=UserRole.INSTRUCTOR.value
    )
    
    assert resource_owner_or_admin(current_user, 2) is True


def test_resource_owner_or_admin_neither():
    """Test resource_owner_or_admin returns False for non-owner non-admin."""
    current_user = CurrentUser(
        user_id=1,
        email="user@test.com",
        role=UserRole.STUDENT.value
    )
    
    assert resource_owner_or_admin(current_user, 2) is False


def test_enforce_least_privilege_instructor_permissions():
    """Test enforce_least_privilege for instructor role permissions."""
    current_user = CurrentUser(
        user_id=1,
        email="instructor@test.com",
        role=UserRole.INSTRUCTOR.value
    )
    
    # Instructor should have these permissions
    allowed_permissions = [
        Permission.CREATE_PROJECT,
        Permission.READ_PROJECT,
        Permission.UPDATE_PROJECT,
        Permission.DELETE_PROJECT,
        Permission.CREATE_FORM,
        Permission.READ_FORM
    ]
    
    for perm in allowed_permissions:
        try:
            enforce_least_privilege(current_user, perm)
        except HTTPException:
            pytest.fail(f"Instructor should have {perm}")


def test_enforce_least_privilege_student_limited_permissions():
    """Test enforce_least_privilege for student role limited permissions."""
    current_user = CurrentUser(
        user_id=1,
        email="student@test.com",
        role=UserRole.STUDENT.value
    )
    
    # Student should NOT have these permissions
    denied_permissions = [
        Permission.CREATE_PROJECT,
        Permission.DELETE_PROJECT,
        Permission.DELETE_USER,
        Permission.CREATE_FORM
    ]
    
    for perm in denied_permissions:
        with pytest.raises(HTTPException):
            enforce_least_privilege(current_user, perm)
