"""Form/rubric management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from app.db import get_db
from app.core.supabase import supabase
from app.utils.deadline import is_deadline_passed, get_time_remaining
from app.utils.weighted_scoring import WeightedScoringCalculator

router = APIRouter(prefix="/forms", tags=["forms"])


# OPETSE-25: Helper function to create form version snapshot
async def create_form_version(form_id: int, created_by: Optional[int] = None) -> Dict[str, Any]:
    """
    Create a version snapshot of a form before modification.
    Returns the created version or None if creation failed.
    """
    try:
        # Get current form data
        form_result = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()
        if not form_result.data:
            return None

        form_data = form_result.data[0]

        # Get all criteria
        criteria_result = supabase.table("form_criteria").select("*").eq("form_id", form_id).order("order_index").execute()
        criteria_data = criteria_result.data if criteria_result.data else []

        # Get next version number
        versions_result = supabase.table("form_versions").select("version_number").eq("form_id", form_id).order("version_number", desc=True).limit(1).execute()
        next_version = 1
        if versions_result.data and len(versions_result.data) > 0:
            next_version = versions_result.data[0]["version_number"] + 1

        # Create version snapshot
        version_data = {
            "form_id": form_id,
            "version_number": next_version,
            "title": form_data["title"],
            "description": form_data.get("description"),
            "max_score": form_data.get("max_score", 100),
            "deadline": form_data.get("deadline"),
            "criteria": json.dumps(criteria_data),  # Store criteria as JSON
            "created_by": created_by
        }

        result = supabase.table("form_versions").insert(version_data).execute()
        return result.data[0] if result.data else None

    except Exception as e:
        print(f"Failed to create form version: {str(e)}")
        return None


# Pydantic models
class FormCriterion(BaseModel):
    text: str
    max_points: int
    order_index: int
    weight: Optional[float] = None  # OPETSE-14: Criterion weight (0-100%)


class FormCreate(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = None
    max_score: int = 100
    criteria: List[FormCriterion]
    deadline: Optional[str] = None  # ISO format datetime string (OPETSE-9)


class FormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_score: Optional[int] = None
    deadline: Optional[str] = None  # ISO format datetime string (OPETSE-9)


class CriterionUpdate(BaseModel):
    text: Optional[str] = None
    max_points: Optional[int] = None
    order_index: Optional[int] = None
    weight: Optional[float] = None  # OPETSE-14: Criterion weight


@router.get("/")
async def list_forms(project_id: Optional[int] = None):
    """List all evaluation forms with optional project filter."""
    try:
        query = supabase.table("evaluation_forms").select("*")

        # Filter by project if provided
        if project_id:
            query = query.eq("project_id", project_id)

        result = query.order("created_at", desc=True).execute()

        # Get criteria for each form
        forms = result.data
        for form in forms:
            # Get project details
            project = supabase.table("projects").select("id, title").eq("id", form["project_id"]).execute()
            form["project"] = project.data[0] if project.data else None

            # Get criteria
            criteria = supabase.table("form_criteria").select("*").eq("form_id", form["id"]).order("order_index").execute()
            form["criteria"] = criteria.data if criteria.data else []
            form["criteria_count"] = len(criteria.data) if criteria.data else 0

            # Add deadline status (OPETSE-9)
            form["is_expired"] = is_deadline_passed(form.get("deadline"))
            form["time_remaining"] = get_time_remaining(form.get("deadline"))

        return {
            "forms": forms,
            "count": len(forms),
            "message": "Evaluation forms retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve forms: {str(e)}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_form(form_data: FormCreate):
    """Create a new evaluation form with criteria."""
    try:
        # Verify project exists
        project = supabase.table("projects").select("*").eq("id", form_data.project_id).execute()

        if not project.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Validate criteria
        if not form_data.criteria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Form must have at least one criterion"
            )

        # Check that max_points sum up reasonably
        total_points = sum(c.max_points for c in form_data.criteria)
        if total_points != form_data.max_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sum of criterion max_points ({total_points}) should equal form max_score ({form_data.max_score})"
            )

        # OPETSE-14: Handle weights
        criteria_with_weights = []
        for criterion in form_data.criteria:
            criteria_with_weights.append({
                'id': None,  # Will be assigned after creation
                'weight': criterion.weight if criterion.weight is not None else 0,
                'text': criterion.text
            })

        # If weights provided, validate them
        has_weights = any(c.weight is not None for c in form_data.criteria)
        if has_weights:
            is_valid, error_msg = WeightedScoringCalculator.validate_weights(criteria_with_weights)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid weights: {error_msg}"
                )
        else:
            # Auto-distribute weights evenly
            even_weights = WeightedScoringCalculator.distribute_weights_evenly(len(form_data.criteria))
            for i, criterion in enumerate(form_data.criteria):
                criterion.weight = float(even_weights[i])

        # Create form
        new_form = {
            "project_id": form_data.project_id,
            "title": form_data.title,
            "description": form_data.description,
            "max_score": form_data.max_score,
            "deadline": form_data.deadline  # OPETSE-9: Store deadline
        }

        result = supabase.table("evaluation_forms").insert(new_form).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create form"
            )

        created_form = result.data[0]
        form_id = created_form["id"]

        # Create criteria
        criteria_data = []
        for criterion in form_data.criteria:
            criterion_entry = {
                "form_id": form_id,
                "text": criterion.text,
                "max_points": criterion.max_points,
                "order_index": criterion.order_index,
                "weight": criterion.weight  # OPETSE-14: Include weight
            }
            criterion_result = supabase.table("form_criteria").insert(criterion_entry).execute()
            if criterion_result.data:
                criteria_data.append(criterion_result.data[0])

        created_form["criteria"] = criteria_data

        return {
            "form": created_form,
            "message": f"Evaluation form created successfully with {len(criteria_data)} criteria"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create form: {str(e)}"
        )


@router.get("/{form_id}")
async def get_form(form_id: int):
    """Get evaluation form with all criteria."""
    try:
        # Get form
        result = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation form not found"
            )

        form = result.data[0]

        # Get project details
        project = supabase.table("projects").select("*").eq("id", form["project_id"]).execute()
        form["project"] = project.data[0] if project.data else None

        # Get criteria
        criteria = supabase.table("form_criteria").select("*").eq("form_id", form_id).order("order_index").execute()
        form["criteria"] = criteria.data if criteria.data else []

        # Get usage statistics
        evaluations = supabase.table("evaluations").select("id").eq("form_id", form_id).execute()
        form["usage_count"] = len(evaluations.data) if evaluations.data else 0

        return {
            "form": form,
            "message": "Evaluation form retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve form: {str(e)}"
        )


@router.put("/{form_id}")
async def update_form(form_id: int, form_data: FormUpdate):
    """Update evaluation form details (not criteria)."""
    try:
        # Check if form exists
        existing = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation form not found"
            )

        # OPETSE-25: Create version snapshot before update
        await create_form_version(form_id)

        # Build update dict
        update_data = {}
        if form_data.title is not None:
            update_data["title"] = form_data.title
        if form_data.description is not None:
            update_data["description"] = form_data.description
        if form_data.max_score is not None:
            update_data["max_score"] = form_data.max_score
        if form_data.deadline is not None:
            update_data["deadline"] = form_data.deadline  # OPETSE-9: Update deadline

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        # Update form
        result = supabase.table("evaluation_forms").update(update_data).eq("id", form_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update form"
            )

        # Get updated form with criteria
        updated_form = result.data[0]
        criteria = supabase.table("form_criteria").select("*").eq("form_id", form_id).order("order_index").execute()
        updated_form["criteria"] = criteria.data if criteria.data else []

        return {
            "form": updated_form,
            "message": "Evaluation form updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update form: {str(e)}"
        )


@router.delete("/{form_id}")
async def delete_form(form_id: int):
    """Delete an evaluation form and all its criteria."""
    try:
        # Check if form exists
        existing = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation form not found"
            )

        # Check if form is being used in evaluations
        evaluations = supabase.table("evaluations").select("id").eq("form_id", form_id).execute()

        if evaluations.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete form. It is being used in {len(evaluations.data)} evaluation(s)"
            )

        # Delete form (cascade will handle criteria)
        result = supabase.table("evaluation_forms").delete().eq("id", form_id).execute()

        return {
            "message": f"Evaluation form {form_id} deleted successfully",
            "deleted_form": existing.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete form: {str(e)}"
        )


@router.post("/{form_id}/criteria", status_code=status.HTTP_201_CREATED)
async def add_criterion(form_id: int, criterion_data: FormCriterion):
    """Add a new criterion to an existing form."""
    try:
        # Verify form exists
        form = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()

        if not form.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation form not found"
            )

        # OPETSE-14: Set default weight if not provided
        weight = criterion_data.weight if criterion_data.weight is not None else 0.0

        # Create criterion
        new_criterion = {
            "form_id": form_id,
            "text": criterion_data.text,
            "max_points": criterion_data.max_points,
            "order_index": criterion_data.order_index,
            "weight": weight  # OPETSE-14
        }

        result = supabase.table("form_criteria").insert(new_criterion).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add criterion"
            )

        return {
            "criterion": result.data[0],
            "message": "Criterion added successfully. Remember to adjust weights to sum to 100%"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add criterion: {str(e)}"
        )


@router.put("/{form_id}/criteria/{criterion_id}")
async def update_criterion(form_id: int, criterion_id: int, criterion_data: CriterionUpdate):
    """Update a specific criterion."""
    try:
        # Verify criterion exists and belongs to form
        existing = supabase.table("form_criteria").select("*").eq("id", criterion_id).eq("form_id", form_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Criterion not found or does not belong to this form"
            )

        # OPETSE-25: Create version snapshot before update
        await create_form_version(form_id)

        # Build update dict
        update_data = {}
        if criterion_data.text is not None:
            update_data["text"] = criterion_data.text
        if criterion_data.max_points is not None:
            update_data["max_points"] = criterion_data.max_points
        if criterion_data.order_index is not None:
            update_data["order_index"] = criterion_data.order_index
        if criterion_data.weight is not None:  # OPETSE-14
            update_data["weight"] = criterion_data.weight

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        # Update criterion
        result = supabase.table("form_criteria").update(update_data).eq("id", criterion_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update criterion"
            )

        return {
            "criterion": result.data[0],
            "message": "Criterion updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update criterion: {str(e)}"
        )


@router.delete("/{form_id}/criteria/{criterion_id}")
async def delete_criterion(form_id: int, criterion_id: int):
    """Delete a criterion from a form."""
    try:
        # Verify criterion exists and belongs to form
        existing = supabase.table("form_criteria").select("*").eq("id", criterion_id).eq("form_id", form_id).execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Criterion not found or does not belong to this form"
            )

        # Check if criterion is being used in evaluation scores
        scores = supabase.table("evaluation_scores").select("id").eq("criterion_id", criterion_id).execute()

        if scores.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete criterion. It is being used in {len(scores.data)} evaluation score(s)"
            )

        # OPETSE-25: Create version snapshot before delete
        await create_form_version(form_id)

        # Delete criterion
        result = supabase.table("form_criteria").delete().eq("id", criterion_id).execute()

        return {
            "message": f"Criterion {criterion_id} deleted successfully",
            "deleted_criterion": existing.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete criterion: {str(e)}"
        )


# OPETSE-19: Rubric Template Reuse
class FormDuplicate(BaseModel):
    target_project_id: int
    new_title: Optional[str] = None


@router.post("/{form_id}/duplicate", status_code=status.HTTP_201_CREATED)
async def duplicate_form(form_id: int, duplicate_data: FormDuplicate):
    """
    Duplicate an existing form to reuse as a template.
    Creates a copy of the form with all its criteria for a new project.
    OPETSE-19: Rubric template reuse feature.
    """
    try:
        # Get original form
        original_form = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()

        if not original_form.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source form not found"
            )

        form_data = original_form.data[0]

        # Verify target project exists
        target_project = supabase.table("projects").select("id, title").eq("id", duplicate_data.target_project_id).execute()

        if not target_project.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target project not found"
            )

        # Get original criteria
        original_criteria = supabase.table("form_criteria").select("*").eq("form_id", form_id).order("order_index").execute()

        if not original_criteria.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source form has no criteria to duplicate"
            )

        # Create new form (duplicate)
        new_title = duplicate_data.new_title or f"{form_data['title']} (Copy)"

        new_form_data = {
            "project_id": duplicate_data.target_project_id,
            "title": new_title,
            "description": form_data.get("description"),
            "max_score": form_data.get("max_score", 100),
            "deadline": form_data.get("deadline")
        }

        new_form_result = supabase.table("evaluation_forms").insert(new_form_data).execute()

        if not new_form_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create duplicated form"
            )

        duplicated_form = new_form_result.data[0]
        new_form_id = duplicated_form["id"]

        # Duplicate all criteria
        duplicated_criteria = []
        for criterion in original_criteria.data:
            new_criterion = {
                "form_id": new_form_id,
                "text": criterion["text"],
                "max_points": criterion["max_points"],
                "order_index": criterion["order_index"],
                "weight": criterion.get("weight")  # OPETSE-14: Include weight if present
            }

            criterion_result = supabase.table("form_criteria").insert(new_criterion).execute()

            if criterion_result.data:
                duplicated_criteria.append(criterion_result.data[0])

        duplicated_form["criteria"] = duplicated_criteria
        duplicated_form["project"] = target_project.data[0]

        return {
            "form": duplicated_form,
            "message": f"Form duplicated successfully with {len(duplicated_criteria)} criteria",
            "source_form_id": form_id,
            "original_title": form_data["title"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate form: {str(e)}"
        )


# OPETSE-25: Form Rollback Capability
@router.get("/{form_id}/versions")
async def list_form_versions(form_id: int):
    """
    List all version history for a form.
    OPETSE-25: Rollback capability - view form history.
    """
    try:
        # Verify form exists
        form_result = supabase.table("evaluation_forms").select("id, title").eq("id", form_id).execute()

        if not form_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )

        # Get all versions
        versions_result = supabase.table("form_versions").select("*").eq("form_id", form_id).order("version_number", desc=True).execute()

        versions = []
        if versions_result.data:
            for version in versions_result.data:
                # Parse criteria JSON
                criteria = json.loads(version["criteria"]) if version["criteria"] else []

                versions.append({
                    "id": version["id"],
                    "version_number": version["version_number"],
                    "title": version["title"],
                    "description": version.get("description"),
                    "max_score": version.get("max_score", 100),
                    "deadline": version.get("deadline"),
                    "criteria_count": len(criteria),
                    "created_at": version["created_at"],
                    "created_by": version.get("created_by")
                })

        return {
            "form_id": form_id,
            "form_title": form_result.data[0]["title"],
            "versions": versions,
            "total_versions": len(versions),
            "message": f"Retrieved {len(versions)} version(s) for form"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve form versions: {str(e)}"
        )


@router.get("/{form_id}/versions/{version_id}")
async def get_form_version(form_id: int, version_id: int):
    """
    Get details of a specific form version.
    OPETSE-25: Rollback capability - view specific version.
    """
    try:
        # Get version
        version_result = supabase.table("form_versions").select("*").eq("id", version_id).eq("form_id", form_id).execute()

        if not version_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found or does not belong to this form"
            )

        version = version_result.data[0]

        # Parse criteria JSON
        criteria = json.loads(version["criteria"]) if version["criteria"] else []

        return {
            "version": {
                "id": version["id"],
                "form_id": version["form_id"],
                "version_number": version["version_number"],
                "title": version["title"],
                "description": version.get("description"),
                "max_score": version.get("max_score", 100),
                "deadline": version.get("deadline"),
                "criteria": criteria,
                "created_at": version["created_at"],
                "created_by": version.get("created_by")
            },
            "message": "Version retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve version: {str(e)}"
        )


@router.post("/{form_id}/rollback/{version_id}", status_code=status.HTTP_200_OK)
async def rollback_form(form_id: int, version_id: int):
    """
    Rollback form to a previous version.
    Restores form metadata and all criteria from the selected version.
    OPETSE-25: Rollback capability for accidental changes.
    """
    try:
        # Verify form exists
        form_result = supabase.table("evaluation_forms").select("*").eq("id", form_id).execute()

        if not form_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )

        # Get version to restore
        version_result = supabase.table("form_versions").select("*").eq("id", version_id).eq("form_id", form_id).execute()

        if not version_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found or does not belong to this form"
            )

        version = version_result.data[0]

        # Create a version snapshot of current state before rollback
        await create_form_version(form_id)

        # Parse criteria from version
        criteria_from_version = json.loads(version["criteria"]) if version["criteria"] else []

        # Update form metadata
        form_update = {
            "title": version["title"],
            "description": version.get("description"),
            "max_score": version.get("max_score", 100),
            "deadline": version.get("deadline")
        }

        form_update_result = supabase.table("evaluation_forms").update(form_update).eq("id", form_id).execute()

        if not form_update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update form during rollback"
            )

        # Delete all current criteria
        supabase.table("form_criteria").delete().eq("form_id", form_id).execute()

        # Restore criteria from version
        restored_criteria = []
        for criterion in criteria_from_version:
            new_criterion = {
                "form_id": form_id,
                "text": criterion["text"],
                "max_points": criterion["max_points"],
                "order_index": criterion.get("order_index", 0),
                "weight": criterion.get("weight")
            }

            criterion_result = supabase.table("form_criteria").insert(new_criterion).execute()

            if criterion_result.data:
                restored_criteria.append(criterion_result.data[0])

        # Get final restored form
        restored_form = form_update_result.data[0]
        restored_form["criteria"] = restored_criteria

        return {
            "form": restored_form,
            "rolled_back_to": {
                "version_id": version_id,
                "version_number": version["version_number"],
                "created_at": version["created_at"]
            },
            "message": f"Form successfully rolled back to version {version['version_number']} with {len(restored_criteria)} criteria"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback form: {str(e)}"
        )
