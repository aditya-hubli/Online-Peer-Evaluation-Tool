"""
OPETSE-11: Reminder Scheduler
Checks for upcoming deadlines and sends automated reminders to students.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from app.utils.deadline import is_deadline_passed, get_time_remaining, format_deadline
from app.utils.email_service import email_service
from app.core.supabase import supabase


def get_upcoming_deadlines(
    hours_ahead: int = 48
) -> List[Dict[str, Any]]:
    """
    Get all evaluation forms with deadlines in the next X hours.

    Args:
        hours_ahead: Number of hours to look ahead for deadlines

    Returns:
        List of forms with upcoming deadlines
    """
    try:
        # Get all forms with deadlines
        forms_response = supabase.table("evaluation_forms").select(
            "id, title, project_id, deadline, max_score"
        ).not_.is_("deadline", "null").execute()

        if not forms_response.data:
            return []

        upcoming_forms = []
        now = datetime.now(timezone.utc)
        future_time = now + timedelta(hours=hours_ahead)

        for form in forms_response.data:
            deadline_str = form.get("deadline")
            if not deadline_str:
                continue

            try:
                deadline_dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))

                # Check if deadline is in the future but within the window
                if now < deadline_dt <= future_time:
                    upcoming_forms.append(form)

            except (ValueError, AttributeError):
                continue

        return upcoming_forms

    except Exception as e:
        print(f"[REMINDER ERROR] Failed to get upcoming deadlines: {str(e)}")
        return []


def get_students_for_form(form_id: int) -> List[Dict[str, Any]]:
    """
    Get all students who haven't submitted evaluations for a form.

    Args:
        form_id: Evaluation form ID

    Returns:
        List of student dictionaries with email, name, and form details
    """
    try:
        # Get the form details including project
        form_response = supabase.table("evaluation_forms").select(
            "id, title, project_id, deadline"
        ).eq("id", form_id).execute()

        if not form_response.data:
            return []

        form = form_response.data[0]
        project_id = form.get("project_id")

        # Get all team members for this project
        teams_response = supabase.table("teams").select(
            "id"
        ).eq("project_id", project_id).execute()

        if not teams_response.data:
            return []

        team_ids = [team["id"] for team in teams_response.data]
        students_to_remind = []

        # For each team, get members who haven't submitted
        for team_id in team_ids:
            members_response = supabase.table("team_members").select(
                "user_id"
            ).eq("team_id", team_id).execute()

            if not members_response.data:
                continue

            for member in members_response.data:
                user_id = member["user_id"]

                # Check if student has submitted evaluation for this form
                eval_response = supabase.table("evaluations").select(
                    "id"
                ).eq("evaluator_id", user_id).eq("form_id", form_id).execute()

                # If no evaluation found, add to reminder list
                if not eval_response.data:
                    # Get student details
                    user_response = supabase.table("users").select(
                        "id, name, email"
                    ).eq("id", user_id).execute()

                    if user_response.data:
                        student = user_response.data[0]
                        students_to_remind.append({
                            "user_id": student["id"],
                            "name": student["name"],
                            "email": student["email"],
                            "form_id": form_id,
                            "form_title": form["title"],
                            "deadline": form["deadline"]
                        })

        return students_to_remind

    except Exception as e:
        print(f"[REMINDER ERROR] Failed to get students for form {form_id}: {str(e)}")
        return []


def send_reminders_for_form(
    form_id: int,
    project_title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send deadline reminders to all students who haven't submitted for a form.

    Args:
        form_id: Evaluation form ID
        project_title: Optional project title for context

    Returns:
        Dictionary with reminder statistics
    """
    students = get_students_for_form(form_id)

    if not students:
        return {
            "form_id": form_id,
            "reminders_sent": 0,
            "success_count": 0,
            "failure_count": 0,
            "message": "No students need reminders"
        }

    # Prepare recipient list for bulk email
    recipients = []
    deadline_str = students[0]["deadline"] if students else None

    for student in students:
        recipients.append({
            "to_email": student["email"],
            "student_name": student["name"],
            "form_title": student["form_title"],
            "deadline": format_deadline(deadline_str),
            "time_remaining": get_time_remaining(deadline_str),
            "project_title": project_title
        })

    # Send bulk reminders
    results = email_service.send_bulk_reminders(recipients)

    return {
        "form_id": form_id,
        "reminders_sent": len(students),
        "success_count": results["success_count"],
        "failure_count": results["failure_count"],
        "failed_emails": results["failed_emails"]
    }


def process_all_upcoming_deadlines(hours_ahead: int = 48) -> Dict[str, Any]:
    """
    Process all upcoming deadlines and send reminders.

    Args:
        hours_ahead: Number of hours to look ahead for deadlines

    Returns:
        Summary of all reminders sent
    """
    upcoming_forms = get_upcoming_deadlines(hours_ahead)

    if not upcoming_forms:
        return {
            "total_forms": 0,
            "total_reminders": 0,
            "total_success": 0,
            "total_failures": 0,
            "forms_processed": []
        }

    summary = {
        "total_forms": len(upcoming_forms),
        "total_reminders": 0,
        "total_success": 0,
        "total_failures": 0,
        "forms_processed": []
    }

    for form in upcoming_forms:
        # Get project title if available
        project_title = None
        if form.get("project_id"):
            try:
                project_response = supabase.table("projects").select(
                    "title"
                ).eq("id", form["project_id"]).execute()
                if project_response.data:
                    project_title = project_response.data[0]["title"]
            except Exception:
                pass

        # Send reminders for this form
        result = send_reminders_for_form(form["id"], project_title)

        summary["total_reminders"] += result["reminders_sent"]
        summary["total_success"] += result["success_count"]
        summary["total_failures"] += result["failure_count"]
        summary["forms_processed"].append(result)

    return summary
