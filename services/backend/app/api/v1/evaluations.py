"""Evaluation submission and retrieval routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.db import get_db
from app.core.supabase import supabase
from app.utils.deadline import is_deadline_passed, format_deadline
from app.utils.anonymity import anonymize_evaluation_list, anonymize_evaluator
from app.utils.weighted_scoring import WeightedScoringCalculator
from app.core.late_submission import is_late_submission_allowed

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


# Pydantic models
class EvaluationScore(BaseModel):
    criterion_id: int
    score: int


class EvaluationSubmit(BaseModel):
    form_id: int
    evaluator_id: str
    evaluatee_id: str
    team_id: int
    total_score: int
    scores: List[EvaluationScore]
    comments: Optional[str] = None


class EvaluationUpdate(BaseModel):
    total_score: Optional[int] = None
    comments: Optional[str] = None
    scores: Optional[List[EvaluationScore]] = None


@router.get("/")
async def list_evaluations(
    form_id: Optional[int] = None,
    team_id: Optional[int] = None,
    evaluator_id: Optional[int] = None,
    evaluatee_id: Optional[int] = None,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    List evaluations with optional filters.

    OPETSE-8: Evaluator identities are anonymized for students.
    Only instructors and admins can see who submitted evaluations.
    """
    try:
        query = supabase.table("evaluations").select("*")

        # Apply filters if provided
        if form_id:
            query = query.eq("form_id", form_id)
        if team_id:
            query = query.eq("team_id", team_id)
        if evaluator_id:
            query = query.eq("evaluator_id", evaluator_id)
        if evaluatee_id:
            query = query.eq("evaluatee_id", evaluatee_id)

        result = query.order("submitted_at", desc=True).execute()

        # Enrich each evaluation with related data
        evaluations = result.data
        for evaluation in evaluations:
            # Get evaluator details
            evaluator = supabase.table("users").select("id, name, email").eq("id", evaluation["evaluator_id"]).execute()
            evaluation["evaluator"] = evaluator.data[0] if evaluator.data else None

            # Get evaluatee details
            evaluatee = supabase.table("users").select("id, name, email").eq("id", evaluation["evaluatee_id"]).execute()
            evaluation["evaluatee"] = evaluatee.data[0] if evaluatee.data else None

            # Get team details
            team = supabase.table("teams").select("id, name").eq("id", evaluation["team_id"]).execute()
            evaluation["team"] = team.data[0] if team.data else None

            # Get form details
            form = supabase.table("evaluation_forms").select("id, title").eq("id", evaluation["form_id"]).execute()
            evaluation["form"] = form.data[0] if form.data else None

            # Get scores with criteria details
            scores = supabase.table("evaluation_scores").select("*").eq("evaluation_id", evaluation["id"]).execute()

            if scores.data:
                for score in scores.data:
                    criterion = supabase.table("form_criteria").select("*").eq("id", score["criterion_id"]).execute()
                    score["criterion"] = criterion.data[0] if criterion.data else None

                evaluation["scores"] = scores.data
            else:
                evaluation["scores"] = []

        # OPETSE-8: Apply anonymization based on requester role
        anonymized_evaluations = anonymize_evaluation_list(
            evaluations,
            requester_role=requester_role
        )

        return {
            "evaluations": anonymized_evaluations,
            "count": len(anonymized_evaluations),
            "message": "Evaluations retrieved successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else True
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evaluations: {str(e)}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_evaluation(evaluation_data: EvaluationSubmit):
    """
    Submit a new peer evaluation.
    
    OPETSE-21: Optimized for fast form submissions (completes within 2 seconds).
    - Batch insert scores instead of individual inserts
    - Parallel validation queries where possible
    - Optimized database operations
    """
    import time
    start_time = time.time()
    
    try:
        # OPETSE-21: Parallel validation queries for better performance
        # Validate form exists and get form data
        form = supabase.table("evaluation_forms").select("*").eq("id", evaluation_data.form_id).execute()

        if not form.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation form not found"
            )

        # OPETSE-9: Check if deadline has passed
        # OPETSE-10: Extended to support late submission override
        form_data = form.data[0]
        deadline = form_data.get("deadline")
        if is_deadline_passed(
            deadline,
            late_submission_checker=is_late_submission_allowed,
            user_id=evaluation_data.evaluator_id,
            form_id=evaluation_data.form_id
        ):
            formatted_deadline = format_deadline(deadline)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Evaluation deadline has passed. Deadline was: {formatted_deadline}"
            )

        # Prevent self-evaluation (fast check, no DB query)
        if evaluation_data.evaluator_id == evaluation_data.evaluatee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot evaluate yourself"
            )

        # OPETSE-21: Parallel validation queries
        # Execute validation queries in parallel where possible
        team_query = supabase.table("teams").select("*").eq("id", evaluation_data.team_id)
        evaluator_query = supabase.table("users").select("id").eq("id", evaluation_data.evaluator_id)
        evaluatee_query = supabase.table("users").select("id").eq("id", evaluation_data.evaluatee_id)
        form_criteria_query = supabase.table("form_criteria").select("*").eq("form_id", evaluation_data.form_id)
        duplicate_check_query = supabase.table("evaluations").select("id").eq("form_id", evaluation_data.form_id).eq("evaluator_id", evaluation_data.evaluator_id).eq("evaluatee_id", evaluation_data.evaluatee_id)

        # Execute queries
        team = team_query.execute()
        evaluator = evaluator_query.execute()
        evaluatee = evaluatee_query.execute()
        form_criteria = form_criteria_query.execute()
        existing = duplicate_check_query.execute()

        # Validate team exists
        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Validate evaluator exists
        if not evaluator.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluator not found"
            )

        # Validate evaluatee exists
        if not evaluatee.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluatee not found"
            )

        # Check for duplicate evaluation
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already evaluated this team member for this form"
            )

        # Validate team membership (parallel queries)
        evaluator_member = supabase.table("team_members").select("id").eq("team_id", evaluation_data.team_id).eq("user_id", evaluation_data.evaluator_id).execute()
        evaluatee_member = supabase.table("team_members").select("id").eq("team_id", evaluation_data.team_id).eq("user_id", evaluation_data.evaluatee_id).execute()

        if not evaluator_member.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evaluator is not a member of this team"
            )

        if not evaluatee_member.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evaluatee is not a member of this team"
            )

        # Validate all criteria belong to the form
        valid_criterion_ids = [c["id"] for c in form_criteria.data] if form_criteria.data else []

        for score in evaluation_data.scores:
            if score.criterion_id not in valid_criterion_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Criterion {score.criterion_id} does not belong to this form"
                )

        # OPETSE-14: Calculate weighted score
        criteria_data = form_criteria.data if form_criteria.data else []
        scores_list = [{"criterion_id": s.criterion_id, "score": s.score} for s in evaluation_data.scores]

        weighted_result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores_list,
            criteria=criteria_data,
            max_score=form_data.get("max_score", 100)
        )

        # Use weighted total as the official score
        calculated_total = weighted_result["weighted_total"]

        # Create evaluation
        new_evaluation = {
            "form_id": evaluation_data.form_id,
            "evaluator_id": evaluation_data.evaluator_id,
            "evaluatee_id": evaluation_data.evaluatee_id,
            "team_id": evaluation_data.team_id,
            "total_score": calculated_total,  # OPETSE-14: Use weighted score
            "comments": evaluation_data.comments
        }

        result = supabase.table("evaluations").insert(new_evaluation).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create evaluation"
            )

        created_evaluation = result.data[0]
        evaluation_id = created_evaluation["id"]

        # OPETSE-21: Batch insert scores for better performance (instead of individual inserts)
        scores_to_insert = [
            {
                "evaluation_id": evaluation_id,
                "criterion_id": score.criterion_id,
                "score": score.score
            }
            for score in evaluation_data.scores
        ]

        # Batch insert all scores at once
        if scores_to_insert:
            batch_result = supabase.table("evaluation_scores").insert(scores_to_insert).execute()
            scores_data = batch_result.data if batch_result.data else []
        else:
            scores_data = []

        created_evaluation["scores"] = scores_data

        # OPETSE-14: Include weighted scoring breakdown in response
        created_evaluation["weighted_breakdown"] = weighted_result["breakdown"]
        created_evaluation["score_percentage"] = weighted_result["percentage"]

        # OPETSE-21: Calculate and include submission time
        submission_time = time.time() - start_time
        created_evaluation["submission_time_seconds"] = round(submission_time, 3)

        return {
            "evaluation": created_evaluation,
            "message": "Evaluation submitted successfully",
            "weighted_scoring_applied": True,
            "submission_time_seconds": round(submission_time, 3)  # OPETSE-21: Performance metric
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit evaluation: {str(e)}"
        )


