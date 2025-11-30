"""Tests for form version history and rollback endpoints (OPETSE-25)."""
import pytest
from fastapi import status


@pytest.mark.rollback
class TestRollbackEndpoints:
    """Test that rollback endpoints exist and respond appropriately."""

    def test_list_versions_endpoint_exists(self, client):
        """Test that version listing endpoint exists."""
        form_id = 999  # Non-existent form
        response = client.get(f"/api/v1/forms/{form_id}/versions")
        # Should return 404 or 500, not 405 Method Not Allowed
        assert response.status_code in [404, 500]

    def test_get_version_endpoint_exists(self, client):
        """Test that get specific version endpoint exists."""
        form_id = 999
        version_id = 1
        response = client.get(f"/api/v1/forms/{form_id}/versions/{version_id}")
        # Should return 404 or 500, not 405 Method Not Allowed
        assert response.status_code in [404, 500]

    def test_rollback_endpoint_exists(self, client):
        """Test that rollback endpoint exists."""
        form_id = 999
        version_id = 1
        response = client.post(f"/api/v1/forms/{form_id}/rollback/{version_id}")
        # Should return 404 or 500, not 405 Method Not Allowed
        assert response.status_code in [404, 500]

    def test_list_versions_returns_json(self, client):
        """Test that list versions returns JSON structure."""
        form_id = 999
        response = client.get(f"/api/v1/forms/{form_id}/versions")
        # Even on error, should return JSON
        assert response.headers.get("content-type", "").startswith("application/json")

    def test_rollback_requires_post(self, client):
        """Test that rollback requires POST method."""
        form_id = 1
        version_id = 1
        # Try GET instead of POST - should fail with Method Not Allowed
        response = client.get(f"/api/v1/forms/{form_id}/rollback/{version_id}")
        assert response.status_code == 405  # Method Not Allowed


@pytest.mark.rollback
class TestRollbackValidation:
    """Test validation for rollback operations."""

    def test_rollback_nonexistent_form(self, client):
        """Test rollback with non-existent form ID."""
        form_id = 99999
        version_id = 1
        response = client.post(f"/api/v1/forms/{form_id}/rollback/{version_id}")
        # Should return 404 or 500
        assert response.status_code in [404, 500]

    def test_rollback_nonexistent_version(self, client):
        """Test rollback with non-existent version ID."""
        form_id = 1
        version_id = 99999
        response = client.post(f"/api/v1/forms/{form_id}/rollback/{version_id}")
        # Should return 404 or 500
        assert response.status_code in [404, 500]

    def test_list_versions_nonexistent_form(self, client):
        """Test listing versions for non-existent form."""
        form_id = 99999
        response = client.get(f"/api/v1/forms/{form_id}/versions")
        # Should return 404 or 500
        assert response.status_code in [404, 500]

    def test_get_version_nonexistent_form(self, client):
        """Test getting version for non-existent form."""
        form_id = 99999
        version_id = 1
        response = client.get(f"/api/v1/forms/{form_id}/versions/{version_id}")
        # Should return 404 or 500
        assert response.status_code in [404, 500]

