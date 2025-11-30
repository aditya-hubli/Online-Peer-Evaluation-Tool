"""
OPETSE-8: Tests for Anonymous Feedback Feature

Tests that evaluator identities are properly anonymized for students
while remaining visible to instructors and admins.
"""
import pytest
from app.utils.anonymity import (
    anonymize_evaluator,
    anonymize_evaluation_list,
    anonymize_report_data,
    should_anonymize_for_user,
    _can_view_evaluator_identity
)


class TestAnonymityPermissions:
    """Test role-based permission checks for viewing evaluator identities."""

    def test_student_cannot_view_evaluator_identity(self):
        """Students should not be able to see evaluator identities."""
        assert not _can_view_evaluator_identity("student")
        assert should_anonymize_for_user("student")

    def test_instructor_can_view_evaluator_identity(self):
        """Instructors should be able to see evaluator identities."""
        assert _can_view_evaluator_identity("instructor")
        assert not should_anonymize_for_user("instructor")

    def test_admin_can_view_evaluator_identity(self):
        """Admins should be able to see evaluator identities."""
        assert _can_view_evaluator_identity("admin")
        assert not should_anonymize_for_user("admin")

    def test_none_role_defaults_to_anonymous(self):
        """None role should default to requiring anonymization."""
        assert not _can_view_evaluator_identity(None)
        assert should_anonymize_for_user(None)

    def test_case_insensitive_role_check(self):
        """Role checks should be case-insensitive."""
        assert _can_view_evaluator_identity("INSTRUCTOR")
        assert _can_view_evaluator_identity("Admin")
        assert not _can_view_evaluator_identity("STUDENT")


class TestEvaluatorAnonymization:
    """Test anonymization of individual evaluation records."""

    def test_anonymize_evaluator_for_student(self):
        """Evaluator info should be masked for students."""
        evaluation = {
            "id": 1,
            "evaluator_id": 123,
            "evaluator": {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com"
            },
            "evaluatee_id": 456,
            "total_score": 85,
            "comments": "Great work!"
        }

        result = anonymize_evaluator(evaluation, requester_role="student")

        # Evaluator info should be anonymized
        assert result["evaluator"]["id"] == "anonymous"
        assert result["evaluator"]["name"] == "Anonymous"
        assert result["evaluator"]["email"] == "anonymous@hidden.com"
        assert "evaluator_id_hidden" in result
        assert result["evaluator_id_hidden"] is True

        # Other data should remain intact
        assert result["evaluatee_id"] == 456
        assert result["total_score"] == 85
        assert result["comments"] == "Great work!"

    def test_preserve_evaluator_for_instructor(self):
        """Evaluator info should be preserved for instructors."""
        evaluation = {
            "id": 1,
            "evaluator_id": 123,
            "evaluator": {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com"
            },
            "evaluatee_id": 456,
            "total_score": 85
        }

        result = anonymize_evaluator(evaluation, requester_role="instructor")

        # Evaluator info should be preserved
        assert result["evaluator"]["id"] == 123
        assert result["evaluator"]["name"] == "John Doe"
        assert result["evaluator"]["email"] == "john@example.com"
        assert "evaluator_id_hidden" not in result

    def test_preserve_evaluator_for_admin(self):
        """Evaluator info should be preserved for admins."""
        evaluation = {
            "id": 1,
            "evaluator_id": 123,
            "evaluator": {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com"
            },
            "total_score": 85
        }

        result = anonymize_evaluator(evaluation, requester_role="admin")

        # Evaluator info should be preserved
        assert result["evaluator"]["id"] == 123
        assert result["evaluator"]["name"] == "John Doe"

    def test_anonymize_evaluation_without_evaluator_object(self):
        """Should handle evaluations without evaluator object gracefully."""
        evaluation = {
            "id": 1,
            "evaluator_id": 123,
            "total_score": 85
        }

        result = anonymize_evaluator(evaluation, requester_role="student")

        # Should mark as hidden but not crash
        assert "evaluator_id_hidden" in result
        assert result["evaluator_id_hidden"] is True