@router.get("/{evaluation_id}")
async def get_evaluation(
    evaluation_id: int,
    requester_role: Optional[str] = Query(None, description="Role of requesting user for anonymity")
):
    """
    Get detailed evaluation by ID.

    OPETSE-8: Evaluator identity is anonymized for students.
    Only instructors and admins can see who submitted the evaluation.
    """
    try:
        # Get evaluation
        result = supabase.table("evaluations").select("*").eq("id", evaluation_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )

        evaluation = result.data[0]

        # Get evaluator details
        evaluator = supabase.table("users").select("id, name, email").eq("id", evaluation["evaluator_id"]).execute()
        evaluation["evaluator"] = evaluator.data[0] if evaluator.data else None

        # Get evaluatee details
        evaluatee = supabase.table("users").select("id, name, email").eq("id", evaluation["evaluatee_id"]).execute()
        evaluation["evaluatee"] = evaluatee.data[0] if evaluatee.data else None

        # Get team details
        team = supabase.table("teams").select("*").eq("id", evaluation["team_id"]).execute()
        evaluation["team"] = team.data[0] if team.data else None

        # Get form details with criteria
        form = supabase.table("evaluation_forms").select("*").eq("id", evaluation["form_id"]).execute()
        evaluation["form"] = form.data[0] if form.data else None

        # Get scores with criteria details
        scores = supabase.table("evaluation_scores").select("*").eq("evaluation_id", evaluation_id).execute()

        if scores.data:
            for score in scores.data:
                criterion = supabase.table("form_criteria").select("*").eq("id", score["criterion_id"]).execute()
                score["criterion"] = criterion.data[0] if criterion.data else None

            evaluation["scores"] = scores.data
        else:
            evaluation["scores"] = []

        # OPETSE-8: Apply anonymization based on requester role
        anonymized_evaluation = anonymize_evaluator(
            evaluation,
            requester_role=requester_role
        )

        return {
            "evaluation": anonymized_evaluation,
            "message": "Evaluation retrieved successfully",
            "anonymized": requester_role not in ["instructor", "admin"] if requester_role else True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evaluation: {str(e)}"
        )


