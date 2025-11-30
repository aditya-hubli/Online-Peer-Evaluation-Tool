"""Team chat management routes (OPETSE-18)."""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.supabase import supabase

router = APIRouter(prefix="/chats", tags=["chats"])


# Pydantic models
class MessageCreate(BaseModel):
    """Schema for creating a new team message."""
    message: str


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    team_id: int
    sender_id: int
    sender_name: str
    sender_email: str
    message: str
    created_at: str
    updated_at: str


@router.get("/teams/{team_id}/messages")
async def get_team_messages(
    team_id: int,
    requester_id: str,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    """
    Get all messages for a team.

    Args:
        team_id: Team ID to get messages for
        requester_id: ID of the user requesting messages
        limit: Maximum number of messages to return (default: 100)
        offset: Number of messages to skip (default: 0)

    Returns:
        List of messages with sender information

    Raises:
        404: Team not found
        403: User is not a member of the team
    """
    try:
        # Verify team exists
        team = supabase.table("teams").select("*").eq("id", team_id).execute()

        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Verify requester is a team member
        membership = supabase.table("team_members").select("*").eq(
            "team_id", team_id
        ).eq("user_id", requester_id).execute()

        if not membership.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )

        # Get messages
        query = supabase.table("team_messages").select("*").eq("team_id", team_id)
        query = query.order("created_at", desc=False).limit(limit).offset(offset)
        result = query.execute()

        # Enrich messages with sender information
        messages = []
        for msg in result.data:
            # Get sender details
            sender = supabase.table("users").select(
                "id, name, email"
            ).eq("id", msg["sender_id"]).execute()

            if sender.data:
                sender_info = sender.data[0]
                messages.append({
                    "id": msg["id"],
                    "team_id": msg["team_id"],
                    "sender_id": msg["sender_id"],
                    "sender_name": sender_info["name"],
                    "sender_email": sender_info["email"],
                    "message": msg["message"],
                    "created_at": msg["created_at"],
                    "updated_at": msg["updated_at"]
                })

        return {
            "messages": messages,
            "count": len(messages),
            "team_id": team_id,
            "team_name": team.data[0]["name"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        ) from e


@router.post("/teams/{team_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_team_message(
    team_id: int,
    message_data: MessageCreate,
    sender_id: int
):
    """
    Send a message to a team.

    Args:
        team_id: Team ID to send message to
        message_data: Message content
        sender_id: ID of the user sending the message

    Returns:
        Created message with sender information

    Raises:
        404: Team not found
        403: User is not a member of the team
        400: Message is empty
    """
    try:
        # Validate message content
        if not message_data.message or not message_data.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Verify team exists
        team = supabase.table("teams").select("*").eq("id", team_id).execute()

        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Verify sender is a team member
        membership = supabase.table("team_members").select("*").eq(
            "team_id", team_id
        ).eq("user_id", sender_id).execute()

        if not membership.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )

        # Create message
        new_message = {
            "team_id": team_id,
            "sender_id": sender_id,
            "message": message_data.message.strip()
        }

        result = supabase.table("team_messages").insert(new_message).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message"
            )

        created_message = result.data[0]

        # Get sender details
        sender = supabase.table("users").select(
            "id, name, email"
        ).eq("id", sender_id).execute()

        sender_info = sender.data[0] if sender.data else {}

        return {
            "message": {
                "id": created_message["id"],
                "team_id": created_message["team_id"],
                "sender_id": created_message["sender_id"],
                "sender_name": sender_info.get("name", "Unknown"),
                "sender_email": sender_info.get("email", ""),
                "message": created_message["message"],
                "created_at": created_message["created_at"],
                "updated_at": created_message["updated_at"]
            },
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        ) from e


@router.delete("/messages/{message_id}")
async def delete_message(message_id: int, requester_id: str):
    """
    Delete a message.

    Args:
        message_id: ID of the message to delete
        requester_id: ID of the user requesting deletion

    Returns:
        Success message

    Raises:
        404: Message not found
        403: User is not the message sender
    """
    try:
        # Get message
        message = supabase.table("team_messages").select("*").eq(
            "id", message_id
        ).execute()

        if not message.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        msg = message.data[0]

        # Verify requester is the sender
        if msg["sender_id"] != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own messages"
            )

        # Delete message
        supabase.table("team_messages").delete().eq("id", message_id).execute()

        return {
            "success": True,
            "message": f"Message {message_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {str(e)}"
        ) from e


@router.get("/teams/{team_id}/members")
async def get_team_members(team_id: int, requester_id: str):
    """
    Get all members of a team (for chat participants list).

    Args:
        team_id: Team ID to get members for
        requester_id: ID of the user requesting member list

    Returns:
        List of team members

    Raises:
        404: Team not found
        403: User is not a member of the team
    """
    try:
        # Verify team exists
        team = supabase.table("teams").select("*").eq("id", team_id).execute()

        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Verify requester is a team member
        membership = supabase.table("team_members").select("*").eq(
            "team_id", team_id
        ).eq("user_id", requester_id).execute()

        if not membership.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )

        # Get all team members
        members_data = supabase.table("team_members").select("*").eq(
            "team_id", team_id
        ).execute()

        members = []
        if members_data.data:
            for member in members_data.data:
                user = supabase.table("users").select(
                    "id, name, email, role"
                ).eq("id", member["user_id"]).execute()

                if user.data:
                    members.append(user.data[0])

        return {
            "members": members,
            "count": len(members),
            "team_id": team_id,
            "team_name": team.data[0]["name"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team members: {str(e)}"
        ) from e
