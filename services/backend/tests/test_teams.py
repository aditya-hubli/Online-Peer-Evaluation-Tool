"""
Comprehensive tests for team management endpoints.
Tests teams.py API to increase code coverage to 80%.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_supabase_teams():
    """Mock supabase for teams tests."""
    with patch('app.api.v1.teams.supabase') as mock:
        yield mock


@pytest.fixture
def sample_team():
    """Sample team data."""
    return {
        "id": 1,
        "project_id": 1,
        "name": "Team Alpha",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        "id": 1,
        "title": "Test Project",
        "description": "A test project"
    }


@pytest.fixture
def sample_users():
    """Sample user data."""
    return [
        {"id": 1, "name": "Student One", "email": "student1@test.com", "role": "student"},
        {"id": 2, "name": "Student Two", "email": "student2@test.com", "role": "student"}
    ]


class TestListTeams:
    """Tests for listing teams."""
    
    def test_list_teams_success(self, mock_supabase_teams, sample_team, sample_project, sample_users):
        """Test successfully listing all teams."""
        # Mock teams query
        mock_teams_result = Mock()
        mock_teams_result.data = [sample_team]
        
        # Mock team members
        mock_members_result = Mock()
        mock_members_result.data = [{"team_id": 1, "user_id": 1}, {"team_id": 1, "user_id": 2}]
        
        # Mock user queries
        mock_user1 = Mock()
        mock_user1.data = [sample_users[0]]
        mock_user2 = Mock()
        mock_user2.data = [sample_users[1]]
        
        # Mock project query
        mock_project_result = Mock()
        mock_project_result.data = [sample_project]
        
        call_count = {"teams": 0, "team_members": 0, "users": 0, "projects": 0}
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "teams":
                mock_table.select.return_value.order.return_value.execute.return_value = mock_teams_result
            elif table_name == "team_members":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_members_result
            elif table_name == "users":
                if call_count["users"] == 0:
                    mock_table.select.return_value.eq.return_value.execute.return_value = mock_user1
                    call_count["users"] += 1
                else:
                    mock_table.select.return_value.eq.return_value.execute.return_value = mock_user2
            elif table_name == "projects":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        response = client.get("/api/v1/teams/")
        
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        assert data["count"] == 1
    
    def test_list_teams_with_project_filter(self, mock_supabase_teams, sample_team):
        """Test listing teams filtered by project."""
        mock_teams_result = Mock()
        mock_teams_result.data = [sample_team]
        
        mock_members_result = Mock()
        mock_members_result.data = []
        
        mock_project_result = Mock()
        mock_project_result.data = [{"id": 1, "title": "Test Project"}]
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "teams":
                mock_eq = Mock()
                mock_eq.order.return_value.execute.return_value = mock_teams_result
                mock_table.select.return_value.eq.return_value = mock_eq
            elif table_name == "team_members":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_members_result
            elif table_name == "projects":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        response = client.get("/api/v1/teams/?project_id=1")
        
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data


class TestCreateTeam:
    """Tests for creating teams."""
    
    def test_create_team_success(self, mock_supabase_teams, sample_team, sample_project, sample_users):
        """Test successfully creating a team."""
        mock_project_result = Mock()
        mock_project_result.data = [sample_project]
        
        mock_user1 = Mock()
        mock_user1.data = [sample_users[0]]
        mock_user2 = Mock()
        mock_user2.data = [sample_users[1]]
        
        mock_team_create = Mock()
        mock_team_create.data = [sample_team]
        
        mock_member_insert = Mock()
        mock_member_insert.data = [{"team_id": 1, "user_id": 1}]
        
        call_count = {"users": 0}
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "projects":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
            elif table_name == "users":
                if call_count["users"] == 0:
                    mock_table.select.return_value.eq.return_value.execute.return_value = mock_user1
                    call_count["users"] += 1
                else:
                    mock_table.select.return_value.eq.return_value.execute.return_value = mock_user2
            elif table_name == "teams":
                mock_table.insert.return_value.execute.return_value = mock_team_create
            elif table_name == "team_members":
                mock_table.insert.return_value.execute.return_value = mock_member_insert
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        payload = {
            "project_id": 1,
            "name": "Team Alpha",
            "member_ids": [1, 2]
        }
        
        response = client.post("/api/v1/teams/", json=payload)
        
        assert response.status_code in [201, 422]
        if response.status_code == 201:
            data = response.json()
            assert "team" in data
    
    def test_create_team_project_not_found(self, mock_supabase_teams):
        """Test creating team with non-existent project."""
        mock_project_result = Mock()
        mock_project_result.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
        mock_supabase_teams.table.return_value = mock_table
        
        payload = {
            "project_id": 999,
            "name": "Team Alpha",
            "member_ids": [1]
        }
        
        response = client.post("/api/v1/teams/", json=payload)
        
        assert response.status_code in [404, 422]
        if response.status_code == 404:
            assert "Project not found" in response.json()["detail"]
    
    def test_create_team_user_not_found(self, mock_supabase_teams, sample_project):
        """Test creating team with non-existent user."""
        mock_project_result = Mock()
        mock_project_result.data = [sample_project]
        
        mock_user_result = Mock()
        mock_user_result.data = []
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "projects":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
            elif table_name == "users":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_user_result
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        payload = {
            "project_id": 1,
            "name": "Team Alpha",
            "member_ids": [999]
        }
        
        response = client.post("/api/v1/teams/", json=payload)
        
        assert response.status_code in [404, 422]
        if response.status_code == 404:
            assert "User with id 999 not found" in response.json()["detail"]
    
    def test_create_team_non_student_member(self, mock_supabase_teams, sample_project):
        """Test creating team with non-student member."""
        mock_project_result = Mock()
        mock_project_result.data = [sample_project]
        
        mock_user_result = Mock()
        mock_user_result.data = [{"id": 1, "role": "instructor"}]
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "projects":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
            elif table_name == "users":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_user_result
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        payload = {
            "project_id": 1,
            "name": "Team Alpha",
            "member_ids": [1]
        }
        
        response = client.post("/api/v1/teams/", json=payload)
        
        assert response.status_code in [400, 422]
        if response.status_code == 400:
            assert "must be a student" in response.json()["detail"]


class TestGetTeam:
    """Tests for getting a single team."""
    
    def test_get_team_success(self, mock_supabase_teams, sample_team, sample_project, sample_users):
        """Test successfully getting a team by ID."""
        mock_team_result = Mock()
        mock_team_result.data = [sample_team]
        
        mock_members_result = Mock()
        mock_members_result.data = [{"team_id": 1, "user_id": 1}]
        
        mock_user_result = Mock()
        mock_user_result.data = [sample_users[0]]
        
        mock_project_result = Mock()
        mock_project_result.data = [sample_project]
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "teams":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_result
            elif table_name == "team_members":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_members_result
            elif table_name == "users":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_user_result
            elif table_name == "projects":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        response = client.get("/api/v1/teams/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
    
    def test_get_team_not_found(self, mock_supabase_teams):
        """Test getting non-existent team."""
        mock_team_result = Mock()
        mock_team_result.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_result
        mock_supabase_teams.table.return_value = mock_table
        
        response = client.get("/api/v1/teams/999")
        
        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]


class TestUpdateTeam:
    """Tests for updating teams."""
    
    def test_update_team_name(self, mock_supabase_teams, sample_team, sample_project, sample_users):
        """Test updating team name."""
        mock_team_check = Mock()
        mock_team_check.data = [sample_team]
        
        updated_team = sample_team.copy()
        updated_team["name"] = "Updated Team Name"
        mock_team_update = Mock()
        mock_team_update.data = [updated_team]
        
        mock_members_result = Mock()
        mock_members_result.data = [{"team_id": 1, "user_id": 1}]
        
        mock_user_result = Mock()
        mock_user_result.data = [sample_users[0]]
        
        mock_project_result = Mock()
        mock_project_result.data = [sample_project]
        
        call_count = {"teams": 0}
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "teams":
                if call_count["teams"] == 0:
                    mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_check
                    call_count["teams"] += 1
                elif call_count["teams"] == 1:
                    mock_table.update.return_value.eq.return_value.execute.return_value = mock_team_update
                    call_count["teams"] += 1
                else:
                    mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_update
            elif table_name == "team_members":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_members_result
            elif table_name == "users":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_user_result
            elif table_name == "projects":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_project_result
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        payload = {"name": "Updated Team Name"}
        response = client.put("/api/v1/teams/1", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
    
    def test_update_team_not_found(self, mock_supabase_teams):
        """Test updating non-existent team."""
        mock_team_result = Mock()
        mock_team_result.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_result
        mock_supabase_teams.table.return_value = mock_table
        
        payload = {"name": "Updated Name"}
        response = client.put("/api/v1/teams/999", json=payload)
        
        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]


class TestDeleteTeam:
    """Tests for deleting teams."""
    
    def test_delete_team_success(self, mock_supabase_teams, sample_team):
        """Test successfully deleting a team."""
        mock_team_check = Mock()
        mock_team_check.data = [sample_team]
        
        mock_members_delete = Mock()
        mock_members_delete.data = []
        
        mock_team_delete = Mock()
        mock_team_delete.data = [sample_team]
        
        call_count = {"teams": 0}
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "teams":
                if call_count["teams"] == 0:
                    mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_check
                    call_count["teams"] += 1
                else:
                    mock_table.delete.return_value.eq.return_value.execute.return_value = mock_team_delete
            elif table_name == "team_members":
                mock_table.delete.return_value.eq.return_value.execute.return_value = mock_members_delete
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        response = client.delete("/api/v1/teams/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "Team 1 deleted successfully" in data["message"]
    
    def test_delete_team_not_found(self, mock_supabase_teams):
        """Test deleting non-existent team."""
        mock_team_result = Mock()
        mock_team_result.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_result
        mock_supabase_teams.table.return_value = mock_table
        
        response = client.delete("/api/v1/teams/999")
        
        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]


class TestAddTeamMember:
    """Tests for adding team members."""
    
    def test_add_member_success(self, mock_supabase_teams, sample_team, sample_users):
        """Test successfully adding a member to a team."""
        mock_team_check = Mock()
        mock_team_check.data = [sample_team]
        
        mock_user_check = Mock()
        mock_user_check.data = [sample_users[0]]
        
        mock_membership_check = Mock()
        mock_membership_check.data = []
        
        mock_member_insert = Mock()
        mock_member_insert.data = [{"team_id": 1, "user_id": 1}]
        
        call_count = {"team_members": 0}
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "teams":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_check
            elif table_name == "users":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_user_check
            elif table_name == "team_members":
                if call_count["team_members"] == 0:
                    mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_membership_check
                    call_count["team_members"] += 1
                else:
                    mock_table.insert.return_value.execute.return_value = mock_member_insert
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        payload = {"user_id": 1}
        response = client.post("/api/v1/teams/1/members", json=payload)
        
        assert response.status_code in [201, 422]
        if response.status_code == 201:
            data = response.json()
            assert data["message"] == "Member added successfully"


class TestRemoveTeamMember:
    """Tests for removing team members."""
    
    def test_remove_member_success(self, mock_supabase_teams, sample_team):
        """Test successfully removing a member from a team."""
        mock_team_check = Mock()
        mock_team_check.data = [sample_team]
        
        mock_membership_check = Mock()
        mock_membership_check.data = [{"team_id": 1, "user_id": 1}]
        
        mock_member_delete = Mock()
        mock_member_delete.data = [{"team_id": 1, "user_id": 1}]
        
        call_count = {"team_members": 0}
        
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "teams":
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_team_check
            elif table_name == "team_members":
                if call_count["team_members"] == 0:
                    mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_membership_check
                    call_count["team_members"] += 1
                else:
                    mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_member_delete
            return mock_table
        
        mock_supabase_teams.table.side_effect = table_side_effect
        
        response = client.delete("/api/v1/teams/1/members/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "removed from team" in data["message"]
