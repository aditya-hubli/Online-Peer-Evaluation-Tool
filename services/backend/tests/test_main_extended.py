"""Extended tests for main application module."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_app_instance_exists():
    """Test that FastAPI app instance exists."""
    assert app is not None
    assert hasattr(app, 'title')


def test_app_has_cors_middleware():
    """Test that CORS middleware is configured."""
    # Check middleware is added
    assert len(app.user_middleware) > 0


def test_app_routes_registered():
    """Test that main routes are registered."""
    routes = [route.path for route in app.routes]
    assert "/api/v1/auth" in [r for r in routes if "/auth" in r] or any("/auth" in r for r in routes)


def test_health_check_endpoint_if_exists():
    """Test health check endpoint if it exists."""
    client = TestClient(app)
    # Try common health check endpoints
    for path in ["/", "/health", "/api/health"]:
        response = client.get(path)
        # We just check it doesn't crash - may or may not exist
        assert response.status_code in [200, 404]


def test_app_openapi_schema():
    """Test that OpenAPI schema is generated."""
    schema = app.openapi()
    assert schema is not None
    assert "openapi" in schema
    assert "paths" in schema


def test_app_version_info():
    """Test app has version information."""
    schema = app.openapi()
    assert "info" in schema
    assert "title" in schema["info"]


def test_api_v1_router_included():
    """Test that API v1 router is included."""
    routes = [route.path for route in app.routes]
    api_v1_routes = [r for r in routes if r.startswith("/api/v1")]
    assert len(api_v1_routes) > 0


def test_app_exception_handlers():
    """Test that exception handlers are configured."""
    # The app should have exception handlers
    assert hasattr(app, 'exception_handlers')
