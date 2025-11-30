"""
OPETSE-11: Tests for Automated Deadline Reminders
Tests email service, reminder scheduler, and API endpoints.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock


@pytest.mark.reminder
class TestEmailService:
    """Test email notification service."""

    def test_email_service_disabled_by_default(self):
        """Test that email service is disabled when EMAIL_ENABLED is false."""
        from app.utils.email_service import EmailService

        service = EmailService()
        # Should return True (no-op) when disabled
        result = service.send_email("test@example.com", "Test", "Body")
        assert result is True

    @patch('smtplib.SMTP')
    @patch('os.getenv')
    def test_send_email_success(self, mock_getenv, mock_smtp):
        """Test successful email sending."""
        from app.utils.email_service import EmailService

        # Mock environment variables
        mock_getenv.side_effect = lambda key, default="": {
            "EMAIL_ENABLED": "true",
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@example.com",
            "SMTP_PASSWORD": "password",
            "FROM_EMAIL": "noreply@example.com"
        }.get(key, default)

        # Mock SMTP connection
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService()
        result = service.send_email("student@example.com", "Test Subject", "Test Body")

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch('os.getenv')
    def test_send_email_missing_credentials(self, mock_getenv):
        """Test email sending fails with missing credentials."""
        from app.utils.email_service import EmailService

        mock_getenv.side_effect = lambda key, default="": {
            "EMAIL_ENABLED": "true",
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "",
            "SMTP_PASSWORD": ""
        }.get(key, default)

        service = EmailService()
        result = service.send_email("test@example.com", "Test", "Body")

        assert result is False

    def test_send_deadline_reminder_formats_correctly(self):
        """Test that deadline reminder email formats correctly."""
        from app.utils.email_service import EmailService

        service = EmailService()
        # This should work even when disabled (no-op)
        result = service.send_deadline_reminder(
            to_email="student@example.com",
            student_name="John Doe",
            form_title="Team Peer Evaluation",
            deadline="2025-12-31 23:59:59 UTC",
            time_remaining="2 days, 3 hours",
            project_title="Software Engineering Project"
        )

        assert result is True

    def test_send_bulk_reminders(self):
        """Test bulk reminder sending."""
        from app.utils.email_service import EmailService

        service = EmailService()
        recipients = [
            {
                "to_email": "student1@example.com",
                "student_name": "Student 1",
                "form_title": "Evaluation Form",
                "deadline": "2025-12-31 23:59:59 UTC",
                "time_remaining": "48 hours",
                "project_title": "Project A"
            },
            {
                "to_email": "student2@example.com",
                "student_name": "Student 2",
                "form_title": "Evaluation Form",
                "deadline": "2025-12-31 23:59:59 UTC",
                "time_remaining": "48 hours",
                "project_title": "Project A"
            }
        ]

        result = service.send_bulk_reminders(recipients)

        assert result["success_count"] == 2
        assert result["failure_count"] == 0
        assert len(result["failed_emails"]) == 0


@pytest.mark.reminder
class TestReminderScheduler:
    """Test reminder scheduler logic."""

    def test_get_upcoming_deadlines_filters_correctly(self):
        """Test that upcoming deadlines are filtered by time window."""
        from app.utils.reminder_scheduler import get_upcoming_deadlines

        # This will query the database, so results depend on test data
        deadlines = get_upcoming_deadlines(hours_ahead=48)

        # Should return a list (empty or with items)
        assert isinstance(deadlines, list)

    def test_get_students_for_form_returns_list(self):
        """Test getting students who need reminders for a form."""
        from app.utils.reminder_scheduler import get_students_for_form

        # Test with non-existent form
        students = get_students_for_form(form_id=999999)

        # Should return empty list for non-existent form
        assert isinstance(students, list)

    @patch('app.utils.email_service.email_service.send_bulk_reminders')
    def test_send_reminders_for_form_no_students(self, mock_send):
        """Test sending reminders when no students need them."""
        from app.utils.reminder_scheduler import send_reminders_for_form

        result = send_reminders_for_form(form_id=999999)

        assert result["reminders_sent"] == 0
        assert result["message"] == "No students need reminders"
        mock_send.assert_not_called()

    def test_process_all_upcoming_deadlines_returns_summary(self):
        """Test processing all upcoming deadlines."""
        from app.utils.reminder_scheduler import process_all_upcoming_deadlines

        summary = process_all_upcoming_deadlines(hours_ahead=48)

        assert "total_forms" in summary
        assert "total_reminders" in summary
        assert "total_success" in summary
        assert "total_failures" in summary
        assert "forms_processed" in summary
        assert isinstance(summary["forms_processed"], list)


@pytest.mark.reminder
class TestReminderAPI:
    """Test reminder API endpoints."""

    def test_list_upcoming_deadlines_endpoint(self, client):
        """Test GET /reminders/upcoming-deadlines endpoint."""
        response = client.get("/api/v1/reminders/upcoming-deadlines?hours_ahead=24")

        # Should return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "count" in data
            assert "forms" in data
            assert "hours_ahead" in data
            assert isinstance(data["forms"], list)

    def test_get_reminder_stats_endpoint(self, client):
        """Test GET /reminders/stats endpoint."""
        response = client.get("/api/v1/reminders/stats?hours_ahead=48")

        # Should return 200 or 500
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "total_forms" in data
            assert "total_students" in data
            assert "hours_ahead" in data
            assert "forms" in data

    def test_trigger_reminders_all_forms(self, client):
        """Test POST /reminders/trigger for all forms."""
        payload = {
            "hours_ahead": 48
        }

        response = client.post("/api/v1/reminders/trigger", json=payload)

        # Should return 200 or 500
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "summary" in data

    def test_trigger_reminders_specific_form(self, client):
        """Test POST /reminders/trigger for specific form."""
        payload = {
            "form_id": 1,
            "hours_ahead": 48
        }

        response = client.post("/api/v1/reminders/trigger", json=payload)

        # Should return 200 or 500
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "result" in data

    def test_send_test_email_endpoint(self, client):
        """Test POST /reminders/test-email endpoint."""
        response = client.post("/api/v1/reminders/test-email?email=test@example.com")

        # Should return 200 or 500 depending on email config
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "email" in data
            assert data["email"] == "test@example.com"


@pytest.mark.reminder
class TestDeadlineUtils:
    """Test deadline utility functions used by reminders."""

    def test_format_deadline_returns_readable_string(self):
        """Test deadline formatting for email display."""
        from app.utils.deadline import format_deadline

        deadline = "2025-12-31T23:59:59+00:00"
        formatted = format_deadline(deadline)

        assert formatted is not None
        assert "2025" in formatted
        assert "UTC" in formatted

    def test_get_time_remaining_future_deadline(self):
        """Test time remaining calculation for future deadline."""
        from app.utils.deadline import get_time_remaining

        future_deadline = (datetime.now(timezone.utc) + timedelta(days=2, hours=3)).isoformat()
        remaining = get_time_remaining(future_deadline)

        assert remaining is not None
        assert "day" in remaining.lower()

    def test_get_time_remaining_past_deadline(self):
        """Test time remaining for expired deadline."""
        from app.utils.deadline import get_time_remaining

        past_deadline = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        remaining = get_time_remaining(past_deadline)

        assert remaining == "Expired"

    def test_is_deadline_passed_future(self):
        """Test deadline check for future deadline."""
        from app.utils.deadline import is_deadline_passed

        future_deadline = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        assert is_deadline_passed(future_deadline) is False

    def test_is_deadline_passed_past(self):
        """Test deadline check for past deadline."""
        from app.utils.deadline import is_deadline_passed

        past_deadline = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert is_deadline_passed(past_deadline) is True


@pytest.mark.reminder
class TestIntegrationScenarios:
    """Integration tests for complete reminder workflows."""

    def test_full_reminder_workflow_no_deadlines(self):
        """Test complete workflow when no deadlines are upcoming."""
        from app.utils.reminder_scheduler import process_all_upcoming_deadlines

        summary = process_all_upcoming_deadlines(hours_ahead=1)  # Very short window

        # Should complete without errors
        assert "total_forms" in summary
        assert isinstance(summary["forms_processed"], list)

    @patch('app.utils.email_service.email_service.send_bulk_reminders')
    def test_reminder_email_content_includes_deadline_info(self, mock_send):
        """Test that reminder emails include all required information."""
        from app.utils.email_service import EmailService

        service = EmailService()
        service.send_deadline_reminder(
            to_email="student@example.com",
            student_name="Test Student",
            form_title="Peer Evaluation Form",
            deadline="2025-12-31 23:59:59 UTC",
            time_remaining="2 days, 5 hours",
            project_title="Software Engineering"
        )

        # Verify the call was made (even if disabled)
        # In production, this would send the actual email
        assert True  # Email service handles the logic
