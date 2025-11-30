"""Test least-privilege access control enforcement - OPETSE-29 (SRS S26)."""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from app.core.jwt_handler import create_access_token, verify_token, decode_token
from app.core.least_privilege import CurrentUser, resource_owner_or_admin, enforce_least_privilege
from app.core.roles import UserRole, Permission


class TestJWTTokenGeneration:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test creating a valid access token."""
        token = create_access_token(user_id=1, email="user@test.com", role="student")
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_user_info(self):
        """Test that token contains encoded user information."""
        token = create_access_token(user_id=42, email="admin@test.com", role="instructor")
        payload = decode_token(token)

        assert payload is not None
        assert payload["user_id"] == 42
        assert payload["email"] == "admin@test.com"
        assert payload["role"] == "instructor"

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        token = create_access_token(user_id=1, email="user@test.com", role="student")
        payload = verify_token(token)

        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["email"] == "user@test.com"

    def test_verify_expired_token(self):
        """Test that expired token verification returns None."""
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(
            user_id=1,
            email="user@test.com",
            role="student",
            expires_delta=expires_delta
        )

        payload = verify_token(token)
        # Token should be expired or None
        assert payload is None or datetime.fromisoformat(str(payload.get("exp", datetime.now()))) < datetime.utcnow()

    def test_decode_token_without_verification(self):
        """Test decoding token without signature verification."""
        token = create_access_token(user_id=5, email="test@example.com", role="student")
        payload = decode_token(token)

        assert payload is not None
        assert payload["user_id"] == 5
        assert payload["email"] == "test@example.com"

    def test_decode_invalid_token(self):
        """Test that decoding invalid token returns None."""
        invalid_token = "invalid.token.here"
        payload = decode_token(invalid_token)

        assert payload is None


class TestCurrentUserContext:
    """Test CurrentUser context and permission checking."""

    def test_current_user_creation(self):
        """Test creating CurrentUser object."""
        user = CurrentUser(user_id=1, email="user@test.com", role="student")

        assert user.user_id == 1
        assert user.email == "user@test.com"
        assert user.role == UserRole.STUDENT

    def test_current_user_has_permission(self):
        """Test checking if user has permission."""
        student = CurrentUser(user_id=1, email="user@test.com", role="student")
        instructor = CurrentUser(user_id=2, email="admin@test.com", role="instructor")

        # Students can read projects
        assert student.has_permission(Permission.READ_PROJECT)
        # Students cannot create projects
        assert not student.has_permission(Permission.CREATE_PROJECT)

        # Instructors can create projects
        assert instructor.has_permission(Permission.CREATE_PROJECT)

    def test_current_user_is_admin(self):
        """Test checking if user is admin."""
        student = CurrentUser(user_id=1, email="user@test.com", role="student")
        instructor = CurrentUser(user_id=2, email="admin@test.com", role="instructor")

        assert not student.is_admin()
        assert instructor.is_admin()

    def test_current_user_is_resource_owner(self):
        """Test checking resource ownership."""
        user = CurrentUser(user_id=1, email="user@test.com", role="student")

        assert user.is_resource_owner(1)
        assert not user.is_resource_owner(2)

    def test_student_permission_matrix(self):
        """Test all student permissions."""
        student = CurrentUser(user_id=1, email="student@test.com", role="student")

        # Students have read permissions
        assert student.has_permission(Permission.READ_USER)
        assert student.has_permission(Permission.READ_PROJECT)
        assert student.has_permission(Permission.READ_TEAM)
        assert student.has_permission(Permission.READ_FORM)

        # Students can create evaluations
        assert student.has_permission(Permission.CREATE_EVALUATION)
        assert student.has_permission(Permission.READ_EVALUATION)

        # Students cannot create/delete resources
        assert not student.has_permission(Permission.CREATE_PROJECT)
        assert not student.has_permission(Permission.DELETE_PROJECT)
        assert not student.has_permission(Permission.DELETE_USER)

    def test_instructor_permission_matrix(self):
        """Test all instructor permissions."""
        instructor = CurrentUser(user_id=1, email="instructor@test.com", role="instructor")

        # Instructors have full permissions
        assert instructor.has_permission(Permission.CREATE_USER)
        assert instructor.has_permission(Permission.READ_USER)
        assert instructor.has_permission(Permission.UPDATE_USER)
        assert instructor.has_permission(Permission.DELETE_USER)

        assert instructor.has_permission(Permission.CREATE_PROJECT)
        assert instructor.has_permission(Permission.CREATE_TEAM)
        assert instructor.has_permission(Permission.CREATE_FORM)
        assert instructor.has_permission(Permission.DELETE_EVALUATION)


class TestAccessControlFunctions:
    """Test least-privilege access control enforcement functions."""

    def test_resource_owner_or_admin_owner(self):
        """Test that resource owner has access."""
        owner = CurrentUser(user_id=1, email="owner@test.com", role="student")

        assert resource_owner_or_admin(owner, resource_owner_id=1)

    def test_resource_owner_or_admin_admin(self):
        """Test that admin always has access."""
        admin = CurrentUser(user_id=2, email="admin@test.com", role="instructor")

        assert resource_owner_or_admin(admin, resource_owner_id=1)

    def test_resource_owner_or_admin_denied(self):
        """Test that non-owner non-admin is denied."""
        user = CurrentUser(user_id=3, email="user@test.com", role="student")

        assert not resource_owner_or_admin(user, resource_owner_id=1)

    def test_enforce_least_privilege_permission_denied(self):
        """Test that permission denial is enforced."""
        from fastapi import HTTPException

        student = CurrentUser(user_id=1, email="student@test.com", role="student")

        with pytest.raises(HTTPException) as exc_info:
            enforce_least_privilege(student, Permission.DELETE_PROJECT)

        assert exc_info.value.status_code == 403

    def test_enforce_least_privilege_permission_granted(self):
        """Test that permission is granted when user has it."""
        instructor = CurrentUser(user_id=1, email="instructor@test.com", role="instructor")

        # Should not raise exception
        result = enforce_least_privilege(instructor, Permission.CREATE_PROJECT)
        assert result is True

    def test_enforce_least_privilege_ownership_denied(self):
        """Test that ownership is enforced for resource-specific actions."""
        from fastapi import HTTPException

        user = CurrentUser(user_id=3, email="user@test.com", role="student")

        with pytest.raises(HTTPException) as exc_info:
            enforce_least_privilege(
                user,
                Permission.UPDATE_USER,
                resource_owner_id=1
            )

        assert exc_info.value.status_code == 403

    def test_enforce_least_privilege_ownership_granted(self):
        """Test that owner has access to resource."""
        user = CurrentUser(user_id=1, email="user@test.com", role="student")

        result = enforce_least_privilege(
            user,
            Permission.UPDATE_USER,
            resource_owner_id=1
        )
        assert result is True


class TestLeastPrivilegeIntegration:
    """Integration tests for least-privilege access control."""

    def test_student_cannot_delete_user(self):
        """Test that student cannot delete any user."""
        from fastapi import HTTPException

        student = CurrentUser(user_id=1, email="student@test.com", role="student")

        with pytest.raises(HTTPException) as exc_info:
            enforce_least_privilege(student, Permission.DELETE_USER, resource_owner_id=1)

        assert exc_info.value.status_code == 403

    def test_instructor_can_delete_user(self):
        """Test that instructor can delete any user."""
        instructor = CurrentUser(user_id=2, email="instructor@test.com", role="instructor")

        result = enforce_least_privilege(
            instructor,
            Permission.DELETE_USER,
            resource_owner_id=1
        )
        assert result is True

    def test_user_can_update_own_profile(self):
        """Test that user can update only their own profile."""
        from fastapi import HTTPException

        user = CurrentUser(user_id=1, email="user@test.com", role="student")

        # Can update own profile
        result = enforce_least_privilege(
            user,
            Permission.UPDATE_USER,
            resource_owner_id=1
        )
        assert result is True

        # Cannot update other profile
        with pytest.raises(HTTPException):
            enforce_least_privilege(
                user,
                Permission.UPDATE_USER,
                resource_owner_id=2
            )

    def test_jwt_integration(self):
        """Test JWT token creation and verification in context."""
        token = create_access_token(user_id=10, email="test@test.com", role="instructor")
        payload = verify_token(token)

        assert payload is not None

        # Create user context from token
        user = CurrentUser(
            user_id=payload["user_id"],
            email=payload["email"],
            role=payload["role"]
        )

        assert user.user_id == 10
        assert user.email == "test@test.com"
        assert user.is_admin()


class TestLeastPrivilegeModuleStructure:
    """Test module structure and file locations."""

    def test_jwt_handler_file_exists(self):
        """Test that jwt_handler.py file exists."""
        test_dir = Path(__file__).parent
        backend_dir = test_dir.parent
        jwt_file = backend_dir / "app" / "core" / "jwt_handler.py"

        assert jwt_file.exists(), f"JWT handler file not found at {jwt_file}"

    def test_least_privilege_file_exists(self):
        """Test that least_privilege.py file exists."""
        test_dir = Path(__file__).parent
        backend_dir = test_dir.parent
        lp_file = backend_dir / "app" / "core" / "least_privilege.py"

        assert lp_file.exists(), f"Least privilege file not found at {lp_file}"

    def test_auth_has_jwt_integration(self):
        """Test that auth.py integrates JWT."""
        test_dir = Path(__file__).parent
        backend_dir = test_dir.parent
        auth_file = backend_dir / "app" / "api" / "v1" / "auth.py"

        with open(auth_file, 'r') as f:
            content = f.read()
            assert "jwt_handler" in content
            assert "create_access_token" in content
            assert "access_token" in content
