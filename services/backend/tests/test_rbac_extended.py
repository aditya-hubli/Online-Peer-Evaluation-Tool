"""Additional tests for RBAC to increase coverage."""
import pytest
from app.core.roles import has_permission, get_role_permissions, UserRole, Permission
from app.core.rbac import get_current_user_role, require_instructor, require_student
from fastapi import HTTPException


def test_has_permission_student_read_evaluation():
    """Test student can read evaluations."""
    assert has_permission(UserRole.STUDENT, Permission.READ_EVALUATION) == True


def test_has_permission_student_create_evaluation():
    """Test student can create evaluations."""
    assert has_permission(UserRole.STUDENT, Permission.CREATE_EVALUATION) == True


def test_has_permission_student_cannot_create_project():
    """Test student cannot create projects."""
    assert has_permission(UserRole.STUDENT, Permission.CREATE_PROJECT) == False


def test_has_permission_student_cannot_delete_user():
    """Test student cannot delete users."""
    assert has_permission(UserRole.STUDENT, Permission.DELETE_USER) == False


def test_has_permission_instructor_can_create_project():
    """Test instructor can create projects."""
    assert has_permission(UserRole.INSTRUCTOR, Permission.CREATE_PROJECT) == True


def test_has_permission_instructor_can_manage_users():
    """Test instructor can manage users."""
    assert has_permission(UserRole.INSTRUCTOR, Permission.UPDATE_USER) == True


def test_get_role_permissions_student():
    """Test getting all student permissions."""
    perms = get_role_permissions(UserRole.STUDENT)
    assert Permission.READ_EVALUATION in perms
    assert Permission.CREATE_EVALUATION in perms
    assert Permission.CREATE_PROJECT not in perms


def test_get_role_permissions_instructor():
    """Test getting all instructor permissions."""
    perms = get_role_permissions(UserRole.INSTRUCTOR)
    assert Permission.CREATE_PROJECT in perms
    assert Permission.UPDATE_USER in perms
    assert Permission.DELETE_USER in perms


def test_get_current_user_role_returns_default():
    """Test get_current_user_role returns default role."""
    role = get_current_user_role()
    assert role == UserRole.STUDENT


def test_require_instructor_with_student_role():
    """Test require_instructor raises HTTPException for student."""
    with pytest.raises(HTTPException) as exc_info:
        require_instructor(UserRole.STUDENT)
    assert exc_info.value.status_code == 403


def test_require_instructor_with_instructor_role():
    """Test require_instructor allows instructor."""
    result = require_instructor(UserRole.INSTRUCTOR)
    assert result == UserRole.INSTRUCTOR


def test_require_student_with_instructor_role():
    """Test require_student raises HTTPException for instructor."""
    with pytest.raises(HTTPException) as exc_info:
        require_student(UserRole.INSTRUCTOR)
    assert exc_info.value.status_code == 403


def test_require_student_with_student_role():
    """Test require_student allows student."""
    result = require_student(UserRole.STUDENT)
    assert result == UserRole.STUDENT


def test_user_role_enum_values():
    """Test UserRole enum values."""
    assert UserRole.STUDENT.value == "student"
    assert UserRole.INSTRUCTOR.value == "instructor"


def test_permission_enum_contains_all_actions():
    """Test Permission enum has all required permissions."""
    assert hasattr(Permission, 'CREATE_USER')
    assert hasattr(Permission, 'READ_USER')
    assert hasattr(Permission, 'UPDATE_USER')
    assert hasattr(Permission, 'DELETE_USER')
