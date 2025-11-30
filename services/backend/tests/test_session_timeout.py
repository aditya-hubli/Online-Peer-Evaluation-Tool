"""Tests for session timeout functionality - OPETSE-30 (SRS S27).

Tests server-side session management, timeout detection, and automatic
session invalidation after 15 minutes of inactivity.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.core.session_timeout import (
    create_session,
    update_session_activity,
    is_session_expired,
    get_session,
    destroy_session,
    get_session_info,
    cleanup_expired_sessions,
    get_all_active_sessions,
    clear_all_sessions,
    _active_sessions,
)
from app.core.config import settings


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear all sessions before and after each test."""
    clear_all_sessions()
    yield
    clear_all_sessions()


# ==================== Session Creation Tests ====================

class TestSessionCreation:
    """Test session creation and initialization."""

    def test_create_session_basic(self):
        """Test basic session creation."""
        user_id = 1
        email = "user@example.com"
        role = "student"
        token = "test-token-123"
        
        session = create_session(user_id, email, role, token)
        
        assert session["user_id"] == user_id
        assert session["email"] == email
        assert session["role"] == role
        assert session["token"] == token
        assert session["timeout_minutes"] == settings.SESSION_TIMEOUT_MINUTES
        assert "created_at" in session
        assert "last_activity" in session
        assert isinstance(session["created_at"], datetime)
        assert isinstance(session["last_activity"], datetime)

    def test_create_session_stored_in_active_sessions(self):
        """Test that created session is stored in _active_sessions."""
        user_id = 2
        create_session(user_id, "test@example.com", "instructor", "token")
        
        assert user_id in _active_sessions
        assert _active_sessions[user_id]["user_id"] == user_id

    def test_create_multiple_sessions(self):
        """Test creating multiple concurrent sessions."""
        session1 = create_session(1, "user1@example.com", "student", "token1")
        session2 = create_session(2, "user2@example.com", "instructor", "token2")
        session3 = create_session(3, "user3@example.com", "admin", "token3")
        
        assert len(_active_sessions) == 3
        assert _active_sessions[1]["email"] == "user1@example.com"
        assert _active_sessions[2]["email"] == "user2@example.com"
        assert _active_sessions[3]["email"] == "user3@example.com"

    def test_create_session_overwrites_existing(self):
        """Test that creating a session for existing user overwrites old session."""
        create_session(1, "old@example.com", "student", "old-token")
        create_session(1, "new@example.com", "instructor", "new-token")
        
        assert _active_sessions[1]["email"] == "new@example.com"
        assert _active_sessions[1]["role"] == "instructor"
        assert _active_sessions[1]["token"] == "new-token"


# ==================== Session Expiration Tests ====================

class TestSessionExpiration:
    """Test session expiration detection."""

    def test_is_session_expired_nonexistent_session(self):
        """Test that nonexistent session is considered expired."""
        assert is_session_expired(999) is True

    def test_is_session_expired_fresh_session(self):
        """Test that fresh session is not expired."""
        create_session(1, "user@example.com", "student", "token")
        assert is_session_expired(1) is False

    def test_is_session_expired_after_timeout(self):
        """Test that session is expired after timeout period."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        
        # Manually set last_activity to past
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        
        assert is_session_expired(user_id) is True

    def test_is_session_expired_at_timeout_boundary(self):
        """Test session expiration at exact timeout boundary."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        
        # Set last_activity to exactly timeout_minutes ago minus 0.5 seconds
        # This accounts for processing time and avoids race conditions
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes, seconds=-0.5)
        )
        
        # At exact boundary (with buffer), should NOT be expired (code uses >, not >=)
        assert is_session_expired(user_id) is False

    def test_is_session_expired_just_before_timeout(self):
        """Test session not expired when just before timeout."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        
        # Set last_activity to just before timeout
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes - 1)
        )
        
        assert is_session_expired(user_id) is False


# ==================== Session Activity Update Tests ====================

class TestSessionActivityUpdate:
    """Test session activity tracking and timeout extension."""

    def test_update_session_activity_success(self):
        """Test successful session activity update."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        original_activity = _active_sessions[user_id]["last_activity"]
        
        import time
        time.sleep(0.01)  # Small delay to ensure time difference
        
        result = update_session_activity(user_id)
        
        assert result is True
        assert _active_sessions[user_id]["last_activity"] >= original_activity

    def test_update_session_activity_nonexistent(self):
        """Test updating activity for nonexistent session returns False."""
        assert update_session_activity(999) is False

    def test_update_session_activity_expired_session(self):
        """Test updating activity for expired session returns False."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        
        # Expire the session
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        
        result = update_session_activity(user_id)
        
        assert result is False


# ==================== Session Retrieval Tests ====================

class TestSessionRetrieval:
    """Test session data retrieval."""

    def test_get_session_existing(self):
        """Test retrieving existing active session."""
        user_id = 1
        created = create_session(user_id, "user@example.com", "student", "token")
        
        retrieved = get_session(user_id)
        
        assert retrieved is not None
        assert retrieved["user_id"] == user_id
        assert retrieved["email"] == "user@example.com"

    def test_get_session_nonexistent(self):
        """Test retrieving nonexistent session returns None."""
        assert get_session(999) is None

    def test_get_session_expired_returns_none(self):
        """Test retrieving expired session returns None."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        
        # Expire the session
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        
        retrieved = get_session(user_id)
        
        assert retrieved is None

    def test_get_session_expired_cleans_up(self):
        """Test that getting expired session cleans it up."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        
        # Expire the session
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        
        # Get session (should return None and clean up)
        get_session(user_id)
        
        # Session should be removed from store
        assert user_id not in _active_sessions

    def test_get_session_info_without_expiration_check(self):
        """Test getting raw session info without expiration check."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        
        # Expire the session
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        
        # get_session_info should still return it (no expiration check)
        info = get_session_info(user_id)
        
        assert info is not None
        assert info["user_id"] == user_id