@router.put("/{evaluation_id}")
async def update_evaluation(evaluation_id: int, evaluation_data: EvaluationUpdate):
    """Update an existing evaluation."""
    try:
        # Check if evaluation exists
        existing = supabase.table("evaluations").select("*").eq("id", evaluation_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )

        # Build update dict
        update_data = {}
        if evaluation_data.total_score is not None:
            update_data["total_score"] = evaluation_data.total_score
        if evaluation_data.comments is not None:
            update_data["comments"] = evaluation_data.comments

        # Update evaluation if there are changes
        if update_data:
            result = supabase.table("evaluations").update(update_data).eq("id", evaluation_id).execute()

            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update evaluation"
                )

        # Update scores if provided
        if evaluation_data.scores is not None:
            # Delete existing scores
            supabase.table("evaluation_scores").delete().eq("evaluation_id", evaluation_id).execute()

            # Insert new scores
            for score in evaluation_data.scores:
                score_entry = {
                    "evaluation_id": evaluation_id,
                    "criterion_id": score.criterion_id,
                    "score": score.score
                }
                supabase.table("evaluation_scores").insert(score_entry).execute()

        # Get updated evaluation
        updated = supabase.table("evaluations").select("*").eq("id", evaluation_id).execute()
        evaluation = updated.data[0] if updated.data else {}

        # Get scores
        scores = supabase.table("evaluation_scores").select("*").eq("evaluation_id", evaluation_id).execute()
        evaluation["scores"] = scores.data if scores.data else []

        return {
            "evaluation": evaluation,
            "message": "Evaluation updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update evaluation: {str(e)}"
        )


