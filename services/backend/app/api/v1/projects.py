"""Project management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.db import get_db
from app.core.supabase import supabase

router = APIRouter(prefix="/projects", tags=["projects"])


# Pydantic models
class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    instructor_id: str  # UUID as string
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "active"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


@router.get("/")
async def list_projects(instructor_id: Optional[str] = None, status: Optional[str] = None):
    """List all projects with optional filters."""
    try:
        # Get projects without JOIN first (simpler and more reliable)
        query = supabase.table("projects").select("*")
        
        # Apply filters if provided
        if instructor_id:
            query = query.eq("instructor_id", instructor_id)
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).execute()
        
        # Fetch instructor details separately for each project
        projects = result.data
        for project in projects:
            instructor = supabase.table("users").select("id, name, email, role").eq("id", project["instructor_id"]).execute()
            project["instructor"] = instructor.data[0] if instructor.data else None
        
        return {
            "projects": projects,
            "count": len(projects),
            "message": "Projects retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreate):
    """Create a new project."""
    try:
        # Verify instructor exists
        instructor = supabase.table("users").select("id, role").eq("id", project_data.instructor_id).execute()
        
        if not instructor.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )
        
        if instructor.data[0]["role"] != "instructor":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must have 'instructor' role to create projects"
            )
        
        # Create project
        new_project = {
            "title": project_data.title,
            "description": project_data.description,
            "instructor_id": project_data.instructor_id,
            "start_date": str(project_data.start_date) if project_data.start_date else None,
            "end_date": str(project_data.end_date) if project_data.end_date else None,
            "status": project_data.status
        }
        
        result = supabase.table("projects").insert(new_project).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project"
            )
        
        created_project = result.data[0]
        return {
            "project": created_project,
            "message": "Project created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/{project_id}")
async def get_project(project_id: int):
    """Get project by ID with instructor details and teams."""
    try:
        # Get project
        result = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = result.data[0]
        
        # Get instructor details
        instructor = supabase.table("users").select("id, name, email, role").eq("id", project["instructor_id"]).execute()
        project["instructor"] = instructor.data[0] if instructor.data else None
        
        # Get teams for this project
        teams = supabase.table("teams").select("*").eq("project_id", project_id).execute()
        
        # For each team, get members
        if teams.data:
            for team in teams.data:
                members = supabase.table("team_members").select("*").eq("team_id", team["id"]).execute()
                
                # Get user details for each member
                team["members"] = []
                if members.data:
                    for member in members.data:
                        user = supabase.table("users").select("id, name, email").eq("id", member["user_id"]).execute()
                        if user.data:
                            team["members"].append(user.data[0])
        
        project["teams"] = teams.data if teams.data else []
        
        return {
            "project": project,
            "message": "Project retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project: {str(e)}"
        )


@router.put("/{project_id}")
async def update_project(project_id: int, project_data: ProjectUpdate):
    """Update project details."""
    try:
        # Check if project exists
        existing = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Build update dict (only include provided fields)
        update_data = {}
        if project_data.title is not None:
            update_data["title"] = project_data.title
        if project_data.description is not None:
            update_data["description"] = project_data.description
        if project_data.start_date is not None:
            update_data["start_date"] = str(project_data.start_date)
        if project_data.end_date is not None:
            update_data["end_date"] = str(project_data.end_date)
        if project_data.status is not None:
            update_data["status"] = project_data.status
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )
        
        # Update project
        result = supabase.table("projects").update(update_data).eq("id", project_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update project"
            )
        
        return {
            "project": result.data[0],
            "message": "Project updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """Delete a project."""
    try:
        # Check if project exists
        existing = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Delete project (cascade will handle related records)
        result = supabase.table("projects").delete().eq("id", project_id).execute()
        
        return {
            "message": f"Project {project_id} deleted successfully",
            "deleted_project": existing.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
