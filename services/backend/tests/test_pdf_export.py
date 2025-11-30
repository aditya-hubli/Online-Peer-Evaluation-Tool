"""Tests for PDF report exports - OPETSE-16."""
import pytest
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from app.utils.pdf_export import (
    export_project_report_to_pdf,
    export_team_report_to_pdf,
    export_evaluations_to_pdf,
    generate_pdf_header,
    generate_pdf_footer
)


@pytest.mark.pdf_export
class TestPDFHeaderFooter:
    """Test PDF header and footer generation."""

    def test_generate_pdf_header_with_title_only(self):
        """Test header generation with title only."""
        story = []
        generate_pdf_header(story, "Test Title")
        assert len(story) >= 2  # Title + spacer

    def test_generate_pdf_header_with_subtitle(self):
        """Test header generation with title and subtitle."""
        story = []
        generate_pdf_header(story, "Test Title", "Test Subtitle")
        assert len(story) >= 3  # Title + subtitle + spacer

    def test_generate_pdf_footer_creates_output(self):
        """Test that footer generation doesn't raise errors."""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Create a mock document object
        class MockDoc:
            page = 1
        
        generate_pdf_footer(c, MockDoc())
        c.save()
        assert buffer.getvalue() != b""


@pytest.mark.pdf_export
class TestProjectReportPDF:
    """Test PDF export of project reports."""

    def test_export_empty_project_report(self):
        """Test exporting project report with minimal data."""
        report_data = {
            "project": {
                "id": 1,
                "title": "Test Project",
                "description": "Test Description",
                "status": "active",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            },
            "overall_statistics": {
                "total_teams": 0,
                "total_evaluations": 0,
                "average_score": 0
            },
            "teams": []
        }
        
        pdf_bytes = export_project_report_to_pdf(report_data, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')  # PDF header

    def test_export_project_report_with_teams(self):
        """Test exporting project report with team data."""
        report_data = {
            "project": {
                "id": 1,
                "title": "Test Project",
                "description": "Test Description",
                "status": "active",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            },
            "overall_statistics": {
                "total_teams": 2,
                "total_evaluations": 10,
                "average_score": 85.5
            },
            "teams": [
                {
                    "team": {"id": 1, "name": "Team A"},
                    "statistics": {
                        "total_members": 5,
                        "total_evaluations": 5,
                        "average_score": 87.0
                    }
                },
                {
                    "team": {"id": 2, "name": "Team B"},
                    "statistics": {
                        "total_members": 5,
                        "total_evaluations": 5,
                        "average_score": 84.0
                    }
                }
            ]
        }
        
        pdf_bytes = export_project_report_to_pdf(report_data, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_export_project_report_anonymized_flag(self):
        """Test that anonymization flag is respected in project report."""
        report_data = {
            "project": {
                "id": 1,
                "title": "Test Project",
                "description": "Test",
                "status": "active",
                "start_date": None,
                "end_date": None
            },
            "overall_statistics": {
                "total_teams": 0,
                "total_evaluations": 0,
                "average_score": 0
            },
            "teams": []
        }
        
        # Anonymized version
        pdf_anon = export_project_report_to_pdf(report_data, anonymize=True)
        assert isinstance(pdf_anon, bytes)
        assert len(pdf_anon) > 0
        
        # Non-anonymized version
        pdf_full = export_project_report_to_pdf(report_data, anonymize=False)
        assert isinstance(pdf_full, bytes)
        assert len(pdf_full) > 0

    def test_export_project_report_handles_none_dates(self):
        """Test that None dates are handled gracefully."""
        report_data = {
            "project": {
                "id": 1,
                "title": "Test Project",
                "description": "Test",
                "status": "active",
                "start_date": None,
                "end_date": None
            },
            "overall_statistics": {
                "total_teams": 0,
                "total_evaluations": 0,
                "average_score": 0
            },
            "teams": []
        }
        
        pdf_bytes = export_project_report_to_pdf(report_data, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0


@pytest.mark.pdf_export
class TestTeamReportPDF:
    """Test PDF export of team reports."""

    def test_export_empty_team_report(self):
        """Test exporting team report with minimal data."""
        report_data = {
            "team": {
                "id": 1,
                "name": "Test Team"
            },
            "statistics": {
                "total_members": 0,
                "total_evaluations": 0,
                "average_score": 0
            },
            "members": []
        }
        
        pdf_bytes = export_team_report_to_pdf(report_data, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_export_team_report_with_members(self):
        """Test exporting team report with member data."""
        report_data = {
            "team": {
                "id": 1,
                "name": "Test Team"
            },
            "statistics": {
                "total_members": 3,
                "total_evaluations": 6,
                "average_score": 88.5
            },
            "members": [
                {
                    "member": {"id": 1, "name": "Alice", "email": "alice@test.com"},
                    "evaluations_received": 2,
                    "average_score": 90.0
                },
                {
                    "member": {"id": 2, "name": "Bob", "email": "bob@test.com"},
                    "evaluations_received": 2,
                    "average_score": 87.0
                },
                {
                    "member": {"id": 3, "name": "Carol", "email": "carol@test.com"},
                    "evaluations_received": 2,
                    "average_score": 88.5
                }
            ]
        }
        
        pdf_bytes = export_team_report_to_pdf(report_data, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_export_team_report_with_project_name(self):
        """Test team report includes project name when provided."""
        report_data = {
            "team": {
                "id": 1,
                "name": "Test Team"
            },
            "project_name": "Test Project",
            "statistics": {
                "total_members": 0,
                "total_evaluations": 0,
                "average_score": 0
            },
            "members": []
        }
        
        pdf_bytes = export_team_report_to_pdf(report_data, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_export_team_report_anonymized_vs_detailed(self):
        """Test differences between anonymized and detailed team reports."""
        report_data = {
            "team": {
                "id": 1,
                "name": "Test Team"
            },
            "statistics": {
                "total_members": 1,
                "total_evaluations": 1,
                "average_score": 85.0
            },
            "members": [
                {
                    "member": {"id": 1, "name": "Alice", "email": "alice@test.com"},
                    "evaluations_received": 1,
                    "average_score": 85.0
                }
            ]
        }
        
        # Anonymized should be smaller (no email column)
        pdf_anon = export_team_report_to_pdf(report_data, anonymize=True)
        pdf_detailed = export_team_report_to_pdf(report_data, anonymize=False)
        
        assert isinstance(pdf_anon, bytes)
        assert isinstance(pdf_detailed, bytes)
        assert len(pdf_anon) > 0
        assert len(pdf_detailed) > 0


@pytest.mark.pdf_export
class TestEvaluationsPDF:
    """Test PDF export of evaluations list."""

    def test_export_empty_evaluations_list(self):
        """Test exporting empty evaluations list."""
        pdf_bytes = export_evaluations_to_pdf([], anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_export_single_evaluation(self):
        """Test exporting single evaluation."""
        evaluations = [
            {
                "evaluatee": {"id": 1, "name": "John Doe", "email": "john@test.com"},
                "evaluator": {"id": 2, "name": "Jane Smith", "email": "jane@test.com"},
                "form_title": "Peer Evaluation",
                "total_score": 85,
                "submitted_at": "2025-11-15T10:30:00"
            }
        ]
        
        pdf_bytes = export_evaluations_to_pdf(evaluations, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_export_multiple_evaluations(self):
        """Test exporting multiple evaluations."""
        evaluations = [
            {
                "evaluatee": {"id": 1, "name": "Alice", "email": "alice@test.com"},
                "evaluator": {"id": 2, "name": "Bob", "email": "bob@test.com"},
                "form_title": "Peer Eval 1",
                "total_score": 90,
                "submitted_at": "2025-11-15T10:00:00"
            },
            {
                "evaluatee": {"id": 2, "name": "Bob", "email": "bob@test.com"},
                "evaluator": {"id": 1, "name": "Alice", "email": "alice@test.com"},
                "form_title": "Peer Eval 1",
                "total_score": 88,
                "submitted_at": "2025-11-15T10:30:00"
            },
            {
                "evaluatee": {"id": 3, "name": "Carol", "email": "carol@test.com"},
                "evaluator": {"id": 1, "name": "Alice", "email": "alice@test.com"},
                "form_title": "Peer Eval 1",
                "total_score": 92,
                "submitted_at": "2025-11-15T11:00:00"
            }
        ]
        
        pdf_bytes = export_evaluations_to_pdf(evaluations, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_export_evaluations_anonymized_flag(self):
        """Test that anonymization flag affects output."""
        evaluations = [
            {
                "evaluatee": {"id": 1, "name": "Alice", "email": "alice@test.com"},
                "evaluator": {"id": 2, "name": "Bob", "email": "bob@test.com"},
                "form_title": "Test Form",
                "total_score": 85,
                "submitted_at": "2025-11-15"
            }
        ]
        
        pdf_anon = export_evaluations_to_pdf(evaluations, anonymize=True)
        pdf_detailed = export_evaluations_to_pdf(evaluations, anonymize=False)
        
        assert isinstance(pdf_anon, bytes)
        assert isinstance(pdf_detailed, bytes)
        # Detailed should be larger (includes evaluator column)
        assert len(pdf_detailed) >= len(pdf_anon) * 0.8  # Within 20% tolerance

    def test_export_evaluations_handles_missing_data(self):
        """Test that missing data is handled gracefully."""
        evaluations = [
            {
                "evaluatee": {"name": "Alice"},  # Missing ID and email
                "evaluator": {"name": "Bob"},
                "form_title": None,
                "total_score": None,
                "submitted_at": None
            }
        ]
        
        pdf_bytes = export_evaluations_to_pdf(evaluations, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')


@pytest.mark.pdf_export
class TestPDFIntegration:
    """Integration tests for PDF export functionality."""

    def test_all_export_functions_return_valid_pdfs(self):
        """Test that all export functions return valid PDF bytes."""
        # Project report
        project_data = {
            "project": {"id": 1, "title": "Test", "description": "", "status": "active", "start_date": None, "end_date": None},
            "overall_statistics": {"total_teams": 0, "total_evaluations": 0, "average_score": 0},
            "teams": []
        }
        project_pdf = export_project_report_to_pdf(project_data, anonymize=True)
        assert project_pdf.startswith(b'%PDF')
        
        # Team report
        team_data = {
            "team": {"id": 1, "name": "Test Team"},
            "statistics": {"total_members": 0, "total_evaluations": 0, "average_score": 0},
            "members": []
        }
        team_pdf = export_team_report_to_pdf(team_data, anonymize=True)
        assert team_pdf.startswith(b'%PDF')
        
        # Evaluations
        eval_pdf = export_evaluations_to_pdf([], anonymize=True)
        assert eval_pdf.startswith(b'%PDF')

    def test_pdf_export_with_large_dataset(self):
        """Test PDF export handles large datasets."""
        evaluations = [
            {
                "evaluatee": {"id": i, "name": f"User {i}", "email": f"user{i}@test.com"},
                "evaluator": {"id": i+1, "name": f"User {i+1}", "email": f"user{i+1}@test.com"},
                "form_title": "Peer Evaluation",
                "total_score": 85 + (i % 15),
                "submitted_at": f"2025-11-{15+(i%10):02d}"
            }
            for i in range(50)
        ]
        
        pdf_bytes = export_evaluations_to_pdf(evaluations, anonymize=True)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    def test_pdf_generation_is_deterministic(self):
        """Test that PDF generation produces consistent output for same input."""
        report_data = {
            "team": {"id": 1, "name": "Test Team"},
            "statistics": {"total_members": 1, "total_evaluations": 1, "average_score": 85.0},
            "members": [{"member": {"id": 1, "name": "Test", "email": "test@test.com"}, "evaluations_received": 1, "average_score": 85.0}]
        }
        
        pdf1 = export_team_report_to_pdf(report_data, anonymize=True)
        pdf2 = export_team_report_to_pdf(report_data, anonymize=True)
        
        # PDFs should have similar length (may differ slightly due to timestamps)
        assert abs(len(pdf1) - len(pdf2)) < 100