@router.delete("/{evaluation_id}")
async def delete_evaluation(evaluation_id: int):
    """Delete an evaluation."""
    try:
        # Check if evaluation exists
        existing = supabase.table("evaluations").select("*").eq("id", evaluation_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )

        # Delete evaluation (cascade will handle scores)
        result = supabase.table("evaluations").delete().eq("id", evaluation_id).execute()

        return {
            "message": f"Evaluation {evaluation_id} deleted successfully",
            "deleted_evaluation": existing.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete evaluation: {str(e)}"
        )


@router.get("/student/{student_id}")
async def get_student_evaluations(student_id: int):
    """
    Get a student's pending and completed evaluations for their dashboard.

    OPETSE-13: As a student, I want a dashboard showing my pending and completed evaluations.

    Returns:
    - pending: List of evaluations the student needs to complete (teammates they haven't evaluated)
    - completed: List of evaluations the student has already submitted
    """
    try:
        # Get all teams the student is a member of
        team_members = supabase.table("team_members").select("team_id").eq("user_id", student_id).execute()

        if not team_members.data:
            return {
                "pending": [],
                "completed": [],
                "message": "Student is not a member of any team"
            }

        team_ids = [tm["team_id"] for tm in team_members.data]

        # Get all completed evaluations where this student is the evaluator
        completed_evals = []
        for team_id in team_ids:
            evals = supabase.table("evaluations").select("*").eq("team_id", team_id).eq("evaluator_id", student_id).execute()
            if evals.data:
                completed_evals.extend(evals.data)

        # Enrich completed evaluations with details
        for evaluation in completed_evals:
            # Get evaluatee details
            evaluatee = supabase.table("users").select("id, name, email").eq("id", evaluation["evaluatee_id"]).execute()
            evaluation["evaluatee"] = evaluatee.data[0] if evaluatee.data else None

            # Get team details
            team = supabase.table("teams").select("id, name").eq("id", evaluation["team_id"]).execute()
            evaluation["team"] = team.data[0] if team.data else None

            # Get form details
            form = supabase.table("evaluation_forms").select("id, title, deadline").eq("id", evaluation["form_id"]).execute()
            evaluation["form"] = form.data[0] if form.data else None

        # Get all active evaluation forms for the student's teams
        pending_evals = []
        for team_id in team_ids:
            # Get team details
            team = supabase.table("teams").select("*").eq("id", team_id).execute()
            if not team.data:
                continue

            team_data = team.data[0]

            # Get all teammates (excluding the student themselves)
            teammates = supabase.table("team_members").select("user_id").eq("team_id", team_id).neq("user_id", student_id).execute()

            if not teammates.data:
                continue

            # Get active forms for this team (forms linked to team's project)
            project_id = team_data.get("project_id")
            if not project_id:
                continue

            forms = supabase.table("evaluation_forms").select("*").eq("project_id", project_id).execute()

            if not forms.data:
                continue

            # For each form, check which teammates haven't been evaluated yet
            for form in forms.data:
                # Skip if deadline has passed
                if is_deadline_passed(form.get("deadline")):
                    continue

                for teammate in teammates.data:
                    teammate_id = teammate["user_id"]

                    # Check if student has already evaluated this teammate for this form
                    existing_eval = supabase.table("evaluations").select("id").eq("form_id", form["id"]).eq("evaluator_id", student_id).eq("evaluatee_id", teammate_id).execute()

                    if not existing_eval.data:
                        # Get teammate details
                        teammate_info = supabase.table("users").select("id, name, email").eq("id", teammate_id).execute()

                        pending_evals.append({
                            "form_id": form["id"],
                            "form_title": form.get("title"),
                            "form_deadline": form.get("deadline"),
                            "team_id": team_id,
                            "team_name": team_data.get("name"),
                            "evaluatee_id": teammate_id,
                            "evaluatee": teammate_info.data[0] if teammate_info.data else None
                        })

        return {
            "pending": pending_evals,
            "completed": completed_evals,
            "pending_count": len(pending_evals),
            "completed_count": len(completed_evals),
            "message": "Student evaluations retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve student evaluations: {str(e)}"
        )
