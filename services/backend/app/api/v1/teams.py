"""Team management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from app.db import get_db
from app.core.supabase import supabase

router = APIRouter(prefix="/teams", tags=["teams"])


# Pydantic models
class TeamCreate(BaseModel):
    project_id: int
    name: str
    member_ids: List[str]


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    member_ids: Optional[List[str]] = None


class MemberAdd(BaseModel):
    user_id: str


@router.get("/")
async def list_teams(project_id: Optional[int] = None):
    """List all teams with optional project filter."""
    try:
        query = supabase.table("teams").select("*")
        
        # Filter by project if provided
        if project_id:
            query = query.eq("project_id", project_id)
        
        result = query.order("created_at", desc=True).execute()
        
        # Get members for each team
        teams = result.data
        for team in teams:
            # Get team members
            members_data = supabase.table("team_members").select("*").eq("team_id", team["id"]).execute()
            
            # Get user details for each member
            team["members"] = []
            if members_data.data:
                for member in members_data.data:
                    user = supabase.table("users").select("id, name, email, role").eq("id", member["user_id"]).execute()
                    if user.data:
                        team["members"].append(user.data[0])
            
            # Get project details
            project = supabase.table("projects").select("id, title").eq("id", team["project_id"]).execute()
            team["project"] = project.data[0] if project.data else None
        
        return {
            "teams": teams,
            "count": len(teams),
            "message": "Teams retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve teams: {str(e)}"
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_team(team_data: TeamCreate):
    """Create a new team with members."""
    try:
        # Verify project exists
        project = supabase.table("projects").select("*").eq("id", team_data.project_id).execute()
        
        if not project.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Verify all members exist and are students
        for user_id in team_data.member_ids:
            user = supabase.table("users").select("id, role").eq("id", user_id).execute()
            
            if not user.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with id {user_id} not found"
                )
            
            if user.data[0]["role"] != "student":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {user_id} must be a student to join a team"
                )
        
        # Create team
        new_team = {
            "project_id": team_data.project_id,
            "name": team_data.name
        }
        
        result = supabase.table("teams").insert(new_team).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create team"
            )
        
        created_team = result.data[0]
        team_id = created_team["id"]
        
        # Add team members
        members = []
        for user_id in team_data.member_ids:
            member_data = {
                "team_id": team_id,
                "user_id": user_id
            }
            member_result = supabase.table("team_members").insert(member_data).execute()
            if member_result.data:
                members.append(member_result.data[0])
        
        # Get full member details
        team_members = []
        for member in members:
            user = supabase.table("users").select("id, name, email, role").eq("id", member["user_id"]).execute()
            if user.data:
                team_members.append(user.data[0])
        
        created_team["members"] = team_members
        
        return {
            "team": created_team,
            "message": f"Team created successfully with {len(team_members)} members"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}"
        )


@router.get("/{team_id}")
async def get_team(team_id: int):
    """Get team details with members and project info."""
    try:
        # Get team
        result = supabase.table("teams").select("*").eq("id", team_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        team = result.data[0]
        
        # Get project details
        project = supabase.table("projects").select("*").eq("id", team["project_id"]).execute()
        team["project"] = project.data[0] if project.data else None
        
        # Get team members
        members_data = supabase.table("team_members").select("*").eq("team_id", team_id).execute()
        
        team["members"] = []
        if members_data.data:
            for member in members_data.data:
                user = supabase.table("users").select("id, name, email, role").eq("id", member["user_id"]).execute()
                if user.data:
                    team["members"].append(user.data[0])
        
        return {
            "team": team,
            "message": "Team retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team: {str(e)}"
        )


@router.put("/{team_id}")
async def update_team(team_id: int, team_data: TeamUpdate):
    """Update team details and/or members."""
    try:
        # Check if team exists
        existing = supabase.table("teams").select("*").eq("id", team_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Update team name if provided
        if team_data.name is not None:
            update_data = {"name": team_data.name}
            result = supabase.table("teams").update(update_data).eq("id", team_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update team"
                )
        
        # Update members if provided
        if team_data.member_ids is not None:
            # Verify all new members exist and are students
            for user_id in team_data.member_ids:
                user = supabase.table("users").select("id, role").eq("id", user_id).execute()
                
                if not user.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"User with id {user_id} not found"
                    )
                
                if user.data[0]["role"] != "student":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"User {user_id} must be a student"
                    )
            
            # Remove all existing members
            supabase.table("team_members").delete().eq("team_id", team_id).execute()
            
            # Add new members
            for user_id in team_data.member_ids:
                member_data = {
                    "team_id": team_id,
                    "user_id": user_id
                }
                supabase.table("team_members").insert(member_data).execute()
        
        # Get updated team with members
        updated_team = supabase.table("teams").select("*").eq("id", team_id).execute()
        team = updated_team.data[0] if updated_team.data else {}
        
        # Get members
        members_data = supabase.table("team_members").select("*").eq("team_id", team_id).execute()
        team["members"] = []
        if members_data.data:
            for member in members_data.data:
                user = supabase.table("users").select("id, name, email, role").eq("id", member["user_id"]).execute()
                if user.data:
                    team["members"].append(user.data[0])
        
        return {
            "team": team,
            "message": "Team updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team: {str(e)}"
        )


@router.delete("/{team_id}")
async def delete_team(team_id: int):
    """Delete a team and all its members."""
    try:
        # Check if team exists
        existing = supabase.table("teams").select("*").eq("id", team_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Delete team (cascade will handle team_members)
        result = supabase.table("teams").delete().eq("id", team_id).execute()
        
        return {
            "message": f"Team {team_id} deleted successfully",
            "deleted_team": existing.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete team: {str(e)}"
        )


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(team_id: int, member_data: MemberAdd):
    """Add a single member to an existing team."""
    try:
        # Verify team exists
        team = supabase.table("teams").select("*").eq("id", team_id).execute()
        
        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Verify user exists and is a student
        user = supabase.table("users").select("id, role").eq("id", member_data.user_id).execute()
        
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.data[0]["role"] != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be a student to join a team"
            )
        
        # Check if already a member
        existing_member = supabase.table("team_members").select("*").eq("team_id", team_id).eq("user_id", member_data.user_id).execute()
        
        if existing_member.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this team"
            )
        
        # Add member
        new_member = {
            "team_id": team_id,
            "user_id": member_data.user_id
        }
        
        result = supabase.table("team_members").insert(new_member).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add member"
            )
        
        # Get user details
        user_details = supabase.table("users").select("id, name, email, role").eq("id", member_data.user_id).execute()
        
        return {
            "member": user_details.data[0] if user_details.data else {},
            "message": "Member added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add member: {str(e)}"
        )


@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(team_id: int, user_id: str):
    """Remove a member from a team."""
    try:
        # Check if team exists
        team = supabase.table("teams").select("*").eq("id", team_id).execute()
        
        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check if user is a member
        member = supabase.table("team_members").select("*").eq("team_id", team_id).eq("user_id", user_id).execute()
        
        if not member.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this team"
            )
        
        # Remove member
        result = supabase.table("team_members").delete().eq("team_id", team_id).eq("user_id", user_id).execute()
        
        return {
            "message": f"User {user_id} removed from team {team_id} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )
