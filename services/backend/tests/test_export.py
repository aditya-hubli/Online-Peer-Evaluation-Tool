"""Tests for anonymized report exports - OPETSE-32."""
import pytest
from app.utils.export import (
    export_evaluations_to_csv,
    export_team_report_to_csv,
    export_project_report_to_csv,
    determine_anonymization
)


@pytest.mark.export
class TestAnonymizationDetermination:
    """Test anonymization logic based on user roles."""

    def test_student_role_requires_anonymization(self):
        """Test that student role requires anonymized exports."""
        assert determine_anonymization("student") is True

    def test_instructor_role_no_anonymization(self):
        """Test that instructor role gets non-anonymized exports."""
        assert determine_anonymization("instructor") is False

    def test_admin_role_no_anonymization(self):
        """Test that admin role gets non-anonymized exports."""
        assert determine_anonymization("admin") is False

    def test_none_role_requires_anonymization(self):
        """Test that undefined role defaults to anonymization."""
        assert determine_anonymization(None) is True

    def test_unknown_role_requires_anonymization(self):
        """Test that unknown role defaults to anonymization."""
        assert determine_anonymization("unknown") is True


@pytest.mark.export
class TestEvaluationsCSVExport:
    """Test CSV export of evaluations with anonymization."""

    def test_export_empty_evaluations_returns_empty_string(self):
        """Test that exporting empty list returns empty string."""
        result = export_evaluations_to_csv([])
        assert result == ""

    def test_export_anonymized_evaluations_hides_rater_identity(self):
        """Test that anonymized export hides rater names and emails."""
        evaluations = [{
            "evaluatee": {"name": "John Doe", "email": "john@example.com"},
            "evaluator": {"name": "Jane Smith", "email": "jane@example.com"},
            "total_score": 85,
            "comments": "Good work",
            "created_at": "2025-01-01",
            "form_title": "Peer Evaluation"
        }]

        csv_output = export_evaluations_to_csv(evaluations, anonymize=True)

        assert "Anonymous Peer" in csv_output
        assert "Jane Smith" not in csv_output
        assert "jane@example.com" not in csv_output
        assert "John Doe" in csv_output
        assert "john@example.com" in csv_output

    def test_export_non_anonymized_evaluations_shows_rater_identity(self):
        """Test that non-anonymized export shows rater details."""
        evaluations = [{
            "evaluatee": {"name": "John Doe", "email": "john@example.com"},
            "evaluator": {"name": "Jane Smith", "email": "jane@example.com"},
            "total_score": 85,
            "comments": "Good work"
        }]

        csv_output = export_evaluations_to_csv(evaluations, anonymize=False)

        assert "Jane Smith" in csv_output
        assert "jane@example.com" in csv_output
        assert "John Doe" in csv_output

    def test_export_includes_metadata_when_requested(self):
        """Test that metadata columns are included when requested."""
        evaluations = [{
            "evaluatee": {"name": "John Doe", "email": "john@example.com"},
            "evaluator": {"name": "Jane Smith", "email": "jane@example.com"},
            "total_score": 85,
            "comments": "Good work",
            "created_at": "2025-01-01 10:00:00",
            "form_title": "Peer Evaluation"
        }]

        csv_output = export_evaluations_to_csv(evaluations, anonymize=True, include_metadata=True)

        assert "Submitted At" in csv_output
        assert "Form Title" in csv_output
        assert "2025-01-01 10:00:00" in csv_output
        assert "Peer Evaluation" in csv_output

    def test_export_excludes_metadata_when_not_requested(self):
        """Test that metadata columns are excluded when not requested."""
        evaluations = [{
            "evaluatee": {"name": "John Doe", "email": "john@example.com"},
            "evaluator": {"name": "Jane Smith", "email": "jane@example.com"},
            "total_score": 85,
            "comments": "Good work"
        }]

        csv_output = export_evaluations_to_csv(evaluations, anonymize=True, include_metadata=False)

        assert "Submitted At" not in csv_output
        assert "Form Title" not in csv_output


