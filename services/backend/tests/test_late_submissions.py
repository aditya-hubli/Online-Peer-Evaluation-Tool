"""Tests for OPETSE-10: Late Submissions feature (SRS S7).

Tests late submission permission granting, validation, and deadline override.
Ensures instructors can allow late submissions for special cases.
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.core.late_submission import (
    grant_late_submission,
    revoke_late_submission,
    is_late_submission_allowed,
    get_late_submission_permission,
    get_all_late_submissions_for_form,
    get_all_late_submissions_for_user,
    get_all_expired_permissions,
    cleanup_expired_permissions,
    clear_all_permissions
)
from app.utils.deadline import is_deadline_passed


class TestLateSubmissionPermissions:
    """Test late submission permission management."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clear all permissions before each test."""
        clear_all_permissions()
        yield
        clear_all_permissions()

    def test_grant_late_submission(self):
        """Test granting late submission permission."""
        form_id = 1
        user_id = 10
        instructor_id = 5
        allowed_until = datetime.now(timezone.utc).isoformat()

        result = grant_late_submission(
            form_id=form_id,
            user_id=user_id,
            allowed_until=allowed_until,
            granted_by=instructor_id,
            reason="Medical emergency"
        )

        assert result["form_id"] == form_id
        assert result["user_id"] == user_id
        assert result["granted_by"] == instructor_id
        assert result["reason"] == "Medical emergency"
        assert result["is_active"] is True

    def test_grant_multiple_permissions(self):
        """Test granting multiple late submission permissions."""
        form_id = 1
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        result1 = grant_late_submission(form_id, 10, allowed_until, 5)
        result2 = grant_late_submission(form_id, 11, allowed_until, 5)

        assert result1["user_id"] == 10
        assert result2["user_id"] == 11
        assert is_late_submission_allowed(form_id, 10)
        assert is_late_submission_allowed(form_id, 11)

    def test_is_late_submission_allowed_active(self):
        """Test checking if late submission is allowed (active permission)."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)

        assert is_late_submission_allowed(form_id, user_id) is True

    def test_is_late_submission_allowed_expired(self):
        """Test checking if late submission is allowed (expired permission)."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now - timedelta(hours=1)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)

        assert is_late_submission_allowed(form_id, user_id) is False

    def test_is_late_submission_allowed_nonexistent(self):
        """Test checking if late submission is allowed (no permission)."""
        assert is_late_submission_allowed(1, 10) is False

    def test_revoke_late_submission(self):
        """Test revoking late submission permission."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)
        assert is_late_submission_allowed(form_id, user_id) is True

        revoked = revoke_late_submission(form_id, user_id)
        assert revoked is True
        assert is_late_submission_allowed(form_id, user_id) is False

    def test_revoke_nonexistent_permission(self):
        """Test revoking permission that doesn't exist."""
        revoked = revoke_late_submission(1, 10)
        assert revoked is False

    def test_get_late_submission_permission(self):
        """Test retrieving late submission permission details."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(
            form_id, user_id, allowed_until, 5, reason="Special case"
        )

        permission = get_late_submission_permission(form_id, user_id)
        assert permission is not None
        assert permission["form_id"] == form_id
        assert permission["user_id"] == user_id

    def test_get_late_submission_permission_expired(self):
        """Test retrieving expired late submission permission (should return None)."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now - timedelta(hours=1)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)

        permission = get_late_submission_permission(form_id, user_id)
        assert permission is None


