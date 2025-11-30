"""
Reports and analytics routes.

OPETSE-8: All reports anonymize evaluator identities for students.
OPETSE-32: Export anonymized reports to CSV format.
OPETSE-16: Export reports in PDF format for instructors.
OPETSE-12: Instructor dashboard showing submission analytics and evaluation progress.
Only instructors and admins can see who submitted evaluations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from app.db import get_db
from app.core.supabase import supabase
from app.utils.anonymity import anonymize_report_data
from app.utils.export import (
    export_evaluations_to_csv,
    export_team_report_to_csv,
    export_project_report_to_csv,
    determine_anonymization
)
from app.utils.pdf_export import (
    export_evaluations_to_pdf,
    export_team_report_to_pdf,
    export_project_report_to_pdf
)
from collections import defaultdict
import io

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/project/{project_id}")
async def get_project_report(
    project_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    Get comprehensive evaluation report for a project.

    OPETSE-8: Evaluator identities are anonymized for students.
    """
    try:
        # Verify project exists
        project = supabase.table("projects").select("*").eq("id", project_id).execute()

        if not project.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        project_info = project.data[0]

        # Get all teams in the project
        teams = supabase.table("teams").select("*").eq("project_id", project_id).execute()

        report = {
            "project": project_info,
            "teams": [],
            "overall_statistics": {
                "total_teams": len(teams.data) if teams.data else 0,
                "total_evaluations": 0,
                "average_score": 0,
                "participation_rate": 0
            }
        }

        if not teams.data:
            return {
                "report": report,
                "message": "No teams found in this project"
            }

        total_evaluations = 0
        all_scores = []

        # Process each team
        for team in teams.data:
            team_report = await _get_team_data(team["id"])
            report["teams"].append(team_report)
            total_evaluations += team_report["statistics"]["total_evaluations"]
            all_scores.extend(team_report["statistics"].get("all_scores", []))

        # Calculate overall statistics
        report["overall_statistics"]["total_evaluations"] = total_evaluations
        if all_scores:
            report["overall_statistics"]["average_score"] = round(sum(all_scores) / len(all_scores), 2)

        # OPETSE-8: Apply anonymization
        anonymized_report = anonymize_report_data(report, requester_role=requester_role)

        return {
            "report": anonymized_report,
            "message": "Project report generated successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate project report: {str(e)}"
        )


