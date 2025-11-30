"""Test password strength validation - OPETSE-28 (SRS S25)."""
import pytest
from pathlib import Path
from app.core.password_validator import validate_password_strength, PasswordValidationError, get_password_strength_criteria


class TestPasswordStrengthValidation:
    """Test suite for password strength validation."""

    def test_valid_strong_password(self):
        """Test that a strong password passes validation."""
        password = "SecurePass123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert "meets all security requirements" in message.lower()

    def test_valid_strong_password_complex(self):
        """Test another valid strong password with different special characters."""
        password = "MyPassword@2024#ABC"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True

    def test_password_too_short(self):
        """Test that password shorter than 8 chars fails."""
        password = "Pass1!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "8 characters" in message

    def test_password_missing_uppercase(self):
        """Test that password without uppercase letter fails."""
        password = "secure123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "uppercase" in message.lower()

    def test_password_missing_lowercase(self):
        """Test that password without lowercase letter fails."""
        password = "SECURE123!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "lowercase" in message.lower()

    def test_password_missing_digit(self):
        """Test that password without digit fails."""
        password = "SecurePass!"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "digit" in message.lower()

    def test_password_missing_special_char(self):
        """Test that password without special character fails."""
        password = "SecurePass123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "special character" in message.lower()

    def test_password_empty_raises_error(self):
        """Test that empty password raises PasswordValidationError."""
        with pytest.raises(PasswordValidationError):
            validate_password_strength("")

    def test_password_none_raises_error(self):
        """Test that None password raises PasswordValidationError."""
        with pytest.raises(PasswordValidationError):
            validate_password_strength(None)

    def test_password_all_requirements_met(self):
        """Test password that meets all requirements."""
        password = "Test@12345"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True

    def test_special_char_variations(self):
        """Test various special characters are accepted."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        base_password = "ValidPass1"

        for char in special_chars:
            password = f"{base_password}{char}"
            is_valid, message = validate_password_strength(password)
            assert is_valid is True, f"Failed with special char: {char}"

    def test_get_password_strength_criteria(self):
        """Test that password criteria are returned correctly."""
        criteria = get_password_strength_criteria()

        assert criteria["min_length"] == 8
        assert criteria["requires_uppercase"] is True
        assert criteria["requires_lowercase"] is True
        assert criteria["requires_digit"] is True
        assert criteria["requires_special_char"] is True
        assert "special_chars" in criteria
        assert criteria["description"] != ""


class TestPasswordValidatorIntegration:
    """Integration tests for password validator."""

    def test_weak_passwords_all_fail(self):
        """Test that all weak passwords fail validation."""
        weak_passwords = [
            "123456",           # No letters or special chars
            "password",         # No uppercase, digits, or special chars
            "PASSWORD",         # No lowercase, digits, or special chars
            "Pass1",            # Too short, no special char
            "Pass!!!",          # No digits
            "1234567890",       # No letters or special chars
            "abcdefgh",         # Only lowercase
            "ABCDEFGH",         # Only uppercase
        ]

        for weak_pass in weak_passwords:
            is_valid, _ = validate_password_strength(weak_pass)
            assert is_valid is False, f"Weak password should fail: {weak_pass}"

    def test_strong_passwords_all_pass(self):
        """Test that all strong passwords pass validation."""
        strong_passwords = [
            "SecurePass123!",
            "MyPassword@2024",
            "TestPass#999",
            "Complex$Pass1",
            "Str0ng!Password",
            "ValidPass@123",
        ]

        for strong_pass in strong_passwords:
            is_valid, _ = validate_password_strength(strong_pass)
            assert is_valid is True, f"Strong password should pass: {strong_pass}"


class TestPasswordValidatorErrorHandling:
    """Test error handling in password validator."""

    def test_validator_function_exists_in_module(self):
        """Test that validate_password_strength function exists and is callable."""
        from app.core.password_validator import validate_password_strength
        assert callable(validate_password_strength)

    def test_error_class_exists(self):
        """Test that PasswordValidationError class exists."""
        from app.core.password_validator import PasswordValidationError
        assert issubclass(PasswordValidationError, ValueError)


class TestPasswordValidatorModuleStructure:
    """Test the module structure and imports."""

    def test_password_validator_file_exists(self):
        """Test that password_validator.py file exists in correct location."""
        test_dir = Path(__file__).parent  # services/backend/tests
        backend_dir = test_dir.parent      # services/backend
        validator_file = backend_dir / "app" / "core" / "password_validator.py"

        assert validator_file.exists(), f"Password validator file not found at {validator_file}"

    def test_auth_imports_password_validator(self):
        """Test that auth.py imports password validator."""
        test_dir = Path(__file__).parent  # services/backend/tests
        backend_dir = test_dir.parent      # services/backend
        auth_file = backend_dir / "app" / "api" / "v1" / "auth.py"

        with open(auth_file, 'r') as f:
            content = f.read()
            assert "password_validator" in content, "auth.py should import password_validator"
            assert "validate_password_strength" in content, "auth.py should call validate_password_strength"

    def test_auth_calls_validation_on_register(self):
        """Test that register endpoint validates password strength."""
        test_dir = Path(__file__).parent
        backend_dir = test_dir.parent
        auth_file = backend_dir / "app" / "api" / "v1" / "auth.py"

        with open(auth_file, 'r') as f:
            content = f.read()
            # Check that password validation is called in register function
            assert "STRONG_PASSWORD_REQUIRED" in content
            assert "validate_password_strength(user_data.password)" in content