# ==================== Session Destruction Tests ====================

class TestSessionDestruction:
    """Test session logout and destruction."""

    def test_destroy_session_success(self):
        """Test successful session destruction."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        
        assert user_id in _active_sessions
        
        result = destroy_session(user_id)
        
        assert result is True
        assert user_id not in _active_sessions

    def test_destroy_session_nonexistent(self):
        """Test destroying nonexistent session."""
        result = destroy_session(999)
        
        assert result is False

    def test_destroy_multiple_sessions(self):
        """Test destroying multiple sessions."""
        create_session(1, "user1@example.com", "student", "token1")
        create_session(2, "user2@example.com", "instructor", "token2")
        create_session(3, "user3@example.com", "admin", "token3")
        
        assert len(_active_sessions) == 3
        
        destroy_session(1)
        assert len(_active_sessions) == 2
        assert 1 not in _active_sessions
        
        destroy_session(2)
        assert len(_active_sessions) == 1
        assert 2 not in _active_sessions
        
        destroy_session(3)
        assert len(_active_sessions) == 0


# ==================== Cleanup Tests ====================

class TestSessionCleanup:
    """Test session cleanup and maintenance."""

    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        # Create multiple sessions
        for i in range(1, 6):
            create_session(i, f"user{i}@example.com", "student", f"token{i}")
        
        assert len(_active_sessions) == 5
        
        # Expire sessions 1, 2, 3
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        for user_id in [1, 2, 3]:
            _active_sessions[user_id]["last_activity"] = (
                datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
            )
        
        cleaned = cleanup_expired_sessions()
        
        assert cleaned == 3
        assert len(_active_sessions) == 2
        assert 4 in _active_sessions
        assert 5 in _active_sessions

    def test_cleanup_no_expired_sessions(self):
        """Test cleanup when no sessions are expired."""
        for i in range(1, 4):
            create_session(i, f"user{i}@example.com", "student", f"token{i}")
        
        cleaned = cleanup_expired_sessions()
        
        assert cleaned == 0
        assert len(_active_sessions) == 3

    def test_get_all_active_sessions(self):
        """Test getting all active sessions."""
        create_session(1, "user1@example.com", "student", "token1")
        create_session(2, "user2@example.com", "instructor", "token2")
        
        # Expire one
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        _active_sessions[2]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        
        active = get_all_active_sessions()
        
        assert len(active) == 1
        assert 1 in active
        assert 2 not in active

    def test_clear_all_sessions(self):
        """Test clearing all sessions."""
        for i in range(1, 5):
            create_session(i, f"user{i}@example.com", "student", f"token{i}")
        
        assert len(_active_sessions) == 4
        
        cleared = clear_all_sessions()
        
        assert cleared == 4
        assert len(_active_sessions) == 0


# ==================== Configuration Tests ====================

class TestSessionConfiguration:
    """Test session timeout configuration."""

    def test_session_timeout_minutes_from_settings(self):
        """Test that SESSION_TIMEOUT_MINUTES is used correctly."""
        user_id = 1
        session = create_session(user_id, "user@example.com", "student", "token")
        
        assert session["timeout_minutes"] == settings.SESSION_TIMEOUT_MINUTES
        assert session["timeout_minutes"] == 15  # Default value

    def test_session_timeout_default_value(self):
        """Test that default timeout is 15 minutes."""
        assert settings.SESSION_TIMEOUT_MINUTES == 15

    def test_session_respects_configured_timeout(self):
        """Test that sessions use configured timeout value."""
        user_id = 1
        create_session(user_id, "user@example.com", "student", "token")
        
        timeout_minutes = _active_sessions[user_id]["timeout_minutes"]
        
        # Set last_activity to just before timeout
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes - 1)
        )
        assert is_session_expired(user_id) is False
        
        # Set last_activity to just after timeout
        _active_sessions[user_id]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        assert is_session_expired(user_id) is True


# ==================== Concurrent Session Tests ====================

class TestConcurrentSessions:
    """Test multiple concurrent sessions."""

    def test_concurrent_sessions_independent_expiration(self):
        """Test that concurrent sessions expire independently."""
        timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
        
        # Create sessions
        create_session(1, "user1@example.com", "student", "token1")
        asyncio.sleep(0.01)
        create_session(2, "user2@example.com", "student", "token2")
        asyncio.sleep(0.01)
        create_session(3, "user3@example.com", "student", "token3")
        
        # Expire first session only
        _active_sessions[1]["last_activity"] = (
            datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
        )
        
        assert is_session_expired(1) is True
        assert is_session_expired(2) is False
        assert is_session_expired(3) is False

    def test_many_concurrent_sessions(self):
        """Test handling many concurrent sessions."""
        num_sessions = 50
        
        for i in range(1, num_sessions + 1):
            create_session(i, f"user{i}@example.com", "student", f"token{i}")
        
        assert len(_active_sessions) == num_sessions
        
        # Verify all are accessible
        for i in range(1, num_sessions + 1):
            assert get_session(i) is not None
