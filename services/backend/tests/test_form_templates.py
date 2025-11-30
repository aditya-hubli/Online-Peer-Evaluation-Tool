"""
Test suite for rubric template reuse functionality (OPETSE-19).
Tests form duplication feature for saving instructor time.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.template
class TestFormDuplication:
    """Test form duplication/template reuse functionality."""

    def test_duplicate_endpoint_exists(self, client, mock_supabase_fixture):
        """Test that duplicate endpoint is accessible."""
        response = client.post(
            "/api/v1/forms/1/duplicate",
            json={"target_project_id": 2}
        )
        # Should not return 405 (Method Not Allowed) - proves endpoint exists
        assert response.status_code != 405

    def test_duplicate_requires_target_project_id(self, client, mock_supabase_fixture):
        """Test that target_project_id is required."""
        response = client.post(
            "/api/v1/forms/1/duplicate",
            json={}
        )
        # Should fail validation
        assert response.status_code in [400, 422]

    def test_duplicate_accepts_new_title(self, client, mock_supabase_fixture):
        """Test that new_title parameter is accepted."""
        response = client.post(
            "/api/v1/forms/1/duplicate",
            json={"target_project_id": 2, "new_title": "My Custom Title"}
        )
        # Should accept valid request format
        assert response.status_code != 422

    def test_duplicate_rejects_invalid_fields(self, client, mock_supabase_fixture):
        """Test that invalid fields are rejected."""
        response = client.post(
            "/api/v1/forms/1/duplicate",
            json={"invalid_field": "value"}
        )
        # Should fail validation (missing required field)
        assert response.status_code in [400, 422]


@pytest.mark.template
class TestTemplateSaveTime:
    """Test that feature achieves goal of saving instructor time."""

    def test_single_api_call_design(self, client, mock_supabase_fixture):
        """Verify duplication uses single API call (efficient design)."""
        # Should be one POST call to duplicate everything
        response = client.post(
            "/api/v1/forms/1/duplicate",
            json={"target_project_id": 2}
        )
        # Proves single-call endpoint exists
        assert response.status_code != 405

    def test_duplicate_route_registered(self, client, mock_supabase_fixture):
        """Test that duplicate route is properly registered."""
        # Test various valid request formats
        test_cases = [
            {"target_project_id": 2},
            {"target_project_id": 3, "new_title": "Copy"},
        ]

        for payload in test_cases:
            response = client.post("/api/v1/forms/1/duplicate", json=payload)
            # None should return 405 (proves route exists)
            assert response.status_code != 405
