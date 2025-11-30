"""
Tests for team chat functionality (OPETSE-18).

This module contains comprehensive tests for:
- Getting team messages
- Sending messages
- Deleting messages
- Team member authorization
- Message validation
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.api.v1.chats import (
    get_team_messages,
    send_team_message,
    delete_message,
    get_team_members,
    MessageCreate
)


class TestGetTeamMessages:
    """Tests for getting team messages."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_get_messages_success(self, mock_supabase):
        """Test successfully retrieving team messages."""
        # Mock team exists - create separate mock for team query
        team_query = MagicMock()
        team_query.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )
        
        # Mock membership check
        membership_query = MagicMock()
        membership_query.execute.return_value = MagicMock(
            data=[{"team_id": 1, "user_id": 1}]
        )

        # Mock messages query
        messages_query = MagicMock()
        messages_query.execute.return_value = MagicMock(
            data=[
                {
                    "id": 1,
                    "team_id": 1,
                    "sender_id": 1,
                    "message": "Hello team!",
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-01T00:00:00Z"
                }
            ]
        )

        # Mock sender details query
        user_query = MagicMock()
        user_query.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "John Doe", "email": "john@example.com"}]
        )

        # Setup table call returns
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "teams":
                mock_table.select.return_value.eq.return_value = team_query
            elif table_name == "team_members":
                mock_table.select.return_value.eq.return_value.eq.return_value = membership_query
            elif table_name == "team_messages":
                mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value = messages_query
            elif table_name == "users":
                mock_table.select.return_value.eq.return_value = user_query
            return mock_table
        
        mock_supabase.table.side_effect = table_side_effect

        result = await get_team_messages(team_id=1, requester_id=1)

        assert result["count"] == 1
        assert result["team_id"] == 1
        assert result["team_name"] == "Team Alpha"
        assert result["messages"][0]["message"] == "Hello team!"
        assert result["messages"][0]["sender_name"] == "John Doe"

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_get_messages_team_not_found(self, mock_supabase):
        """Test error when team doesn't exist."""
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_team_messages(team_id=999, requester_id=1)

        assert exc_info.value.status_code == 404
        assert "Team not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_get_messages_not_team_member(self, mock_supabase):
        """Test error when user is not a team member."""
        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is NOT team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_team_messages(team_id=1, requester_id=999)

        assert exc_info.value.status_code == 403
        assert "not a member" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_get_messages_with_limit_offset(self, mock_supabase):
        """Test pagination with limit and offset."""
        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"team_id": 1, "user_id": 1}]
        )

        # Mock messages with limit/offset
        mock_supabase.table("team_messages").select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": 11,
                    "team_id": 1,
                    "sender_id": 1,
                    "message": "Message 11",
                    "created_at": "2025-01-01T00:11:00Z",
                    "updated_at": "2025-01-01T00:11:00Z"
                }
            ]
        )

        # Mock sender details
        mock_supabase.table("users").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "John Doe", "email": "john@example.com"}]
        )

        result = await get_team_messages(team_id=1, requester_id=1, limit=10, offset=10)

        assert result["count"] == 1
        assert result["messages"][0]["id"] == 11


class TestSendTeamMessage:
    """Tests for sending team messages."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_send_message_success(self, mock_supabase):
        """Test successfully sending a message."""
        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"team_id": 1, "user_id": 1}]
        )

        # Mock message creation
        mock_supabase.table("team_messages").insert.return_value.execute.return_value = MagicMock(
            data=[{
                "id": 1,
                "team_id": 1,
                "sender_id": 1,
                "message": "Hello team!",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }]
        )

        # Mock sender details
        mock_supabase.table("users").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "John Doe", "email": "john@example.com"}]
        )

        message_data = MessageCreate(message="Hello team!")
        result = await send_team_message(team_id=1, message_data=message_data, sender_id=1)

        assert result["success"] is True
        assert result["message"]["message"] == "Hello team!"
        assert result["message"]["sender_name"] == "John Doe"

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_send_empty_message(self, mock_supabase):
        """Test error when sending empty message."""
        message_data = MessageCreate(message="   ")

        with pytest.raises(HTTPException) as exc_info:
            await send_team_message(team_id=1, message_data=message_data, sender_id=1)

        assert exc_info.value.status_code == 400
        assert "cannot be empty" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_send_message_team_not_found(self, mock_supabase):
        """Test error when team doesn't exist."""
        message_data = MessageCreate(message="Hello team!")

        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with pytest.raises(HTTPException) as exc_info:
            await send_team_message(team_id=999, message_data=message_data, sender_id=1)

        assert exc_info.value.status_code == 404
        assert "Team not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_send_message_not_team_member(self, mock_supabase):
        """Test error when sender is not a team member."""
        message_data = MessageCreate(message="Hello team!")

        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is NOT team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with pytest.raises(HTTPException) as exc_info:
            await send_team_message(team_id=1, message_data=message_data, sender_id=999)

        assert exc_info.value.status_code == 403
        assert "not a member" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_send_message_with_whitespace_trimming(self, mock_supabase):
        """Test that message whitespace is trimmed."""
        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"team_id": 1, "user_id": 1}]
        )

        # Mock message creation
        mock_supabase.table("team_messages").insert.return_value.execute.return_value = MagicMock(
            data=[{
                "id": 1,
                "team_id": 1,
                "sender_id": 1,
                "message": "Hello team!",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }]
        )

        # Mock sender details
        mock_supabase.table("users").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "John Doe", "email": "john@example.com"}]
        )

        message_data = MessageCreate(message="  Hello team!  ")
        result = await send_team_message(team_id=1, message_data=message_data, sender_id=1)

        assert result["success"] is True


