# Bulk User Upload - CSV Feature

## Overview
OPETSE-20 implements bulk user upload functionality via CSV files, allowing instructors to efficiently onboard entire classes of students.

## Features
- ✅ CSV file upload and parsing
- ✅ Validation of email addresses and required fields
- ✅ Support for both student and instructor roles
- ✅ Duplicate email detection and skipping
- ✅ Detailed upload results with success/failure breakdown
- ✅ CSV template download
- ✅ Instructor-only access (RBAC protected)

## CSV Format

### Required Headers
- `email` - Valid email address (must be unique)
- `name` - User's full name

### Optional Headers
- `role` - User role: `student` or `instructor` (defaults to `student`)

### Example CSV
```csv
email,name,role
student1@example.com,John Doe,student
student2@example.com,Jane Smith,student
instructor@example.com,Dr. Brown,instructor
```

## API Endpoint

### POST /api/v1/users/bulk-upload

**Authentication:** Requires instructor role

**Request:**
- Content-Type: `multipart/form-data`
- Body: CSV file

**Response:**
```json
{
  "success": true,
  "message": "Bulk upload completed. Created 10 users.",
  "summary": {
    "total_in_csv": 12,
    "created": 10,
    "skipped": 1,
    "failed": 1
  },
  "created_users": [...],
  "skipped_users": [
    {
      "email": "existing@example.com",
      "reason": "Email already exists"
    }
  ],
  "failed_users": [
    {
      "email": "invalid@",
      "reason": "Invalid email format"
    }
  ],
  "validation_errors": []
}
```

## Validation Rules

1. **Email Validation**
   - Must not be empty
   - Must contain `@` symbol
   - Must have domain with `.`
   - Converted to lowercase
   - Must be unique in database

2. **Name Validation**
   - Must not be empty
   - Whitespace is trimmed

3. **Role Validation**
   - Must be either `student` or `instructor`
   - Defaults to `student` if not provided
   - Case-insensitive

## Error Handling

The system provides detailed error reporting:

- **CSV Format Errors**: Invalid file type, encoding issues, missing headers
- **Validation Errors**: Invalid email, missing name, invalid role
- **Database Errors**: Duplicate emails, insert failures
- **Partial Success**: Some users created, others skipped/failed

## Frontend Component

Located at: `src/pages/BulkUserUpload.jsx`

Features:
- File selection with `.csv` restriction
- Template download button
- Upload progress indicator
- Detailed results display
- Error handling and user feedback
- Role-based access control (Instructor only)

## Testing

Run CSV upload tests:
```bash
pytest -m csv
```

Test coverage includes:
- CSV header validation
- Row validation (email, name, role)
- CSV parsing with various encodings
- Bulk processing logic
- API endpoint existence and RBAC