@pytest.mark.export
class TestTeamReportCSVExport:
    """Test CSV export of team reports with anonymization."""

    def test_export_team_report_includes_team_summary(self):
        """Test that team report includes summary information."""
        team_data = {
            "name": "Team Alpha",
            "project_name": "Project X",
            "statistics": {
                "total_members": 5,
                "total_evaluations": 20,
                "average_score": 82.5
            },
            "members": []
        }

        csv_output = export_team_report_to_csv(team_data, anonymize=True)

        assert "Team Alpha" in csv_output
        assert "Project X" in csv_output
        assert "5" in csv_output
        assert "20" in csv_output
        assert "82.5" in csv_output

    def test_export_anonymized_team_report_shows_aggregated_scores(self):
        """Test that anonymized team report shows aggregated member scores."""
        team_data = {
            "name": "Team Alpha",
            "statistics": {"total_members": 2, "total_evaluations": 4, "average_score": 80},
            "members": [
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "average_score": 85,
                    "evaluations": [
                        {"evaluator": {"name": "Jane"}, "total_score": 85}
                    ]
                }
            ]
        }

        csv_output = export_team_report_to_csv(team_data, anonymize=True)

        assert "John Doe" in csv_output
        assert "85" in csv_output
        assert "Jane" not in csv_output
        assert "Average Score" in csv_output
        assert "Evaluation Count" in csv_output

    def test_export_non_anonymized_team_report_shows_detailed_evaluations(self):
        """Test that non-anonymized team report shows individual ratings."""
        team_data = {
            "name": "Team Alpha",
            "statistics": {"total_members": 1, "total_evaluations": 2, "average_score": 80},
            "members": [
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "evaluations": [
                        {
                            "evaluator": {"name": "Jane Smith", "email": "jane@example.com"},
                            "total_score": 85,
                            "comments": "Excellent"
                        }
                    ]
                }
            ]
        }

        csv_output = export_team_report_to_csv(team_data, anonymize=False)

        assert "Jane Smith" in csv_output
        assert "jane@example.com" in csv_output
        assert "Excellent" in csv_output
        assert "Rater Name" in csv_output


@pytest.mark.export
class TestProjectReportCSVExport:
    """Test CSV export of project reports with anonymization."""

    def test_export_project_report_includes_project_summary(self):
        """Test that project report includes summary information."""
        project_data = {
            "project": {
                "title": "Project X",
                "description": "A great project"
            },
            "overall_statistics": {
                "total_teams": 3,
                "total_evaluations": 30,
                "average_score": 78.5,
                "participation_rate": 95
            },
            "teams": []
        }

        csv_output = export_project_report_to_csv(project_data, anonymize=True)

        assert "Project X" in csv_output
        assert "A great project" in csv_output
        assert "3" in csv_output
        assert "30" in csv_output
        assert "78.5" in csv_output
        assert "95" in csv_output

    def test_export_anonymized_project_report_shows_team_summaries(self):
        """Test that anonymized project report shows aggregated team data."""
        project_data = {
            "project": {"title": "Project X"},
            "overall_statistics": {"total_teams": 1, "total_evaluations": 10, "average_score": 80},
            "teams": [
                {
                    "name": "Team Alpha",
                    "members": [
                        {"name": "John", "evaluations": []},
                        {"name": "Jane", "evaluations": []}
                    ],
                    "statistics": {
                        "average_score": 82,
                        "total_evaluations": 5
                    }
                }
            ]
        }

        csv_output = export_project_report_to_csv(project_data, anonymize=True)

        assert "Team Alpha" in csv_output
        assert "2" in csv_output  # Number of members
        assert "82" in csv_output  # Team average
        assert "Team Name" in csv_output
        assert "Members" in csv_output

    def test_export_non_anonymized_project_report_shows_individual_ratings(self):
        """Test that non-anonymized project report shows all evaluation details."""
        project_data = {
            "project": {"title": "Project X"},
            "overall_statistics": {"total_teams": 1, "total_evaluations": 1, "average_score": 85},
            "teams": [
                {
                    "name": "Team Alpha",
                    "members": [
                        {
                            "name": "John Doe",
                            "evaluations": [
                                {
                                    "evaluator": {"name": "Jane Smith"},
                                    "total_score": 85,
                                    "comments": "Great work"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        csv_output = export_project_report_to_csv(project_data, anonymize=False)

        assert "Jane Smith" in csv_output
        assert "Great work" in csv_output
        assert "Rater Name" in csv_output


@pytest.mark.export
class TestExportEndpoints:
    """Test export API endpoints."""

    def test_project_export_endpoint_exists(self):
        """Test that project export endpoint is defined."""
        from app.api.v1 import reports
        route_paths = [(route.path, list(route.methods)[0]) for route in reports.router.routes]
        assert any("/reports/project/{project_id}/export" in path and method == "GET" for path, method in route_paths)

    def test_team_export_endpoint_exists(self):
        """Test that team export endpoint is defined."""
        from app.api.v1 import reports
        route_paths = [(route.path, list(route.methods)[0]) for route in reports.router.routes]
        assert any("/reports/team/{team_id}/export" in path and method == "GET" for path, method in route_paths)

    def test_evaluations_export_endpoint_exists(self):
        """Test that evaluations export endpoint is defined."""
        from app.api.v1 import reports
        route_paths = [(route.path, list(route.methods)[0]) for route in reports.router.routes]
        assert any("/reports/evaluations/export" in path and method == "GET" for path, method in route_paths)
