"""Password strength validation - SRS requirement S25 (OPETSE-28)."""
import re
from typing import Tuple


class PasswordValidationError(ValueError):
    """Custom exception for password validation failures."""
    pass


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to SRS requirement S25.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

    Args:
        password: The password string to validate

    Returns:
        Tuple of (is_valid: bool, message: str)
        - If valid: (True, "Password meets all requirements")
        - If invalid: (False, "Specific error message")

    Raises:
        PasswordValidationError: If password is None or empty
    """
    if not password:
        raise PasswordValidationError("Password cannot be empty")

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit (0-9)"

    # Check for special characters
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"

    return True, "Password meets all security requirements"


def get_password_strength_criteria() -> dict:
    """
    Get password strength requirements for client-side validation feedback.

    Returns:
        dict with validation criteria
    """
    return {
        "min_length": 8,
        "requires_uppercase": True,
        "requires_lowercase": True,
        "requires_digit": True,
        "requires_special_char": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
        "description": "Password must contain: 8+ chars, uppercase, lowercase, digit, special char"
    }