class TestLateSumbissionQueries:
    """Test late submission query operations."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clear all permissions before each test."""
        clear_all_permissions()
        yield
        clear_all_permissions()

    def test_get_all_late_submissions_for_form_empty(self):
        """Test getting all late submissions for form with no permissions."""
        result = get_all_late_submissions_for_form(1)
        assert result == {}

    def test_get_all_late_submissions_for_form_multiple(self):
        """Test getting all late submissions for form with multiple permissions."""
        form_id = 1
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(form_id, 10, allowed_until, 5)
        grant_late_submission(form_id, 11, allowed_until, 5)
        grant_late_submission(form_id, 12, allowed_until, 5)

        result = get_all_late_submissions_for_form(form_id)
        assert len(result) == 3
        assert 10 in result
        assert 11 in result
        assert 12 in result

    def test_get_all_late_submissions_for_form_filters_expired(self):
        """Test that expired permissions are filtered out."""
        form_id = 1
        now = datetime.now(timezone.utc)
        active_until = (now + timedelta(hours=24)).isoformat()
        expired_until = (now - timedelta(hours=1)).isoformat()

        grant_late_submission(form_id, 10, active_until, 5)
        grant_late_submission(form_id, 11, expired_until, 5)

        result = get_all_late_submissions_for_form(form_id)
        assert len(result) == 1
        assert 10 in result
        assert 11 not in result

    def test_get_all_late_submissions_for_form_filters_inactive(self):
        """Test that revoked permissions are filtered out."""
        form_id = 1
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(form_id, 10, allowed_until, 5)
        grant_late_submission(form_id, 11, allowed_until, 5)
        revoke_late_submission(form_id, 10)

        result = get_all_late_submissions_for_form(form_id)
        assert len(result) == 1
        assert 10 not in result
        assert 11 in result

    def test_get_all_late_submissions_for_user_empty(self):
        """Test getting all late submissions for user with no permissions."""
        result = get_all_late_submissions_for_user(10)
        assert result == []

    def test_get_all_late_submissions_for_user_multiple(self):
        """Test getting all late submissions for user across multiple forms."""
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(1, user_id, allowed_until, 5)
        grant_late_submission(2, user_id, allowed_until, 5)
        grant_late_submission(3, user_id, allowed_until, 5)

        result = get_all_late_submissions_for_user(user_id)
        assert len(result) == 3

    def test_get_all_late_submissions_for_user_filters_expired(self):
        """Test that expired permissions are filtered out for user queries."""
        user_id = 10
        now = datetime.now(timezone.utc)
        active_until = (now + timedelta(hours=24)).isoformat()
        expired_until = (now - timedelta(hours=1)).isoformat()

        grant_late_submission(1, user_id, active_until, 5)
        grant_late_submission(2, user_id, expired_until, 5)

        result = get_all_late_submissions_for_user(user_id)
        assert len(result) == 1

    def test_get_all_expired_permissions(self):
        """Test retrieving all expired permissions."""
        now = datetime.now(timezone.utc)
        active_until = (now + timedelta(hours=24)).isoformat()
        expired_until = (now - timedelta(hours=1)).isoformat()

        grant_late_submission(1, 10, active_until, 5)
        grant_late_submission(1, 11, expired_until, 5)
        grant_late_submission(2, 12, expired_until, 5)

        expired = get_all_expired_permissions()
        assert len(expired) == 2

    def test_cleanup_expired_permissions(self):
        """Test cleanup of expired permissions."""
        now = datetime.now(timezone.utc)
        active_until = (now + timedelta(hours=24)).isoformat()
        expired_until = (now - timedelta(hours=1)).isoformat()

        grant_late_submission(1, 10, active_until, 5)
        grant_late_submission(1, 11, expired_until, 5)

        count = cleanup_expired_permissions()
        assert count == 1
        assert is_late_submission_allowed(1, 10) is True
        assert is_late_submission_allowed(1, 11) is False


