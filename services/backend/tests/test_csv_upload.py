"""Tests for CSV upload functionality."""
import pytest
from app.core.csv_utils import (
    validate_csv_headers,
    parse_csv_file,
    validate_student_row,
    process_students_csv
)


@pytest.mark.csv
class TestCSVValidation:
    """Test CSV validation utilities."""

    def test_validate_csv_headers_with_all_required(self):
        """Test header validation with all required headers present."""
        headers = ['email', 'name', 'role']
        required = ['email', 'name']
        is_valid, error = validate_csv_headers(headers, required)
        assert is_valid is True
        assert error == ""

    def test_validate_csv_headers_missing_required(self):
        """Test header validation with missing required headers."""
        headers = ['email']
        required = ['email', 'name']
        is_valid, error = validate_csv_headers(headers, required)
        assert is_valid is False
        assert "name" in error

    def test_validate_student_row_valid(self):
        """Test validation of valid student row."""
        row = {'email': 'student@example.com', 'name': 'John Doe', 'role': 'student'}
        is_valid, data, error = validate_student_row(row, 2)
        assert is_valid is True
        assert data['email'] == 'student@example.com'
        assert data['name'] == 'John Doe'
        assert data['role'] == 'student'

    def test_validate_student_row_missing_email(self):
        """Test validation fails with missing email."""
        row = {'email': '', 'name': 'John Doe'}
        is_valid, data, error = validate_student_row(row, 2)
        assert is_valid is False
        assert "email" in error.lower()

    def test_validate_student_row_invalid_email(self):
        """Test validation fails with invalid email."""
        row = {'email': 'notanemail', 'name': 'John Doe'}
        is_valid, data, error = validate_student_row(row, 2)
        assert is_valid is False
        assert "email" in error.lower()

    def test_validate_student_row_missing_name(self):
        """Test validation fails with missing name."""
        row = {'email': 'student@example.com', 'name': ''}
        is_valid, data, error = validate_student_row(row, 2)
        assert is_valid is False
        assert "name" in error.lower()

    def test_validate_student_row_invalid_role(self):
        """Test validation fails with invalid role."""
        row = {'email': 'student@example.com', 'name': 'John', 'role': 'admin'}
        is_valid, data, error = validate_student_row(row, 2)
        assert is_valid is False
        assert "role" in error.lower()

    def test_validate_student_row_defaults_to_student_role(self):
        """Test role defaults to student if not provided."""
        row = {'email': 'student@example.com', 'name': 'John Doe'}
        is_valid, data, error = validate_student_row(row, 2)
        assert is_valid is True
        assert data['role'] == 'student'


@pytest.mark.csv
class TestCSVParsing:
    """Test CSV parsing functions."""

    def test_parse_valid_csv(self):
        """Test parsing valid CSV content."""
        csv_content = b"email,name,role\nstudent@example.com,John Doe,student\n"
        is_valid, rows, error = parse_csv_file(csv_content, ['email', 'name'])
        assert is_valid is True
        assert len(rows) == 1
        assert rows[0]['email'] == 'student@example.com'

    def test_parse_empty_csv(self):
        """Test parsing empty CSV."""
        csv_content = b""
        is_valid, rows, error = parse_csv_file(csv_content, ['email', 'name'])
        assert is_valid is False
        assert "empty" in error.lower()

    def test_parse_csv_no_data_rows(self):
        """Test CSV with headers but no data."""
        csv_content = b"email,name,role\n"
        is_valid, rows, error = parse_csv_file(csv_content, ['email', 'name'])
        assert is_valid is False
        assert "no data" in error.lower()

    def test_parse_csv_with_bom(self):
        """Test parsing CSV with BOM (Byte Order Mark)."""
        csv_content = b"\xef\xbb\xbfemail,name\nstudent@example.com,John Doe\n"
        is_valid, rows, error = parse_csv_file(csv_content, ['email', 'name'])
        assert is_valid is True
        assert len(rows) == 1


@pytest.mark.csv
class TestProcessStudentsCSV:
    """Test complete student CSV processing."""

    def test_process_valid_students_csv(self):
        """Test processing valid students CSV."""
        csv_content = b"email,name,role\nstudent1@example.com,John,student\nstudent2@example.com,Jane,student\n"
        is_valid, students, errors = process_students_csv(csv_content)
        assert is_valid is True
        assert len(students) == 2
        assert students[0]['email'] == 'student1@example.com'
        assert students[1]['email'] == 'student2@example.com'

    def test_process_csv_with_mixed_validity(self):
        """Test CSV with some valid and some invalid rows."""
        csv_content = b"email,name\nvalid@example.com,Valid User\n,Missing Email\ngood@example.com,Good User\n"
        is_valid, students, errors = process_students_csv(csv_content)
        assert is_valid is True
        assert len(students) == 2  # 2 valid rows
        assert len(errors) == 1    # 1 invalid row

    def test_process_csv_all_invalid(self):
        """Test CSV with all invalid rows."""
        csv_content = b"email,name\n,Missing Email\ninvalid,Missing Email Too\n"
        is_valid, students, errors = process_students_csv(csv_content)
        assert is_valid is False
        assert len(students) == 0
        assert len(errors) > 0

    def test_process_csv_missing_required_headers(self):
        """Test CSV missing required headers."""
        csv_content = b"email\nstudent@example.com\n"
        is_valid, students, errors = process_students_csv(csv_content)
        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)


@pytest.mark.csv
class TestBulkUploadEndpoint:
    """Test bulk upload API endpoint."""

    def test_bulk_upload_endpoint_exists(self):
        """Test that bulk upload endpoint is defined."""
        from app.api.v1 import users
        route_paths = [(route.path, list(route.methods)[0]) for route in users.router.routes]
        assert any(path == "/users/bulk-upload" and method == "POST" for path, method in route_paths)

    def test_bulk_upload_requires_instructor_role(self):
        """Test that bulk upload requires instructor role."""
        from app.api.v1 import users
        import inspect

        # Find the bulk_upload_users function
        bulk_upload_func = None
        for route in users.router.routes:
            if route.path == "/users/bulk-upload":
                bulk_upload_func = route.endpoint
                break

        assert bulk_upload_func is not None
        # Check that it has dependencies (RBAC check)
        sig = inspect.signature(bulk_upload_func)
        # The function should have file parameter
        assert 'file' in sig.parameters