@router.get("/team/{team_id}")
async def get_team_report(
    team_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    Get detailed evaluation report for a specific team.

    OPETSE-8: Evaluator identities are anonymized for students.
    """
    try:
        # Verify team exists
        team = supabase.table("teams").select("*").eq("id", team_id).execute()

        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        team_report = await _get_team_data(team_id)

        # OPETSE-8: Apply anonymization
        anonymized_report = anonymize_report_data(team_report, requester_role=requester_role)

        return {
            "report": anonymized_report,
            "message": "Team report generated successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate team report: {str(e)}"
        )


@router.get("/user/{user_id}")
async def get_user_report(
    user_id: str,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    Get evaluation report for a specific user across all their teams.

    OPETSE-8: Evaluator identities are anonymized for students.
    Students can see their own received evaluations but not who rated them.
    """
    try:
        # Verify user exists
        user = supabase.table("users").select("*").eq("id", user_id).execute()

        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_info = user.data[0]

        # Get all teams the user is a member of
        memberships = supabase.table("team_members").select("team_id").eq("user_id", user_id).execute()

        if not memberships.data:
            return {
                "report": {
                    "user": user_info,
                    "teams": [],
                    "overall_statistics": {
                        "teams_count": 0,
                        "evaluations_received": 0,
                        "evaluations_given": 0,
                        "average_score_received": 0
                    }
                },
                "message": "User is not a member of any team"
            }

        team_ids = [m["team_id"] for m in memberships.data]

        # Get evaluations received by this user
        evaluations_received = supabase.table("evaluations").select("*").eq("evaluatee_id", user_id).execute()

        # Get evaluations given by this user
        evaluations_given = supabase.table("evaluations").select("*").eq("evaluator_id", user_id).execute()

        # Calculate statistics
        scores_received = [e["total_score"] for e in evaluations_received.data if e.get("total_score")]
        avg_score = round(sum(scores_received) / len(scores_received), 2) if scores_received else 0

        # Get team details
        teams_data = []
        for team_id in team_ids:
            team = supabase.table("teams").select("*").eq("id", team_id).execute()
            if team.data:
                team_info = team.data[0]
                # Get evaluations for this user in this team
                team_evals = [e for e in evaluations_received.data if e["team_id"] == team_id]
                team_scores = [e["total_score"] for e in team_evals if e.get("total_score")]

                teams_data.append({
                    "team": team_info,
                    "evaluations_count": len(team_evals),
                    "average_score": round(sum(team_scores) / len(team_scores), 2) if team_scores else 0
                })

        report = {
            "user": {
                "id": user_info["id"],
                "name": user_info["name"],
                "email": user_info["email"],
                "role": user_info["role"]
            },
            "teams": teams_data,
            "overall_statistics": {
                "teams_count": len(team_ids),
                "evaluations_received": len(evaluations_received.data),
                "evaluations_given": len(evaluations_given.data),
                "average_score_received": avg_score
            },
            "detailed_evaluations": evaluations_received.data
        }

        # OPETSE-8: Apply anonymization
        anonymized_report = anonymize_report_data(report, requester_role=requester_role)

        return {
            "report": anonymized_report,
            "message": "User report generated successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate user report: {str(e)}"
        )


@router.get("/evaluation-form/{form_id}")
async def get_form_report(
    form_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    Get statistical report for a specific evaluation form.

    OPETSE-8: Evaluator identities are anonymized for students.
    Form reports show aggregated statistics without individual evaluator information.
    """
    try:
        # Get form details
        form = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()

        if not form.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation form not found"
            )

        form_info = form.data[0]

        # Get all criteria for this form
        criteria = supabase.table("form_criteria").select("*").eq("form_id", form_id).order("order_index").execute()

        # Get all evaluations using this form
        evaluations = supabase.table("evaluations").select("*").eq("form_id", form_id).execute()

        # Get all scores for this form
        if evaluations.data:
            evaluation_ids = [e["id"] for e in evaluations.data]
            all_scores = supabase.table("evaluation_scores").select("*").in_("evaluation_id", evaluation_ids).execute()

            # Aggregate scores by criterion
            criterion_stats = defaultdict(list)
            for score in all_scores.data:
                criterion_stats[score["criterion_id"]].append(score["score"])

            # Build criteria statistics
            criteria_analysis = []
            for criterion in criteria.data:
                scores = criterion_stats.get(criterion["id"], [])
                criteria_analysis.append({
                    "criterion": criterion,
                    "statistics": {
                        "total_responses": len(scores),
                        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
                        "max_score": max(scores) if scores else 0,
                        "min_score": min(scores) if scores else 0
                    }
                })
        else:
            criteria_analysis = [{"criterion": c, "statistics": {"total_responses": 0, "average_score": 0}} for c in criteria.data]

        report = {
            "form": form_info,
            "criteria_analysis": criteria_analysis,
            "overall_statistics": {
                "total_evaluations": len(evaluations.data),
                "completion_rate": "N/A"  # Would need to know expected evaluations
            }
        }

        # Note: Form reports are aggregated and don't contain individual evaluator info
        # So anonymization is not strictly needed, but we apply it for consistency
        anonymized_report = anonymize_report_data(report, requester_role=requester_role)

        return {
            "report": anonymized_report,
            "message": "Evaluation form report generated successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate form report: {str(e)}"
        )


# Helper function to get team data
async def _get_team_data(team_id: int) -> dict:
    """Helper function to get comprehensive team data."""
    team = supabase.table("teams").select("*").eq("id", team_id).execute()
    team_info = team.data[0] if team.data else {}

    # Get team members
    members = supabase.table("team_members").select("*").eq("team_id", team_id).execute()

    team_members = []
    if members.data:
        for member in members.data:
            user = supabase.table("users").select("id, name, email").eq("id", member["user_id"]).execute()
            if user.data:
                team_members.append(user.data[0])

    # Get all evaluations for this team
    evaluations = supabase.table("evaluations").select("*").eq("team_id", team_id).execute()

    # Calculate member statistics
    member_stats = {}
    all_scores = []

    for member in team_members:
        member_evals = [e for e in evaluations.data if e["evaluatee_id"] == member["id"]]
        scores = [e["total_score"] for e in member_evals if e.get("total_score")]
        all_scores.extend(scores)

        member_stats[member["id"]] = {
            "member": member,
            "evaluations_received": len(member_evals),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "evaluations": member_evals
        }

    return {
        "team": team_info,
        "members": list(member_stats.values()),
        "statistics": {
            "total_members": len(team_members),
            "total_evaluations": len(evaluations.data),
            "average_score": round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
            "all_scores": all_scores
        }
    }


# OPETSE-32 & OPETSE-16: Export Endpoints

@router.get("/project/{project_id}/export")
async def export_project_report(
    project_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity"),
    format: str = Query("csv", description="Export format: csv or pdf")
):
    """
    Export project evaluation report as CSV or PDF.

    OPETSE-32: Anonymizes rater identities for students in CSV exports.
    OPETSE-16: PDF export support for instructors.
    Only instructors and admins see non-anonymized exports.
    """
    try:
        # Get project report data
        report_response = await get_project_report(project_id, requester_role)
        report_data = report_response["report"]

        # Determine if anonymization is needed
        anonymize = determine_anonymization(requester_role)

        # Generate export based on format
        if format.lower() == "pdf":
            # OPETSE-16: PDF export
            content = export_project_report_to_pdf(report_data, anonymize=anonymize)
            output = io.BytesIO(content)
            output.seek(0)
            media_type = "application/pdf"
            file_ext = "pdf"
        else:
            # OPETSE-32: CSV export (default)
            content = export_project_report_to_csv(report_data, anonymize=anonymize)
            output = io.BytesIO(content.encode('utf-8'))
            output.seek(0)
            media_type = "text/csv"
            file_ext = "csv"

        filename = f"project_{project_id}_report_{'anonymized' if anonymize else 'detailed'}_{datetime.now().strftime('%Y%m%d')}.{file_ext}"

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export project report: {str(e)}"
        )


@router.get("/team/{team_id}/export")
async def export_team_report(
    team_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity"),
    format: str = Query("csv", description="Export format: csv or pdf")
):
    """
    Export team evaluation report as CSV or PDF.

    OPETSE-32: Anonymizes rater identities for students in CSV exports.
    OPETSE-16: PDF export support for instructors.
    """
    try:
        # Get team report data
        report_response = await get_team_report(team_id, requester_role)
        report_data = report_response["report"]

        # Determine if anonymization is needed
        anonymize = determine_anonymization(requester_role)

        # Add project name to team data
        team_info = report_data.get("team", {})
        project_id = team_info.get("project_id")
        if project_id:
            project = supabase.table("projects").select("title").eq("id", project_id).execute()
            if project.data:
                report_data["project_name"] = project.data[0]["title"]

        # Generate export based on format
        if format.lower() == "pdf":
            # OPETSE-16: PDF export
            content = export_team_report_to_pdf(report_data, anonymize=anonymize)
            output = io.BytesIO(content)
            output.seek(0)
            media_type = "application/pdf"
            file_ext = "pdf"
        else:
            # OPETSE-32: CSV export (default)
            content = export_team_report_to_csv(report_data, anonymize=anonymize)
            output = io.BytesIO(content.encode('utf-8'))
            output.seek(0)
            media_type = "text/csv"
            file_ext = "csv"

        filename = f"team_{team_id}_report_{'anonymized' if anonymize else 'detailed'}_{datetime.now().strftime('%Y%m%d')}.{file_ext}"

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export team report: {str(e)}"
        )


@router.get("/evaluations/export")
async def export_evaluations(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity"),
    format: str = Query("csv", description="Export format: csv or pdf")
):
    """
    Export evaluations as CSV or PDF with optional filtering.

    OPETSE-32: Anonymizes rater identities for students in CSV exports.
    OPETSE-16: PDF export support for instructors.
    """
    try:
        # Build query based on filters
        query = supabase.table("evaluations").select("*")

        if team_id:
            query = query.eq("team_id", team_id)
        elif project_id:
            # Get teams for this project first
            teams = supabase.table("teams").select("id").eq("project_id", project_id).execute()
            if teams.data:
                team_ids = [t["id"] for t in teams.data]
                # Note: Supabase doesn't support IN operator directly in this client
                # We'll need to fetch all and filter client-side
                query = query

        evaluations_result = query.execute()

        if not evaluations_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No evaluations found"
            )

        # Filter by project_id if specified (client-side filtering)
        evaluations = evaluations_result.data
        if project_id and not team_id:
            teams = supabase.table("teams").select("id").eq("project_id", project_id).execute()
            team_ids = [t["id"] for t in teams.data] if teams.data else []
            evaluations = [e for e in evaluations if e.get("team_id") in team_ids]

        # Enrich evaluations with related data
        enriched_evaluations = []
        for evaluation in evaluations:
            # Get evaluatee data
            evaluatee = supabase.table("users").select("id, name, email").eq("id", evaluation.get("evaluatee_id")).execute()
            evaluation["evaluatee"] = evaluatee.data[0] if evaluatee.data else {}

            # Get evaluator data
            evaluator = supabase.table("users").select("id, name, email").eq("id", evaluation.get("evaluator_id")).execute()
            evaluation["evaluator"] = evaluator.data[0] if evaluator.data else {}

            # Get form title
            form = supabase.table("evaluation_forms").select("title").eq("id", evaluation.get("form_id")).execute()
            evaluation["form_title"] = form.data[0]["title"] if form.data else ""

            enriched_evaluations.append(evaluation)

        # Apply anonymization if needed
        anonymize = determine_anonymization(requester_role)
        if anonymize:
            from app.utils.anonymity import anonymize_evaluation_list
            enriched_evaluations = anonymize_evaluation_list(enriched_evaluations, requester_role=requester_role)

        # Generate export based on format
        if format.lower() == "pdf":
            # OPETSE-16: PDF export
            content = export_evaluations_to_pdf(enriched_evaluations, anonymize=anonymize)
            output = io.BytesIO(content)
            output.seek(0)
            media_type = "application/pdf"
            file_ext = "pdf"
        else:
            # OPETSE-32: CSV export (default)
            content = export_evaluations_to_csv(enriched_evaluations, anonymize=anonymize)
            output = io.BytesIO(content.encode('utf-8'))
            output.seek(0)
            media_type = "text/csv"
            file_ext = "csv"

        filter_str = f"project_{project_id}" if project_id else (f"team_{team_id}" if team_id else "all")
        filename = f"evaluations_{filter_str}_{'anonymized' if anonymize else 'detailed'}_{datetime.now().strftime('%Y%m%d')}.{file_ext}"

        return StreamingResponse(
            output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export evaluations: {str(e)}"
        )


# ============================================================================
# OPETSE-12: Submission Analytics & Instructor Dashboard
# ============================================================================

@router.get("/analytics/project/{project_id}/submission-progress")
async def get_project_submission_progress(
    project_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    OPETSE-12: Get submission analytics and evaluation progress for a project.
    Shows progress tracking for instructors to monitor evaluation completion.
    """
    try:
        # Verify project exists
        project = supabase.table("projects").select("*").eq("id", project_id).execute()

        if not project.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        project_info = project.data[0]

        # Get all teams in the project
        teams = supabase.table("teams").select("*").eq("project_id", project_id).execute()

        if not teams.data:
            return {
                "analytics": {
                    "project": project_info,
                    "submission_progress": {
                        "total_teams": 0,
                        "total_possible_evaluations": 0,
                        "completed_evaluations": 0,
                        "pending_evaluations": 0,
                        "completion_percentage": 0
                    },
                    "teams": []
                },
                "message": "No teams found in this project"
            }

        total_possible = 0
        total_completed = 0
        teams_data = []

        # Process each team for submission progress
        for team in teams.data:
            team_members = supabase.table("team_members").select("*").eq("team_id", team["id"]).execute()
            
            if not team_members.data:
                continue

            member_count = len(team_members.data)
            # Possible evaluations: each member evaluates all other members
            possible_evals = member_count * (member_count - 1)
            total_possible += possible_evals

            # Get actual evaluations for this team
            evaluations = supabase.table("evaluations").select("*").eq("team_id", team["id"]).execute()
            completed_evals = len(evaluations.data) if evaluations.data else 0
            total_completed += completed_evals

            # Get team member details with their evaluation progress
            member_progress = []
            for member in team_members.data:
                user = supabase.table("users").select("id, name, email").eq("id", member["user_id"]).execute()
                
                # Count evaluations this member has received
                evals_received = [e for e in (evaluations.data or []) if e["evaluatee_id"] == member["user_id"]]
                
                # Count evaluations this member has given
                evals_given = [e for e in (evaluations.data or []) if e["evaluator_id"] == member["user_id"]]
                
                member_progress.append({
                    "member_id": member["user_id"],
                    "member_name": user.data[0]["name"] if user.data else "Unknown",
                    "evaluations_received": len(evals_received),
                    "evaluations_given": len(evals_given),
                    "pending_to_receive": (member_count - 1) - len(evals_received)
                })

            teams_data.append({
                "team_id": team["id"],
                "team_name": team["name"],
                "total_members": member_count,
                "possible_evaluations": possible_evals,
                "completed_evaluations": completed_evals,
                "pending_evaluations": possible_evals - completed_evals,
                "completion_percentage": round((completed_evals / possible_evals * 100), 2) if possible_evals > 0 else 0,
                "member_progress": member_progress
            })

        completion_percentage = round((total_completed / total_possible * 100), 2) if total_possible > 0 else 0

        analytics = {
            "project": project_info,
            "submission_progress": {
                "total_teams": len(teams.data),
                "total_possible_evaluations": total_possible,
                "completed_evaluations": total_completed,
                "pending_evaluations": total_possible - total_completed,
                "completion_percentage": completion_percentage
            },
            "teams": teams_data
        }

        # Apply anonymization if needed
        anonymized_analytics = anonymize_report_data(analytics, requester_role=requester_role) if requester_role not in ["instructor", "admin"] else analytics

        return {
            "analytics": anonymized_analytics,
            "message": "Project submission analytics retrieved successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else False
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve submission analytics: {str(e)}"
        )


@router.get("/analytics/team/{team_id}/evaluation-status")
async def get_team_evaluation_status(
    team_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    OPETSE-12: Get detailed evaluation status for a specific team.
    Shows which members have completed/pending evaluations.
    """
    try:
        # Verify team exists
        team = supabase.table("teams").select("*").eq("id", team_id).execute()

        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        team_info = team.data[0]
        team_members = supabase.table("team_members").select("*").eq("team_id", team_id).execute()

        if not team_members.data:
            return {
                "evaluation_status": {
                    "team": team_info,
                    "members": [],
                    "overall": {
                        "total_members": 0,
                        "total_possible_evaluations": 0,
                        "completed": 0,
                        "pending": 0
                    }
                },
                "message": "Team has no members"
            }

        # Get all evaluations for this team
        evaluations = supabase.table("evaluations").select("*").eq("team_id", team_id).execute()
        evaluations_list = evaluations.data if evaluations.data else []

        member_count = len(team_members.data)
        total_possible = member_count * (member_count - 1)
        total_completed = len(evaluations_list)

        # Build detailed member status
        member_statuses = []
        for member in team_members.data:
            user = supabase.table("users").select("id, name, email").eq("id", member["user_id"]).execute()
            user_info = user.data[0] if user.data else {}

            # Evaluations this member has given
            given = [e for e in evaluations_list if e["evaluator_id"] == member["user_id"]]
            
            # Evaluations this member should give (to all other members)
            should_give = member_count - 1

            # Evaluations this member has received
            received = [e for e in evaluations_list if e["evaluatee_id"] == member["user_id"]]
            
            # Evaluations this member should receive
            should_receive = member_count - 1

            member_statuses.append({
                "member_id": member["user_id"],
                "member_name": user_info.get("name", "Unknown"),
                "member_email": user_info.get("email", ""),
                "evaluations_given": len(given),
                "evaluations_should_give": should_give,
                "evaluations_pending_to_give": should_give - len(given),
                "evaluations_received": len(received),
                "evaluations_should_receive": should_receive,
                "evaluations_pending_to_receive": should_receive - len(received),
                "status": "complete" if (len(given) == should_give and len(received) == should_receive) else "pending"
            })

        evaluation_status = {
            "team": team_info,
            "members": member_statuses,
            "overall": {
                "total_members": member_count,
                "total_possible_evaluations": total_possible,
                "completed": total_completed,
                "pending": total_possible - total_completed,
                "completion_percentage": round((total_completed / total_possible * 100), 2) if total_possible > 0 else 0
            }
        }

        # Apply anonymization if needed
        anonymized_status = anonymize_report_data(evaluation_status, requester_role=requester_role) if requester_role not in ["instructor", "admin"] else evaluation_status

        return {
            "evaluation_status": anonymized_status,
            "message": "Team evaluation status retrieved successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else False
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team evaluation status: {str(e)}"
        )


@router.get("/analytics/dashboard")
async def get_instructor_dashboard(
    requester_role: Optional[str] = Query(None, description="Role of requesting user"),
    project_id: Optional[int] = Query(None, description="Filter by project ID")
):
    """
    OPETSE-12: Get comprehensive instructor dashboard with all project analytics.
    Shows overview of all projects with submission progress and key metrics.
    """
    try:
        if requester_role not in ["instructor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors and admins can access dashboard analytics"
            )

        if project_id:
            # Get specific project analytics
            projects = supabase.table("projects").select("*").eq("id", project_id).execute()
        else:
            # Get all projects
            projects = supabase.table("projects").select("*").execute()

        if not projects.data:
            return {
                "dashboard": {
                    "projects": [],
                    "overall_metrics": {
                        "total_projects": 0,
                        "total_teams": 0,
                        "total_evaluations_expected": 0,
                        "total_evaluations_completed": 0,
                        "overall_completion_percentage": 0
                    }
                },
                "message": "No projects found"
            }

        projects_data = []
        total_teams = 0
        total_expected = 0
        total_completed = 0

        for project in projects.data:
            # Get teams for this project
            teams = supabase.table("teams").select("*").eq("project_id", project["id"]).execute()
            teams_list = teams.data if teams.data else []
            total_teams += len(teams_list)

            project_expected = 0
            project_completed = 0

            for team in teams_list:
                # Get team members
                members = supabase.table("team_members").select("*").eq("team_id", team["id"]).execute()
                member_count = len(members.data) if members.data else 0

                # Possible evaluations for this team
                possible = member_count * (member_count - 1)
                project_expected += possible

                # Get actual evaluations
                evals = supabase.table("evaluations").select("*").eq("team_id", team["id"]).execute()
                completed = len(evals.data) if evals.data else 0
                project_completed += completed

            total_expected += project_expected
            total_completed += project_completed

            projects_data.append({
                "project_id": project["id"],
                "project_name": project.get("title", "Unknown"),
                "project_description": project.get("description", ""),
                "total_teams": len(teams_list),
                "total_expected_evaluations": project_expected,
                "total_completed_evaluations": project_completed,
                "pending_evaluations": project_expected - project_completed,
                "completion_percentage": round((project_completed / project_expected * 100), 2) if project_expected > 0 else 0,
                "deadline": project.get("deadline")
            })

        overall_completion = round((total_completed / total_expected * 100), 2) if total_expected > 0 else 0

        dashboard = {
            "projects": projects_data,
            "overall_metrics": {
                "total_projects": len(projects.data),
                "total_teams": total_teams,
                "total_evaluations_expected": total_expected,
                "total_evaluations_completed": total_completed,
                "overall_completion_percentage": overall_completion
            }
        }

        return {
            "dashboard": dashboard,
            "message": "Instructor dashboard retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard: {str(e)}"
        )