class TestDeadlineWithLateSubmission:
    """Test deadline checking with late submission support."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clear all permissions before each test."""
        clear_all_permissions()
        yield
        clear_all_permissions()

    def test_deadline_passed_no_late_submission(self):
        """Test deadline check when deadline passed and no late submission."""
        now = datetime.now(timezone.utc)
        passed_deadline = (now - timedelta(hours=1)).isoformat()

        result = is_deadline_passed(passed_deadline)
        assert result is True

    def test_deadline_not_passed(self):
        """Test deadline check when deadline not passed."""
        now = datetime.now(timezone.utc)
        future_deadline = (now + timedelta(hours=1)).isoformat()

        result = is_deadline_passed(future_deadline)
        assert result is False

    def test_deadline_with_late_submission_allowed(self):
        """Test deadline check with late submission permission granted."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        passed_deadline = (now - timedelta(hours=1)).isoformat()
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)

        result = is_deadline_passed(
            passed_deadline,
            late_submission_checker=is_late_submission_allowed,
            user_id=user_id,
            form_id=form_id
        )
        assert result is False  # Late submission allowed

    def test_deadline_with_late_submission_expired(self):
        """Test deadline check with expired late submission permission."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        passed_deadline = (now - timedelta(hours=1)).isoformat()
        expired_until = (now - timedelta(hours=2)).isoformat()

        grant_late_submission(form_id, user_id, expired_until, 5)

        result = is_deadline_passed(
            passed_deadline,
            late_submission_checker=is_late_submission_allowed,
            user_id=user_id,
            form_id=form_id
        )
        assert result is True  # Late submission expired, deadline passed

    def test_deadline_with_late_submission_not_granted(self):
        """Test deadline check when late submission not granted."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        passed_deadline = (now - timedelta(hours=1)).isoformat()

        result = is_deadline_passed(
            passed_deadline,
            late_submission_checker=is_late_submission_allowed,
            user_id=user_id,
            form_id=form_id
        )
        assert result is True  # No late submission permission


class TestLateSubmissionEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clear all permissions before each test."""
        clear_all_permissions()
        yield
        clear_all_permissions()

    def test_grant_multiple_times_overwrites(self):
        """Test that granting multiple times overwrites the previous permission."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until1 = (now + timedelta(hours=24)).isoformat()
        allowed_until2 = (now + timedelta(hours=48)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until1, 5, reason="First")
        grant_late_submission(form_id, user_id, allowed_until2, 6, reason="Second")

        permission = get_late_submission_permission(form_id, user_id)
        assert permission["reason"] == "Second"
        assert permission["granted_by"] == 6

    def test_deadline_exactly_at_expiration(self):
        """Test deadline check at exact expiration time."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        # Add a small buffer to account for execution time
        allowed_until = (now + timedelta(seconds=0.1)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)

        # Should still be allowed with small time buffer (<=)
        result = is_late_submission_allowed(form_id, user_id)
        assert result is True

    def test_none_deadline_always_open(self):
        """Test that None deadline means always open."""
        result = is_deadline_passed(None)
        assert result is False

    def test_invalid_deadline_format_treated_as_no_deadline(self):
        """Test that invalid datetime format is treated as no deadline."""
        result = is_deadline_passed("invalid-date")
        assert result is False

    def test_malformed_iso_format_with_z(self):
        """Test handling of malformed ISO format with Z suffix."""
        result = is_deadline_passed("2024-01-01T12:00:00Zinvalid")
        assert result is False

    def test_late_submission_reason_optional(self):
        """Test that late submission reason is optional."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        result = grant_late_submission(
            form_id, user_id, allowed_until, 5
        )

        assert result["reason"] is None

    def test_different_instructors_can_grant_same_form(self):
        """Test that different instructors can grant permissions for same form."""
        form_id = 1
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        result1 = grant_late_submission(form_id, 10, allowed_until, 5)
        result2 = grant_late_submission(form_id, 11, allowed_until, 6)

        assert result1["granted_by"] == 5
        assert result2["granted_by"] == 6


class TestLateSubmissionStateManagement:
    """Test state management and consistency."""

    def test_clear_all_permissions(self):
        """Test clearing all permissions."""
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(1, 10, allowed_until, 5)
        grant_late_submission(1, 11, allowed_until, 5)
        grant_late_submission(2, 12, allowed_until, 5)

        count = clear_all_permissions()
        assert count == 3
        assert is_late_submission_allowed(1, 10) is False
        assert is_late_submission_allowed(2, 12) is False

    def test_separate_forms_have_separate_permissions(self):
        """Test that permissions for different forms don't interfere."""
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(1, 10, allowed_until, 5)
        grant_late_submission(2, 10, allowed_until, 5)

        assert is_late_submission_allowed(1, 10) is True
        assert is_late_submission_allowed(2, 10) is True

        revoke_late_submission(1, 10)

        assert is_late_submission_allowed(1, 10) is False
        assert is_late_submission_allowed(2, 10) is True

    def test_permission_copy_independence(self):
        """Test that returned permission copies are independent."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)

        perm1 = get_late_submission_permission(form_id, user_id)
        perm1["is_active"] = False  # Modify copy

        perm2 = get_late_submission_permission(form_id, user_id)
        assert perm2["is_active"] is True  # Original unchanged


class TestLateSubmissionIntegration:
    """Integration tests combining multiple features."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clear all permissions before each test."""
        clear_all_permissions()
        yield
        clear_all_permissions()

    def test_multiple_users_same_form_late_submissions(self):
        """Test multiple users with late submissions on same form."""
        form_id = 1
        now = datetime.now(timezone.utc)
        passed_deadline = (now - timedelta(hours=1)).isoformat()
        allowed_until = (now + timedelta(hours=24)).isoformat()

        # Grant late submission to user 10
        grant_late_submission(form_id, 10, allowed_until, 5)

        # User 10 can submit late
        assert is_deadline_passed(
            passed_deadline,
            late_submission_checker=is_late_submission_allowed,
            user_id=10,
            form_id=form_id
        ) is False

        # User 11 cannot submit late (no permission)
        assert is_deadline_passed(
            passed_deadline,
            late_submission_checker=is_late_submission_allowed,
            user_id=11,
            form_id=form_id
        ) is True

    def test_cascade_revoke_checks(self):
        """Test that revoking affects all downstream checks."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)
        allowed_until = (now + timedelta(hours=24)).isoformat()

        grant_late_submission(form_id, user_id, allowed_until, 5)

        assert is_late_submission_allowed(form_id, user_id) is True
        assert get_late_submission_permission(form_id, user_id) is not None

        revoke_late_submission(form_id, user_id)

        assert is_late_submission_allowed(form_id, user_id) is False
        assert get_late_submission_permission(form_id, user_id) is None

    def test_time_based_permission_expiration(self):
        """Test time-based expiration of permissions."""
        form_id = 1
        user_id = 10
        now = datetime.now(timezone.utc)

        # Grant with 1-second expiration
        allowed_until = (now + timedelta(seconds=1)).isoformat()
        grant_late_submission(form_id, user_id, allowed_until, 5)

        assert is_late_submission_allowed(form_id, user_id) is True

        # Wait for expiration
        import time
        time.sleep(1.1)

        assert is_late_submission_allowed(form_id, user_id) is False
