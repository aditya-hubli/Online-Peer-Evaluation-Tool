"""Pytest configuration and shared fixtures."""
import sys
from pathlib import Path
import os
import uuid

# Set environment variables FIRST before any imports
os.environ["ENV"] = "test"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-key"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
os.environ["ASYNC_DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/test"

# Add parent directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch, MagicMock

# In-memory user database for testing
test_users_db = {}
test_user_counter = [1]


def reset_test_db():
    """Reset the test database."""
    global test_users_db, test_user_counter
    test_users_db.clear()
    test_user_counter[0] = 1


def mock_supabase_table(table_name):
    """Create a mock Supabase table with select/insert/execute chain."""
    mock = Mock()

    def select(columns="*"):
        select_mock = Mock()

        def eq(field, value):
            eq_mock = Mock()

            def execute():
                result = Mock()
                if table_name == "users":
                    matching_users = [u for u in test_users_db.values() if u.get(field) == value]
                    result.data = matching_users
                else:
                    result.data = []
                return result

            eq_mock.execute = execute
            return eq_mock

        select_mock.eq = eq
        return select_mock

    def insert(data):
        insert_mock = Mock()

        def execute():
            result = Mock()
            if table_name == "users":
                # Add user to test database with UUID
                user_id = str(uuid.uuid4())
                new_user = {**data, "id": user_id}
                test_users_db[user_id] = new_user
                result.data = [new_user]
            else:
                result.data = [data]
            return result

        insert_mock.execute = execute
        return insert_mock

    mock.select = select
    mock.insert = insert
    return mock


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before any tests run."""
    # Import modules first to make them available for patching
    import app.core.supabase
    import app.api.v1.auth
    import app.api.v1.forms
    import app.api.v1.users
    import app.api.v1.evaluations
    import app.utils.reminder_scheduler
    
    # Create a mock Supabase client
    mock_supabase = Mock()
    mock_supabase.table = mock_supabase_table

    # Patch supabase in all modules
    patcher1 = patch('app.core.supabase.supabase', mock_supabase)
    patcher2 = patch('app.api.v1.auth.supabase', mock_supabase)
    patcher3 = patch('app.api.v1.forms.supabase', mock_supabase)
    patcher4 = patch('app.api.v1.users.supabase', mock_supabase)
    patcher5 = patch('app.api.v1.evaluations.supabase', mock_supabase)
    patcher6 = patch('app.utils.reminder_scheduler.supabase', mock_supabase)

    patcher1.start()
    patcher2.start()
    patcher3.start()
    patcher4.start()
    patcher5.start()
    patcher6.start()

    yield

    patcher1.stop()
    patcher2.stop()
    patcher3.stop()
    patcher4.stop()
    patcher5.stop()
    patcher6.stop()


@pytest.fixture(scope="function", autouse=True)
def mock_supabase_fixture():
    """Reset test database before each test."""
    reset_test_db()

    # Create mock Supabase client for this test
    mock_supabase_client = Mock()
    mock_supabase_client.table = mock_supabase_table

    yield mock_supabase_client

    reset_test_db()


@pytest.fixture
def client(mock_supabase_fixture):
    """Create a test client for the FastAPI app with mocked Supabase."""
    # Import here to ensure mocking is in place
    from app.main import app
    return TestClient(app)


@pytest.fixture
def authenticated_client(mock_supabase_fixture):
    """Create a test client with authentication header for student role."""
    from app.main import app
    from app.core.jwt_handler import create_access_token
    from app.core.roles import UserRole
    from app.core import rbac

    # Mock get_current_user_role to return STUDENT
    def mock_get_current_user_role():
        return UserRole.STUDENT

    rbac.get_current_user_role = mock_get_current_user_role

    # Create a test token for a test user
    token = create_access_token(
        user_id=1,
        email="test@example.com",
        role="student"
    )

    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def authenticated_admin_client(mock_supabase_fixture):
    """Create a test client with admin authentication."""
    from app.main import app
    from app.core.jwt_handler import create_access_token
    from app.core.roles import UserRole
    from app.core import rbac

    # Mock get_current_user_role to return INSTRUCTOR (who can create users)
    def mock_get_current_user_role():
        return UserRole.INSTRUCTOR

    rbac.get_current_user_role = mock_get_current_user_role

    token = create_access_token(
        user_id=2,
        email="admin@example.com",
        role="instructor"
    )

    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "name": "Test User",
        "role": "student"
    }


@pytest.fixture
def test_instructor_data():
    """Sample instructor data for testing."""
    return {
        "email": "instructor@example.com",
        "password": "InstructorPass123!",
        "name": "Test Instructor",
        "role": "instructor"
    }


@pytest.fixture
def test_admin_data():
    """Sample admin data for testing."""
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "name": "Test Admin",
        "role": "admin"
    }


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Ensure we're in test mode
    os.environ["ENV"] = "test"
    yield
    # Cleanup if needed