class TestEvaluationListAnonymization:
    """Test anonymization of lists of evaluations."""

    def test_anonymize_multiple_evaluations_for_student(self):
        """All evaluations in list should be anonymized for students."""
        evaluations = [
            {
                "id": 1,
                "evaluator_id": 123,
                "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"},
                "total_score": 85
            },
            {
                "id": 2,
                "evaluator_id": 456,
                "evaluator": {"id": 456, "name": "Jane Smith", "email": "jane@example.com"},
                "total_score": 90
            }
        ]

        result = anonymize_evaluation_list(evaluations, requester_role="student")

        assert len(result) == 2
        for evaluation in result:
            assert evaluation["evaluator"]["name"] == "Anonymous"
            assert evaluation["evaluator"]["email"] == "anonymous@hidden.com"

    def test_preserve_multiple_evaluations_for_instructor(self):
        """All evaluations in list should be preserved for instructors."""
        evaluations = [
            {
                "id": 1,
                "evaluator_id": 123,
                "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"},
                "total_score": 85
            },
            {
                "id": 2,
                "evaluator_id": 456,
                "evaluator": {"id": 456, "name": "Jane Smith", "email": "jane@example.com"},
                "total_score": 90
            }
        ]

        result = anonymize_evaluation_list(evaluations, requester_role="instructor")

        assert len(result) == 2
        assert result[0]["evaluator"]["name"] == "John Doe"
        assert result[1]["evaluator"]["name"] == "Jane Smith"

    def test_empty_evaluation_list(self):
        """Should handle empty lists gracefully."""
        result = anonymize_evaluation_list([], requester_role="student")
        assert result == []


