"""Tests for role-based access control."""
import pytest
from app.core.roles import UserRole, Permission, get_role_permissions, has_permission


class TestUserRoles:
    """Test user role definitions."""

    def test_student_role_exists(self):
        """Test that student role is defined."""
        assert UserRole.STUDENT == "student"

    def test_instructor_role_exists(self):
        """Test that instructor role is defined."""
        assert UserRole.INSTRUCTOR == "instructor"


class TestPermissions:
    """Test permission definitions."""

    def test_create_project_permission_exists(self):
        """Test that CREATE_PROJECT permission exists."""
        assert Permission.CREATE_PROJECT == "create:project"

    def test_read_form_permission_exists(self):
        """Test that READ_FORM permission exists."""
        assert Permission.READ_FORM == "read:form"


class TestRolePermissions:
    """Test role-permission mappings."""

    def test_student_has_read_permissions(self):
        """Test that students have read permissions."""
        student_perms = get_role_permissions(UserRole.STUDENT)
        assert Permission.READ_USER in student_perms
        assert Permission.READ_PROJECT in student_perms
        assert Permission.READ_FORM in student_perms

    def test_student_cannot_create_projects(self):
        """Test that students cannot create projects."""
        assert not has_permission(UserRole.STUDENT, Permission.CREATE_PROJECT)

    def test_student_cannot_delete_users(self):
        """Test that students cannot delete users."""
        assert not has_permission(UserRole.STUDENT, Permission.DELETE_USER)

    def test_instructor_has_all_permissions(self):
        """Test that instructors have all permissions."""
        instructor_perms = get_role_permissions(UserRole.INSTRUCTOR)
        assert Permission.CREATE_PROJECT in instructor_perms
        assert Permission.DELETE_USER in instructor_perms
        assert Permission.CREATE_FORM in instructor_perms
        assert Permission.UPDATE_TEAM in instructor_perms

    def test_instructor_can_create_projects(self):
        """Test that instructors can create projects."""
        assert has_permission(UserRole.INSTRUCTOR, Permission.CREATE_PROJECT)

    def test_instructor_can_manage_users(self):
        """Test that instructors can manage users."""
        assert has_permission(UserRole.INSTRUCTOR, Permission.CREATE_USER)
        assert has_permission(UserRole.INSTRUCTOR, Permission.UPDATE_USER)
        assert has_permission(UserRole.INSTRUCTOR, Permission.DELETE_USER)


class TestHasPermission:
    """Test has_permission utility function."""

    def test_has_permission_returns_true_for_valid_permission(self):
        """Test that has_permission returns True for valid permissions."""
        assert has_permission(UserRole.INSTRUCTOR, Permission.CREATE_PROJECT) is True

    def test_has_permission_returns_false_for_invalid_permission(self):
        """Test that has_permission returns False for invalid permissions."""
        assert has_permission(UserRole.STUDENT, Permission.DELETE_USER) is False
