"""Tests for authentication endpoints (OPETSE-4)."""
import pytest
from fastapi import status


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration functionality."""

    def test_register_new_user_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]
        assert data["role"] == test_user_data["role"]
        assert "password" not in data  # Password should not be in response
        assert data["message"] == "User registered successfully"

    def test_register_duplicate_email_fails(self, client, test_user_data):
        """Test that registering with duplicate email fails."""
        # First registration
        client.post("/api/v1/auth/register", json=test_user_data)

        # Second registration with same email should fail
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_register_invalid_email_fails(self, client, test_user_data):
        """Test that invalid email format is rejected."""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "not-an-email"

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields_fails(self, client):
        """Test that missing required fields are rejected."""
        incomplete_data = {
            "email": "test@example.com"
            # Missing password, name
        }

        response = client.post("/api/v1/auth/register", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_instructor_role(self, client, test_instructor_data):
        """Test registration with instructor role."""
        response = client.post("/api/v1/auth/register", json=test_instructor_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["role"] == "instructor"

    def test_register_admin_role(self, client, test_admin_data):
        """Test registration with admin role."""
        response = client.post("/api/v1/auth/register", json=test_admin_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["role"] == "admin"

    def test_register_default_role_is_student(self, client):
        """Test that default role is student when not specified."""
        data = {
            "email": "newuser@example.com",
            "password": "Pass123!",
            "name": "New User"
            # role not specified
        }

        response = client.post("/api/v1/auth/register", json=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["role"] == "student"


@pytest.mark.auth
class TestUserLogin:
    """Test user login functionality."""

    def test_login_success(self, client, test_user_data):
        """Test successful login with valid credentials."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)

        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
        assert data["message"] == "Login successful"
        # TODO: Uncomment when JWT is implemented
        # assert "access_token" in data
        # assert data["token_type"] == "bearer"

    def test_login_wrong_password_fails(self, client, test_user_data):
        """Test that login fails with wrong password."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)

        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user_fails(self, client):
        """Test that login fails for non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_login_invalid_email_format_fails(self, client):
        """Test that login with invalid email format is rejected."""
        login_data = {
            "email": "not-an-email",
            "password": "Password123!"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_credentials_fails(self, client):
        """Test that login without credentials is rejected."""
        response = client.post("/api/v1/auth/login", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_preserves_user_role(self, client, test_instructor_data):
        """Test that login returns correct user role."""
        # Register instructor
        client.post("/api/v1/auth/register", json=test_instructor_data)

        # Login
        login_data = {
            "email": test_instructor_data["email"],
            "password": test_instructor_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["role"] == "instructor"


@pytest.mark.auth
class TestUserLogout:
    """Test user logout functionality."""

    def test_logout_returns_success(self, client):
        """Test that logout endpoint returns success message."""
        # First login to get user_id
        login_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
        # Pre-create user via register first
        register_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "name": "Test User",
            "role": "student"
        }
        client.post("/api/v1/auth/register", json=register_data)
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        user_id = login_response.json()["user"]["id"]
        
        # OPETSE-30: Logout now requires user_id query parameter
        response = client.post("/api/v1/auth/logout", params={"user_id": user_id})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "logout" in data["message"].lower() or "session" in data["message"].lower()


@pytest.mark.auth
class TestAuthenticationFlow:
    """Test complete authentication flows."""

    def test_register_login_flow(self, client, test_user_data):
        """Test complete registration and login flow."""
        # Step 1: Register
        register_response = client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]

        # Step 2: Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        assert login_response.json()["user"]["id"] == user_id
        # OPETSE-30: Verify session_timeout_minutes is returned
        assert login_response.json()["session_timeout_minutes"] == 15

        # Step 3: Logout with user_id parameter
        logout_response = client.post("/api/v1/auth/logout", params={"user_id": user_id})
        assert logout_response.status_code == status.HTTP_200_OK

    def test_multiple_users_can_register(self, client, test_user_data, test_instructor_data):
        """Test that multiple users can register independently."""
        # Register student
        response1 = client.post("/api/v1/auth/register", json=test_user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Register instructor
        response2 = client.post("/api/v1/auth/register", json=test_instructor_data)
        assert response2.status_code == status.HTTP_201_CREATED

        # Both should have different IDs
        assert response1.json()["id"] != response2.json()["id"]