class TestReportAnonymization:
    """Test anonymization of report data structures."""

    def test_anonymize_simple_report_with_evaluations(self):
        """Report with evaluations list should be anonymized for students."""
        report = {
            "project": {"id": 1, "name": "Test Project"},
            "evaluations": [
                {
                    "id": 1,
                    "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"},
                    "total_score": 85
                }
            ]
        }

        result = anonymize_report_data(report, requester_role="student")

        assert result["evaluations"][0]["evaluator"]["name"] == "Anonymous"

    def test_anonymize_team_report_with_member_evaluations(self):
        """Team report with nested member evaluations should be anonymized."""
        report = {
            "team": {"id": 1, "name": "Team A"},
            "members": [
                {
                    "member": {"id": 456, "name": "Alice"},
                    "evaluations": [
                        {
                            "id": 1,
                            "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"}
                        }
                    ]
                }
            ]
        }

        result = anonymize_report_data(report, requester_role="student")

        assert result["members"][0]["evaluations"][0]["evaluator"]["name"] == "Anonymous"

    def test_anonymize_project_report_with_nested_teams(self):
        """Project report with nested team and member evaluations should be anonymized."""
        report = {
            "project": {"id": 1, "name": "Project X"},
            "teams": [
                {
                    "team": {"id": 1, "name": "Team A"},
                    "members": [
                        {
                            "member": {"id": 456, "name": "Alice"},
                            "evaluations": [
                                {
                                    "id": 1,
                                    "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"}
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        result = anonymize_report_data(report, requester_role="student")

        member_evals = result["teams"][0]["members"][0]["evaluations"]
        assert member_evals[0]["evaluator"]["name"] == "Anonymous"

    def test_preserve_report_for_instructor(self):
        """Report should preserve evaluator info for instructors."""
        report = {
            "evaluations": [
                {
                    "id": 1,
                    "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"}
                }
            ]
        }

        result = anonymize_report_data(report, requester_role="instructor")

        assert result["evaluations"][0]["evaluator"]["name"] == "John Doe"

    def test_anonymize_detailed_evaluations_in_user_report(self):
        """User report detailed_evaluations should be anonymized."""
        report = {
            "user": {"id": 456, "name": "Alice"},
            "detailed_evaluations": [
                {
                    "id": 1,
                    "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"}
                }
            ]
        }

        result = anonymize_report_data(report, requester_role="student")

        assert result["detailed_evaluations"][0]["evaluator"]["name"] == "Anonymous"


class TestAnonymityInAPIContext:
    """Test anonymity behavior in API-like scenarios."""

    def test_student_viewing_own_evaluations(self):
        """
        Student viewing their own received evaluations should see scores
        but not who evaluated them.
        """
        my_evaluations = [
            {
                "id": 1,
                "evaluator_id": 123,
                "evaluator": {"id": 123, "name": "Peer A", "email": "peer_a@example.com"},
                "evaluatee_id": 456,  # The student viewing
                "total_score": 85,
                "comments": "Good collaboration"
            },
            {
                "id": 2,
                "evaluator_id": 789,
                "evaluator": {"id": 789, "name": "Peer B", "email": "peer_b@example.com"},
                "evaluatee_id": 456,
                "total_score": 90,
                "comments": "Excellent technical skills"
            }
        ]

        # Student views their evaluations
        result = anonymize_evaluation_list(my_evaluations, requester_role="student")

        # Should see scores and comments but not evaluator identities
        assert result[0]["total_score"] == 85
        assert result[0]["comments"] == "Good collaboration"
        assert result[0]["evaluator"]["name"] == "Anonymous"

        assert result[1]["total_score"] == 90
        assert result[1]["comments"] == "Excellent technical skills"
        assert result[1]["evaluator"]["name"] == "Anonymous"

    def test_instructor_viewing_all_team_evaluations(self):
        """Instructors should see full details including evaluator names."""
        team_evaluations = [
            {
                "id": 1,
                "evaluator": {"id": 123, "name": "Student A", "email": "student_a@example.com"},
                "evaluatee": {"id": 456, "name": "Student B"},
                "total_score": 85
            }
        ]

        result = anonymize_evaluation_list(team_evaluations, requester_role="instructor")

        assert result[0]["evaluator"]["name"] == "Student A"
        assert result[0]["evaluator"]["email"] == "student_a@example.com"

    def test_aggregated_scores_remain_visible(self):
        """
        Aggregated statistics should remain visible even when
        individual evaluator identities are hidden.
        """
        report = {
            "team": {"id": 1, "name": "Team A"},
            "statistics": {
                "total_evaluations": 10,
                "average_score": 87.5,
                "total_members": 5
            },
            "members": [
                {
                    "member": {"id": 456, "name": "Alice"},
                    "average_score": 88.0,
                    "evaluations_received": 4,
                    "evaluations": [
                        {
                            "evaluator": {"id": 123, "name": "John Doe"},
                            "total_score": 85
                        }
                    ]
                }
            ]
        }

        result = anonymize_report_data(report, requester_role="student")

        # Statistics should remain
        assert result["statistics"]["total_evaluations"] == 10
        assert result["statistics"]["average_score"] == 87.5

        # But evaluator identities should be hidden
        assert result["members"][0]["evaluations"][0]["evaluator"]["name"] == "Anonymous"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_missing_evaluator_field(self):
        """Should handle missing evaluator field gracefully."""
        evaluation = {
            "id": 1,
            "total_score": 85
        }

        result = anonymize_evaluator(evaluation, requester_role="student")

        # Should not crash and should still process
        assert result["id"] == 1
        assert result["total_score"] == 85

    def test_null_evaluator(self):
        """Should handle null evaluator gracefully."""
        evaluation = {
            "id": 1,
            "evaluator": None,
            "total_score": 85
        }

        result = anonymize_evaluator(evaluation, requester_role="student")

        # Should not crash
        assert result["id"] == 1

    def test_empty_report(self):
        """Should handle empty report structure."""
        report = {}
        result = anonymize_report_data(report, requester_role="student")
        assert result == {}

    def test_unknown_role(self):
        """Unknown roles should default to anonymization."""
        evaluation = {
            "id": 1,
            "evaluator": {"id": 123, "name": "John Doe", "email": "john@example.com"}
        }

        result = anonymize_evaluator(evaluation, requester_role="unknown_role")

        # Should anonymize for safety
        assert result["evaluator"]["name"] == "Anonymous"
