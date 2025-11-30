#!/usr/bin/env python
"""Manual test script for OPETSE-28 password strength validation."""
import sys
sys.path.insert(0, '.')

from app.core.password_validator import validate_password_strength, get_password_strength_criteria

print("=" * 70)
print("OPETSE-28: PASSWORD STRENGTH VALIDATION TEST SUITE")
print("=" * 70)

# Test 1: Strong passwords should pass
print("\nTEST 1: Strong Passwords (Should PASS)")
print("-" * 70)
strong_passwords = [
    "SecurePass123!",
    "MyPassword@2024",
    "TestPass#999",
    "Complex$Pass1",
    "Str0ng!Password",
]

passed = 0
for pwd in strong_passwords:
    valid, msg = validate_password_strength(pwd)
    if valid:
        passed += 1
        print(f"PASS: '{pwd}'")
    else:
        print(f"FAIL: '{pwd}' - {msg}")

print(f"\nResult: {passed}/{len(strong_passwords)} passed")

# Test 2: Weak passwords should fail
print("\nTEST 2: Weak Passwords (Should FAIL)")
print("-" * 70)
weak_passwords = [
    ("123456", "Only digits"),
    ("password", "No uppercase/digits/special"),
    ("Pass1", "Too short, no special char"),
    ("PASSWORD", "No lowercase/digits"),
]

failed_correctly = 0
for pwd, reason in weak_passwords:
    valid, msg = validate_password_strength(pwd)
    if not valid:
        failed_correctly += 1
        print(f"PASS: '{pwd}' correctly rejected - {msg}")
    else:
        print(f"FAIL: '{pwd}' should have been rejected")

print(f"\nResult: {failed_correctly}/{len(weak_passwords)} failed correctly")

# Test 3: Show password criteria
print("\nTEST 3: Password Strength Criteria")
print("-" * 70)
criteria = get_password_strength_criteria()
print(f"Minimum Length: {criteria['min_length']}")
print(f"Requires Uppercase: {criteria['requires_uppercase']}")
print(f"Requires Lowercase: {criteria['requires_lowercase']}")
print(f"Requires Digit: {criteria['requires_digit']}")
print(f"Requires Special Char: {criteria['requires_special_char']}")
print(f"Allowed Special Chars: {criteria['special_chars']}")

print("\n" + "=" * 70)
total_tests = len(strong_passwords) + len(weak_passwords)
total_passed = passed + failed_correctly
if total_passed == total_tests:
    print("SUCCESS: ALL TESTS PASSED!")
else:
    print(f"FAILURE: {total_passed}/{total_tests} tests passed")
print("=" * 70)
