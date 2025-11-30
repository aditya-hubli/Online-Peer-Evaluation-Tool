"""Deadline validation and checking utilities for OPETSE-9 and OPETSE-10."""
from datetime import datetime, timezone
from typing import Optional, Callable


def is_deadline_passed(
    deadline: Optional[str],
    late_submission_checker: Optional[Callable] = None,
    user_id: Optional[int] = None,
    form_id: Optional[int] = None
) -> bool:
    """
    Check if a deadline has passed.
    
    OPETSE-10: Extended to support late submission override.

    Args:
        deadline: ISO format datetime string or None
        late_submission_checker: Optional callable to check late submission permission
        user_id: Optional user ID for late submission check
        form_id: Optional form ID for late submission check

    Returns:
        True if deadline exists and has passed (and no late submission allowed), False otherwise
    """
    if not deadline:
        # No deadline means always open
        return False

    try:
        # Parse the deadline string to datetime
        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))

        # Get current time in UTC
        now = datetime.now(timezone.utc)

        # If not passed, return False
        if now <= deadline_dt:
            return False
        
        # Deadline has passed - check if late submission is allowed
        # OPETSE-10: If late submission checker is provided, check permissions
        if late_submission_checker and user_id is not None and form_id is not None:
            if late_submission_checker(form_id, user_id):
                return False  # Late submission is allowed, so deadline hasn't effectively "passed"
        
        return True  # Deadline has passed and no late submission allowed
    except (ValueError, AttributeError):
        # If parsing fails, treat as no deadline
        return False


def format_deadline(deadline: Optional[str]) -> Optional[str]:
    """
    Format a deadline string for display.

    Args:
        deadline: ISO format datetime string or None

    Returns:
        Formatted datetime string or None
    """
    if not deadline:
        return None

    try:
        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        return deadline_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return deadline


def get_time_remaining(deadline: Optional[str]) -> Optional[str]:
    """
    Get human-readable time remaining until deadline.

    Args:
        deadline: ISO format datetime string or None

    Returns:
        Human-readable string like "2 days, 3 hours" or None
    """
    if not deadline:
        return None

    try:
        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)

        if now > deadline_dt:
            return "Expired"

        delta = deadline_dt - now
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if days == 0 and minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        return ", ".join(parts) if parts else "Less than a minute"
    except (ValueError, AttributeError):
        return None


def validate_deadline_format(deadline: str) -> bool:
    """
    Validate that a deadline string is in correct ISO format.

    Args:
        deadline: Deadline string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError, TypeError):
        return False
