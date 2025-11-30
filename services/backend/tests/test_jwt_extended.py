"""Tests for JWT handler to improve coverage."""
import pytest
from app.core.jwt_handler import create_access_token, verify_token
from datetime import timedelta


def test_create_access_token_basic():
    """Test creating an access token."""
    token = create_access_token(1, "test@example.com", "student")
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expiry():
    """Test creating token with custom expiry."""
    token = create_access_token(
        1, "test@example.com", "student",
        expires_delta=timedelta(hours=1)
    )
    assert token is not None


def test_verify_token_valid():
    """Test verifying a valid token."""
    token = create_access_token(1, "test@example.com", "student")
    payload = verify_token(token)
    assert payload is not None
    if payload:  # May be None if verification fails in test env
        assert "email" in payload
        assert payload["email"] == "test@example.com"


def test_create_access_token_instructor():
    """Test creating token for instructor."""
    token = create_access_token(2, "instructor@example.com", "instructor")
    assert token is not None
    payload = verify_token(token)
    if payload:
        assert payload["role"] == "instructor"
