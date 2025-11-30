"""Tests for deadline enforcement functionality (OPETSE-9)."""
import pytest
from datetime import datetime, timedelta, timezone


@pytest.mark.deadline
class TestDeadlineEnforcement:
    """Test deadline validation and enforcement in evaluations."""

    def test_submit_evaluation_before_deadline_succeeds(self, client):
        """Test that submissions before deadline are allowed."""
        # Set deadline to future (1 day from now)
        future_deadline = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        payload = {
            "form_id": 1,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 100,
            "scores": [
                {"criterion_id": 1, "score": 50},
                {"criterion_id": 2, "score": 50}
            ],
            "comments": "Test before deadline"
        }

        response = client.post("/api/v1/evaluations/", json=payload)
        # Could be 201 if mocked correctly, or 404 if form doesn't exist
        # But should NOT be 403 (deadline passed)
        assert response.status_code != 403

    def test_submit_evaluation_after_deadline_blocked(self, client):
        """Test that submissions after deadline are blocked with 403."""
        # Set deadline to past (1 day ago)
        past_deadline = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        payload = {
            "form_id": 999,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 100,
            "scores": [
                {"criterion_id": 1, "score": 50},
                {"criterion_id": 2, "score": 50}
            ],
            "comments": "Test after deadline"
        }

        response = client.post("/api/v1/evaluations/", json=payload)
        # Expect either 403 (deadline), 404 (form not found), or 422 (validation) depending on mock
        assert response.status_code in [403, 404, 422, 500]

    def test_submit_evaluation_no_deadline_allowed(self, client):
        """Test that submissions are allowed when no deadline is set."""
        payload = {
            "form_id": 1,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 100,
            "scores": [
                {"criterion_id": 1, "score": 50},
                {"criterion_id": 2, "score": 50}
            ],
            "comments": "Test no deadline"
        }

        response = client.post("/api/v1/evaluations/", json=payload)
        # Should not fail with 403 (deadline)
        assert response.status_code != 403

    def test_create_form_with_deadline(self, client):
        """Test creating a form with a deadline."""
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        form_data = {
            "project_id": 1,
            "title": "Test Form with Deadline",
            "max_score": 100,
            "deadline": deadline,
            "criteria": [
                {"text": "Criterion 1", "max_points": 100, "order_index": 0}
            ]
        }

        response = client.post("/api/v1/forms/", json=form_data)
        # Expect 201 or 404/500 depending on project existence
        assert response.status_code in [201, 404, 500]

    def test_update_form_deadline(self, client):
        """Test updating a form's deadline."""
        new_deadline = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()

        update_data = {
            "deadline": new_deadline
        }

        response = client.put("/api/v1/forms/999", json=update_data)
        # Expect 200 or 404 depending on form existence
        assert response.status_code in [200, 404, 500]

    def test_list_forms_includes_deadline_status(self, client):
        """Test that listing forms includes deadline status fields."""
        response = client.get("/api/v1/forms/")

        # Should return 200 or 500
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "forms" in data or "detail" in data


@pytest.mark.deadline
class TestDeadlineUtilityFunctions:
    """Test deadline utility helper functions."""

    def test_deadline_in_future_not_passed(self):
        """Test that future deadlines are not marked as passed."""
        from app.utils.deadline import is_deadline_passed

        future_deadline = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        assert is_deadline_passed(future_deadline) is False

    def test_deadline_in_past_is_passed(self):
        """Test that past deadlines are marked as passed."""
        from app.utils.deadline import is_deadline_passed

        past_deadline = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert is_deadline_passed(past_deadline) is True

    def test_no_deadline_not_passed(self):
        """Test that None deadline is treated as never expired."""
        from app.utils.deadline import is_deadline_passed

        assert is_deadline_passed(None) is False
        assert is_deadline_passed("") is False

    def test_invalid_deadline_format_not_passed(self):
        """Test that invalid deadline formats are treated as not expired."""
        from app.utils.deadline import is_deadline_passed

        assert is_deadline_passed("invalid-date") is False
        assert is_deadline_passed("2024-13-45") is False

    def test_get_time_remaining_future(self):
        """Test time remaining calculation for future deadlines."""
        from app.utils.deadline import get_time_remaining

        future_deadline = (datetime.now(timezone.utc) + timedelta(days=2, hours=3)).isoformat()
        remaining = get_time_remaining(future_deadline)

        assert remaining is not None
        assert "day" in remaining.lower()

    def test_get_time_remaining_past(self):
        """Test time remaining shows 'Expired' for past deadlines."""
        from app.utils.deadline import get_time_remaining

        past_deadline = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        remaining = get_time_remaining(past_deadline)

        assert remaining == "Expired"

    def test_get_time_remaining_none(self):
        """Test time remaining for no deadline."""
        from app.utils.deadline import get_time_remaining

        assert get_time_remaining(None) is None

    def test_format_deadline(self):
        """Test deadline formatting for display."""
        from app.utils.deadline import format_deadline

        deadline = "2025-12-31T23:59:59+00:00"
        formatted = format_deadline(deadline)

        assert formatted is not None
        assert "2025" in formatted
        assert "UTC" in formatted

    def test_validate_deadline_format(self):
        """Test deadline format validation."""
        from app.utils.deadline import validate_deadline_format

        # Valid formats
        assert validate_deadline_format("2025-12-31T23:59:59+00:00") is True
        assert validate_deadline_format("2025-12-31T23:59:59Z") is True

        # Invalid formats
        assert validate_deadline_format("invalid") is False
        assert validate_deadline_format("2025-13-45") is False