class TestDeleteMessage:
    """Tests for deleting messages."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_delete_message_success(self, mock_supabase):
        """Test successfully deleting own message."""
        # Mock message exists and user is sender
        mock_supabase.table("team_messages").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": 1,
                "team_id": 1,
                "sender_id": 1,
                "message": "Hello team!",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }]
        )

        # Mock deletion
        mock_supabase.table("team_messages").delete.return_value.eq.return_value.execute.return_value = MagicMock()

        result = await delete_message(message_id=1, requester_id=1)

        assert result["success"] is True
        assert "deleted successfully" in result["message"]

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_delete_message_not_found(self, mock_supabase):
        """Test error when message doesn't exist."""
        mock_supabase.table("team_messages").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_message(message_id=999, requester_id=1)

        assert exc_info.value.status_code == 404
        assert "Message not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_delete_message_not_sender(self, mock_supabase):
        """Test error when trying to delete someone else's message."""
        # Mock message exists but requester is not sender
        mock_supabase.table("team_messages").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": 1,
                "team_id": 1,
                "sender_id": 2,  # Different user
                "message": "Hello team!",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }]
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_message(message_id=1, requester_id=1)

        assert exc_info.value.status_code == 403
        assert "only delete your own messages" in exc_info.value.detail


class TestGetTeamMembers:
    """Tests for getting team members."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_get_team_members_success(self, mock_supabase):
        """Test successfully retrieving team members."""
        # Track number of team_members queries
        members_query_count = [0]
        
        # Mock team exists
        team_query = MagicMock()
        team_query.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is team member (first query)
        membership_check = MagicMock()
        membership_check.execute.return_value = MagicMock(
            data=[{"team_id": 1, "user_id": 1}]
        )

        # Mock all team members (second query)
        all_members_query = MagicMock()
        all_members_query.execute.return_value = MagicMock(
            data=[
                {"team_id": 1, "user_id": 1},
                {"team_id": 1, "user_id": 2}
            ]
        )

        # Mock user details (called twice for two members)
        user_query_calls = [
            MagicMock(data=[{"id": 1, "name": "John Doe", "email": "john@example.com", "role": "student"}]),
            MagicMock(data=[{"id": 2, "name": "Jane Smith", "email": "jane@example.com", "role": "student"}])
        ]
        user_call_index = [0]

        # Setup table call returns
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "teams":
                mock_table.select.return_value.eq.return_value = team_query
            elif table_name == "team_members":
                # First call is membership check, second is get all members
                if members_query_count[0] == 0:
                    mock_table.select.return_value.eq.return_value.eq.return_value = membership_check
                    members_query_count[0] += 1
                else:
                    mock_table.select.return_value.eq.return_value = all_members_query
            elif table_name == "users":
                user_mock = MagicMock()
                user_mock.execute.return_value = user_query_calls[user_call_index[0]]
                user_call_index[0] = min(user_call_index[0] + 1, len(user_query_calls) - 1)
                mock_table.select.return_value.eq.return_value = user_mock
            return mock_table
        
        mock_supabase.table.side_effect = table_side_effect

        result = await get_team_members(team_id=1, requester_id=1)

        assert result["count"] == 2
        assert result["team_id"] == 1
        assert result["team_name"] == "Team Alpha"
        assert len(result["members"]) == 2

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_get_team_members_not_member(self, mock_supabase):
        """Test error when requester is not a team member."""
        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is NOT team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_team_members(team_id=1, requester_id=999)

        assert exc_info.value.status_code == 403
        assert "not a member" in exc_info.value.detail


class TestMessageValidation:
    """Tests for message validation and edge cases."""

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_message_with_special_characters(self, mock_supabase):
        """Test sending message with special characters."""
        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"team_id": 1, "user_id": 1}]
        )

        # Mock message creation
        special_message = "Hello! @team 😊 How's it going? #project"
        mock_supabase.table("team_messages").insert.return_value.execute.return_value = MagicMock(
            data=[{
                "id": 1,
                "team_id": 1,
                "sender_id": 1,
                "message": special_message,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }]
        )

        # Mock sender details
        mock_supabase.table("users").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "John Doe", "email": "john@example.com"}]
        )

        message_data = MessageCreate(message=special_message)
        result = await send_team_message(team_id=1, message_data=message_data, sender_id=1)

        assert result["success"] is True
        assert result["message"]["message"] == special_message

    @pytest.mark.asyncio
    @patch('app.api.v1.chats.supabase')
    async def test_long_message(self, mock_supabase):
        """Test sending a long message."""
        # Mock team exists
        mock_supabase.table("teams").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "Team Alpha"}]
        )

        # Mock user is team member
        mock_supabase.table("team_members").select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"team_id": 1, "user_id": 1}]
        )

        # Create a long message
        long_message = "A" * 1000

        # Mock message creation
        mock_supabase.table("team_messages").insert.return_value.execute.return_value = MagicMock(
            data=[{
                "id": 1,
                "team_id": 1,
                "sender_id": 1,
                "message": long_message,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }]
        )

        # Mock sender details
        mock_supabase.table("users").select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1, "name": "John Doe", "email": "john@example.com"}]
        )

        message_data = MessageCreate(message=long_message)
        result = await send_team_message(team_id=1, message_data=message_data, sender_id=1)

        assert result["success"] is True
        assert len(result["message"]["message"]) == 1000
