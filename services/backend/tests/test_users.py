"""Tests for users API with RBAC."""
import pytest
from app.core.roles import UserRole


@pytest.mark.rbac
class TestUsersAPI:
    """Test users API endpoints."""

    def test_list_users_endpoint_exists(self):
        """Test that list users endpoint is defined."""
        from app.api.v1 import users
        assert hasattr(users.router, 'routes')
        route_paths = [route.path for route in users.router.routes]
        assert "/users/" in route_paths

    def test_get_user_endpoint_exists(self):
        """Test that get user by ID endpoint is defined."""
        from app.api.v1 import users
        route_paths = [route.path for route in users.router.routes]
        assert "/users/{user_id}" in route_paths

    def test_create_user_endpoint_exists(self):
        """Test that create user endpoint is defined."""
        from app.api.v1 import users
        route_methods = [(route.path, list(route.methods)[0]) for route in users.router.routes]
        assert any(path == "/users/" and method == "POST" for path, method in route_methods)

    def test_update_user_endpoint_exists(self):
        """Test that update user endpoint is defined."""
        from app.api.v1 import users
        route_methods = [(route.path, list(route.methods)[0]) for route in users.router.routes]
        assert any(path == "/users/{user_id}" and method == "PUT" for path, method in route_methods)

    def test_delete_user_endpoint_exists(self):
        """Test that delete user endpoint is defined."""
        from app.api.v1 import users
        route_methods = [(route.path, list(route.methods)[0]) for route in users.router.routes]
        assert any(path == "/users/{user_id}" and method == "DELETE" for path, method in route_methods)


@pytest.mark.rbac
class TestUserModels:
    """Test user pydantic models."""

    def test_user_create_model_has_role_field(self):
        """Test that UserCreate model has role field with default."""
        from app.api.v1.users import UserCreate
        user = UserCreate(email="test@example.com", name="Test User")
        assert hasattr(user, 'role')
        assert user.role == "student"  # Default role

    def test_user_create_model_accepts_custom_role(self):
        """Test that UserCreate model accepts custom role."""
        from app.api.v1.users import UserCreate
        user = UserCreate(email="instructor@example.com", name="Instructor", role="instructor")
        assert user.role == "instructor"

    def test_user_response_model_has_role_field(self):
        """Test that UserResponse model has role field."""
        from app.api.v1.users import UserResponse
        assert 'role' in UserResponse.model_fields


@pytest.mark.rbac
class TestUsersRouterIntegration:
    """Test that users router is integrated into API."""

    def test_users_router_included_in_api_v1(self):
        """Test that users router is included in v1 API."""
        from app.api.v1 import api_router
        # Check that users router routes are included
        all_routes = [route.path for route in api_router.routes]
        assert any('/users' in path for path in all_routes)
