"""
OPETSE-11: Reminder Management API
Endpoints for managing and triggering deadline reminders.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.utils.reminder_scheduler import (
    get_upcoming_deadlines,
    send_reminders_for_form,
    process_all_upcoming_deadlines
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


class TriggerRemindersRequest(BaseModel):
    """Request model for manual reminder triggering."""
    form_id: Optional[int] = None
    hours_ahead: int = 48


class ReminderStatsResponse(BaseModel):
    """Response model for reminder statistics."""
    total_forms: int
    total_reminders: int
    total_success: int
    total_failures: int


@router.get("/upcoming-deadlines")
async def list_upcoming_deadlines(hours_ahead: int = 48):
    """
    Get list of evaluation forms with upcoming deadlines.

    Args:
        hours_ahead: Number of hours to look ahead (default: 48)

    Returns:
        List of forms with deadlines approaching
    """
    try:
        deadlines = get_upcoming_deadlines(hours_ahead)
        return {
            "count": len(deadlines),
            "forms": deadlines,
            "hours_ahead": hours_ahead
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch upcoming deadlines: {str(e)}"
        )


@router.post("/trigger", status_code=status.HTTP_200_OK)
async def trigger_reminders(request: TriggerRemindersRequest):
    """
    Manually trigger deadline reminders.

    Args:
        request: Trigger request with optional form_id and hours_ahead

    Returns:
        Summary of reminders sent

    OPETSE-11: Allows instructors/admins to manually send reminders
    """
    try:
        if request.form_id:
            # Send reminders for specific form
            result = send_reminders_for_form(request.form_id)
            return {
                "message": "Reminders triggered for specific form",
                "result": result
            }
        else:
            # Process all upcoming deadlines
            summary = process_all_upcoming_deadlines(request.hours_ahead)
            return {
                "message": "Reminders processed for all upcoming deadlines",
                "summary": summary
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger reminders: {str(e)}"
        )


@router.get("/stats")
async def get_reminder_stats(hours_ahead: int = 48):
    """
    Get statistics about pending reminders without sending them.

    Args:
        hours_ahead: Number of hours to look ahead (default: 48)

    Returns:
        Statistics about how many reminders would be sent
    """
    try:
        deadlines = get_upcoming_deadlines(hours_ahead)

        # Count total students who need reminders (without sending)
        from app.utils.reminder_scheduler import get_students_for_form

        total_students = 0
        form_stats = []

        for form in deadlines:
            students = get_students_for_form(form["id"])
            total_students += len(students)
            form_stats.append({
                "form_id": form["id"],
                "form_title": form["title"],
                "deadline": form["deadline"],
                "students_to_remind": len(students)
            })

        return {
            "total_forms": len(deadlines),
            "total_students": total_students,
            "hours_ahead": hours_ahead,
            "forms": form_stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reminder stats: {str(e)}"
        )


@router.post("/test-email")
async def send_test_email(email: str):
    """
    Send a test reminder email to verify email configuration.

    Args:
        email: Email address to send test to

    Returns:
        Success/failure message

    OPETSE-11: Test endpoint for email configuration
    """
    from app.utils.email_service import email_service
    from datetime import datetime, timezone

    try:
        success = email_service.send_deadline_reminder(
            to_email=email,
            student_name="Test User",
            form_title="Test Evaluation Form",
            deadline=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            time_remaining="48 hours",
            project_title="Test Project"
        )

        if success:
            return {
                "message": "Test email sent successfully",
                "email": email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test email. Check SMTP configuration."
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}"
        )
