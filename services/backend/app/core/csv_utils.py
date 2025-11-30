"""CSV utility functions for bulk uploads."""
import csv
import io
from typing import List, Dict, Any
from pydantic import EmailStr, ValidationError


def validate_csv_headers(headers: List[str], required_headers: List[str]) -> tuple[bool, str]:
    """
    Validate that CSV has all required headers.

    Args:
        headers: List of headers from CSV
        required_headers: List of required header names

    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_headers = set(required_headers) - set(headers)
    if missing_headers:
        return False, f"Missing required headers: {', '.join(missing_headers)}"
    return True, ""


def parse_csv_file(file_content: bytes, required_headers: List[str]) -> tuple[bool, List[Dict[str, Any]], str]:
    """
    Parse CSV file content and validate structure.

    Args:
        file_content: Raw bytes of CSV file
        required_headers: List of required header names

    Returns:
        Tuple of (is_valid, parsed_data, error_message)
    """
    try:
        # Decode bytes to string
        content_str = file_content.decode('utf-8-sig')  # Handle BOM

        # Parse CSV
        csv_file = io.StringIO(content_str)
        reader = csv.DictReader(csv_file)

        # Validate headers
        if not reader.fieldnames:
            return False, [], "CSV file is empty or has no headers"

        is_valid, error_msg = validate_csv_headers(list(reader.fieldnames), required_headers)
        if not is_valid:
            return False, [], error_msg

        # Read all rows
        rows = list(reader)

        if not rows:
            return False, [], "CSV file has no data rows"

        return True, rows, ""

    except UnicodeDecodeError:
        return False, [], "Invalid file encoding. Please use UTF-8 encoding."
    except csv.Error as e:
        return False, [], f"CSV parsing error: {str(e)}"
    except Exception as e:
        return False, [], f"Unexpected error parsing CSV: {str(e)}"


def validate_student_row(row: Dict[str, str], row_number: int) -> tuple[bool, Dict[str, Any], str]:
    """
    Validate a single student row from CSV.

    Args:
        row: Dictionary of row data
        row_number: Row number for error reporting

    Returns:
        Tuple of (is_valid, validated_data, error_message)
    """
    errors = []
    validated = {}

    # Validate email
    email = row.get('email', '').strip()
    if not email:
        errors.append(f"Row {row_number}: Email is required")
    else:
        try:
            # Basic email validation
            if '@' not in email or '.' not in email.split('@')[1]:
                errors.append(f"Row {row_number}: Invalid email format")
            else:
                validated['email'] = email.lower()
        except Exception:
            errors.append(f"Row {row_number}: Invalid email format")

    # Validate name
    name = row.get('name', '').strip()
    if not name:
        errors.append(f"Row {row_number}: Name is required")
    else:
        validated['name'] = name

    # Validate role (optional, defaults to student)
    role = row.get('role', 'student').strip().lower()
    if role not in ['student', 'instructor']:
        errors.append(f"Row {row_number}: Invalid role. Must be 'student' or 'instructor'")
    else:
        validated['role'] = role

    if errors:
        return False, {}, "; ".join(errors)

    return True, validated, ""


def process_students_csv(file_content: bytes) -> tuple[bool, List[Dict[str, Any]], List[str]]:
    """
    Process a CSV file containing student data.

    Args:
        file_content: Raw bytes of CSV file

    Returns:
        Tuple of (is_valid, valid_students, errors_list)
    """
    required_headers = ['email', 'name']

    # Parse CSV
    is_valid, rows, error = parse_csv_file(file_content, required_headers)
    if not is_valid:
        return False, [], [error]

    # Validate each row
    valid_students = []
    errors = []

    for idx, row in enumerate(rows, start=2):  # Start at 2 (header is row 1)
        is_valid_row, validated_data, error_msg = validate_student_row(row, idx)

        if is_valid_row:
            valid_students.append(validated_data)
        else:
            errors.append(error_msg)

    # Return results
    if not valid_students:
        return False, [], errors if errors else ["No valid student records found"]

    return True, valid_students, errors
