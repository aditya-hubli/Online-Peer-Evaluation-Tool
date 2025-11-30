"""Additional tests for least_privilege module to increase coverage."""
import pytest
from app.core.least_privilege import CurrentUser
from app.core.roles import UserRole, Permission


def test_current_user_creation():
    """Test creating a CurrentUser instance."""
    user = CurrentUser(user_id=1, email="test@test.com", role="student")
    assert user.user_id == 1
    assert user.role == UserRole.STUDENT
    assert user.email == "test@test.com"


def test_current_user_has_permission_student():
    """Test student has read permissions."""
    user = CurrentUser(user_id=1, email="student@test.com", role="student")
    assert user.has_permission(Permission.READ_EVALUATION) == True
    assert user.has_permission(Permission.CREATE_PROJECT) == False


def test_current_user_has_permission_instructor():
    """Test instructor has create project permission."""
    user = CurrentUser(user_id=1, email="instructor@test.com", role="instructor")
    assert user.has_permission(Permission.CREATE_PROJECT) == True
    assert user.has_permission(Permission.DELETE_USER) == True


def test_current_user_is_resource_owner():
    """Test is_resource_owner method."""
    user = CurrentUser(user_id=5, email="user@test.com", role="student")
    assert user.is_resource_owner(5) == True
    assert user.is_resource_owner(10) == False
