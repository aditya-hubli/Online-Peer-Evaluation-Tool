"""Standalone test for session timeout module - OPETSE-30.

This test file doesn't import the full app, avoiding dependency conflicts.
"""

import sys
from datetime import datetime, timedelta
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.session_timeout import (
    create_session,
    update_session_activity,
    is_session_expired,
    get_session,
    destroy_session,
    get_session_info,
    cleanup_expired_sessions,
    _active_sessions
)
from app.core.config import settings


def test_session_timeout_basic():
    """Test basic session timeout functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Session Creation and Expiration")
    print("="*60)
    
    # Clear any existing sessions
    _active_sessions.clear()
    
    # Create a session
    user_id = 1
    session = create_session(
        user_id=user_id,
        email="test@university.edu",
        role="student",
        token="test-token-123"
    )
    
    print(f"✓ Session created for user {user_id}")
    print(f"  - Email: {session['email']}")
    print(f"  - Role: {session['role']}")
    print(f"  - Active: {session['is_active']}")
    
    # Session should not be expired
    is_expired = is_session_expired(user_id)
    assert not is_expired, "Newly created session should not be expired"
    print(f"✓ Session is not expired (as expected)")
    
    # Get session
    retrieved = get_session(user_id)
    assert retrieved is not None, "Should retrieve active session"
    print(f"✓ Successfully retrieved session")


def test_session_timeout_expiration():
    """Test session expiration after timeout period."""
    print("\n" + "="*60)
    print("TEST 2: Session Expiration After Timeout")
    print("="*60)
    
    _active_sessions.clear()
    
    user_id = 2
    session = create_session(
        user_id=user_id,
        email="expired@university.edu",
        role="instructor",
        token="test-token-456"
    )
    
    print(f"✓ Session created for user {user_id}")
    
    # Simulate inactivity by setting last_activity to past
    timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
    past_time = datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
    _active_sessions[user_id]["last_activity"] = past_time
    
    print(f"  - Session timeout configured: {timeout_minutes} minutes")
    print(f"  - Simulated inactivity: {timeout_minutes + 1} minutes")
    
    # Check if expired
    is_expired = is_session_expired(user_id)
    assert is_expired, "Session should be expired"
    print(f"✓ Session correctly detected as expired")
    
    # Trying to retrieve expired session should return None
    retrieved = get_session(user_id)
    assert retrieved is None, "Expired session should be destroyed"
    print(f"✓ Expired session was automatically destroyed")


def test_session_activity_update():
    """Test session activity tracking."""
    print("\n" + "="*60)
    print("TEST 3: Session Activity Updates")
    print("="*60)
    
    _active_sessions.clear()
    
    user_id = 3
    session = create_session(
        user_id=user_id,
        email="active@university.edu",
        role="student",
        token="test-token-789"
    )
    
    print(f"✓ Session created for user {user_id}")
    
    # Set activity to 14 minutes ago (within timeout)
    _active_sessions[user_id]["last_activity"] = datetime.utcnow() - timedelta(minutes=14)
    print(f"  - Set last activity to 14 minutes ago")
    
    # Session should not be expired
    assert not is_session_expired(user_id), "Session should not expire yet"
    print(f"✓ Session still active (within {settings.SESSION_TIMEOUT_MINUTES} min timeout)")
    
    # Update activity
    result = update_session_activity(user_id)
    assert result is True, "Activity update should succeed"
    print(f"✓ Successfully updated session activity")
    
    # Verify activity was updated
    current_session = _active_sessions[user_id]
    time_diff = (datetime.utcnow() - current_session["last_activity"]).total_seconds()
    assert time_diff < 5, "Activity should be recently updated"
    print(f"  - Activity timestamp refreshed (time diff: {time_diff:.1f}s)")


def test_session_info_retrieval():
    """Test session info with time remaining."""
    print("\n" + "="*60)
    print("TEST 4: Session Info with Time Remaining")
    print("="*60)
    
    _active_sessions.clear()
    
    user_id = 4
    session = create_session(
        user_id=user_id,
        email="info@university.edu",
        role="student",
        token="test-token-000"
    )
    
    print(f"✓ Session created for user {user_id}")
    
    # Get session info
    session_info = get_session_info(user_id)
    
    assert session_info["user_id"] == user_id
    assert session_info["email"] == "info@university.edu"
    assert session_info["timeout_minutes"] == settings.SESSION_TIMEOUT_MINUTES
    assert session_info["is_active"] is True
    assert session_info["time_remaining_seconds"] > 0
    
    print(f"  - Email: {session_info['email']}")
    print(f"  - Role: {session_info['role']}")
    print(f"  - Timeout: {session_info['timeout_minutes']} minutes")
    print(f"  - Time Remaining: {session_info['time_remaining_seconds']} seconds (~{session_info['time_remaining_seconds']//60} min)")
    print(f"✓ Session info retrieved successfully")


def test_session_destruction():
    """Test session logout/destruction."""
    print("\n" + "="*60)
    print("TEST 5: Session Destruction (Logout)")
    print("="*60)
    
    _active_sessions.clear()
    
    user_id = 5
    session = create_session(
        user_id=user_id,
        email="destroy@university.edu",
        role="admin",
        token="test-token-111"
    )
    
    print(f"✓ Session created for user {user_id}")
    
    # Verify session exists
    assert user_id in _active_sessions, "Session should exist"
    print(f"✓ Session exists in active sessions")
    
    # Destroy session
    result = destroy_session(user_id)
    assert result is True, "Destroy should succeed"
    print(f"✓ Session destroyed successfully")
    
    # Verify session is gone
    assert user_id not in _active_sessions, "Session should be removed"
    print(f"✓ Session removed from active sessions")
    
    # Try to retrieve destroyed session
    retrieved = get_session(user_id)
    assert retrieved is None, "Cannot retrieve destroyed session"
    print(f"✓ Cannot retrieve destroyed session")


def test_multiple_sessions():
    """Test management of multiple concurrent sessions."""
    print("\n" + "="*60)
    print("TEST 6: Multiple Concurrent Sessions")
    print("="*60)
    
    _active_sessions.clear()
    
    # Create multiple sessions
    users = [
        (1, "user1@university.edu", "student"),
        (2, "user2@university.edu", "instructor"),
        (3, "user3@university.edu", "student"),
    ]
    
    for user_id, email, role in users:
        create_session(user_id, email, role, f"token-{user_id}")
    
    print(f"✓ Created {len(users)} concurrent sessions")
    
    # Expire one session
    timeout_minutes = settings.SESSION_TIMEOUT_MINUTES
    _active_sessions[2]["last_activity"] = datetime.utcnow() - timedelta(minutes=timeout_minutes + 1)
    print(f"  - Expired user 2 session")
    
    # Cleanup expired sessions
    cleaned = cleanup_expired_sessions()
    assert cleaned == 1, "Should clean 1 expired session"
    print(f"✓ Cleaned up {cleaned} expired session(s)")
    
    # Verify active sessions
    assert len(_active_sessions) == 2, "Should have 2 active sessions"
    print(f"✓ Remaining active sessions: {len(_active_sessions)}")


def test_timeout_configuration():
    """Test session timeout configuration."""
    print("\n" + "="*60)
    print("TEST 7: Timeout Configuration")
    print("="*60)
    
    _active_sessions.clear()
    
    timeout = settings.SESSION_TIMEOUT_MINUTES
    assert timeout == 15, f"Default timeout should be 15 minutes, got {timeout}"
    print(f"✓ Session timeout configuration: {timeout} minutes")
    print(f"  - This matches SRS requirement S27")
    print(f"  - Users will be logged out after {timeout} minutes of inactivity")


def run_all_tests():
    """Run all session timeout tests."""
    print("\n" + "="*80)
    print(" OPETSE-30: SESSION TIMEOUT TESTS (SRS S27)")
    print("="*80)
    print(f" Testing automatic session timeout after {settings.SESSION_TIMEOUT_MINUTES} minutes")
    print("="*80)
    
    try:
        test_session_timeout_basic()
        test_session_timeout_expiration()
        test_session_activity_update()
        test_session_info_retrieval()
        test_session_destruction()
        test_multiple_sessions()
        test_timeout_configuration()
        
        print("\n" + "="*80)
        print(" ✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n Summary:")
        print("  ✓ Session creation and tracking working")
        print("  ✓ Session expiration detection working")
        print("  ✓ Activity tracking and refresh working")
        print("  ✓ Session information retrieval working")
        print("  ✓ Session destruction (logout) working")
        print("  ✓ Multiple concurrent sessions management working")
        print("  ✓ Configuration correctly set to 15 minutes")
        print("\n OPETSE-30 Feature: ✅ READY FOR DEPLOYMENT")
        print("="*80 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
