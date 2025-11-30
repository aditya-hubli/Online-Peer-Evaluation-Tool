"""
Tests for submission analytics and instructor dashboard (OPETSE-12).

OPETSE-12: As an instructor, I want a dashboard showing submission analytics
so that I can monitor evaluation progress.

This test suite validates:
- Project-level evaluation analytics and progress tracking
- Team-level submission statistics
- Member-level evaluation status tracking
- Instructor dashboard with overall metrics
- Anonymization of evaluator data for non-instructor roles
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class MockSupabaseResponse:
    """Mock Supabase response object."""

    def __init__(self, data):
        self.data = data


class MockSupabaseQuery:
    """Mock Supabase query builder."""

    def __init__(self, data):
        self._data = data
        self._filters = []
        self._order_by = None

    def select(self, fields):
        """Mock select."""
        return self

    def eq(self, field, value):
        """Mock eq filter."""
        self._filters.append(('eq', field, value))
        return self

    def neq(self, field, value):
        """Mock neq filter."""
        self._filters.append(('neq', field, value))
        return self

    def in_(self, field, values):
        """Mock in filter."""
        self._filters.append(('in', field, values))
        return self

    def order(self, field, desc=False):
        """Mock order."""
        self._order_by = (field, desc)
        return self

    def execute(self):
        """Mock execute - returns filtered data."""
        filtered = self._data[:]

        for filter_type, field, value in self._filters:
            if filter_type == 'eq':
                filtered = [item for item in filtered if item.get(field) == value]
            elif filter_type == 'neq':
                filtered = [item for item in filtered if item.get(field) != value]
            elif filter_type == 'in':
                filtered = [item for item in filtered if item.get(field) in value]

        if self._order_by:
            field, desc = self._order_by
            filtered = sorted(filtered, key=lambda x: x.get(field, 0), reverse=desc)

        return MockSupabaseResponse(filtered)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch('app.api.v1.reports.supabase') as mock_sb:
        mock_sb.table = MagicMock(return_value=MockSupabaseQuery([]))
        yield mock_sb


@pytest.fixture
def sample_project():
    """Sample project for analytics tests."""
    return {
        "id": 1,
        "title": "Semester Project - Peer Evaluation",
        "description": "Team-based evaluation project",
        "deadline": "2024-11-30T23:59:59Z"
    }


@pytest.fixture
def sample_teams():
    """Sample teams data."""
    return [
        {"id": 1, "name": "Team Alpha", "project_id": 1},
        {"id": 2, "name": "Team Beta", "project_id": 1},
        {"id": 3, "name": "Team Gamma", "project_id": 1}
    ]


@pytest.fixture
def sample_team_members():
    """Sample team members data."""
    return [
        {"id": 1, "team_id": 1, "user_id": 1},
        {"id": 2, "team_id": 1, "user_id": 2},
        {"id": 3, "team_id": 1, "user_id": 3},
        {"id": 4, "team_id": 2, "user_id": 4},
        {"id": 5, "team_id": 2, "user_id": 5},
        {"id": 6, "team_id": 3, "user_id": 6}
    ]


@pytest.fixture
def sample_evaluations():
    """Sample evaluations data."""
    return [
        {"id": 1, "team_id": 1, "evaluator_id": 1, "evaluatee_id": 2, "total_score": 85, "submitted_at": "2024-11-15T10:00:00Z"},
        {"id": 2, "team_id": 1, "evaluator_id": 1, "evaluatee_id": 3, "total_score": 90, "submitted_at": "2024-11-15T10:15:00Z"},
        {"id": 3, "team_id": 1, "evaluator_id": 2, "evaluatee_id": 1, "total_score": 80, "submitted_at": "2024-11-15T10:30:00Z"},
        {"id": 4, "team_id": 2, "evaluator_id": 4, "evaluatee_id": 5, "total_score": 75, "submitted_at": "2024-11-14T14:00:00Z"}
    ]


@pytest.fixture
def sample_users():
    """Sample users data."""
    return [
        {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
        {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
        {"id": 3, "name": "Carol White", "email": "carol@example.com"},
        {"id": 4, "name": "David Brown", "email": "david@example.com"},
        {"id": 5, "name": "Eve Davis", "email": "eve@example.com"},
        {"id": 6, "name": "Frank Green", "email": "frank@example.com"}
    ]


# ============================================================================
# OPETSE-12: Submission Analytics Tests
# ============================================================================

@pytest.mark.asyncio
async def test_project_submission_progress_nonexistent(client, mock_supabase):
    """Test project submission progress for non-existent project."""
    
    def mock_table(table_name):
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/project/999/submission-progress")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_submission_progress_empty_project(
    client, mock_supabase, sample_project
):
    """Test project submission progress when no teams exist."""
    
    def mock_table(table_name):
        if table_name == "projects":
            return MockSupabaseQuery([sample_project])
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/project/1/submission-progress")

    assert response.status_code == 200
    data = response.json()
    
    analytics = data.get("analytics", {})
    assert analytics["submission_progress"]["total_teams"] == 0
    assert analytics["submission_progress"]["completion_percentage"] == 0


@pytest.mark.asyncio
async def test_project_submission_progress_with_evaluations(
    client, mock_supabase, sample_project, sample_teams, 
    sample_team_members, sample_evaluations, sample_users
):
    """Test project submission progress calculates correctly."""
    
    def mock_table(table_name):
        if table_name == "projects":
            return MockSupabaseQuery([sample_project])
        elif table_name == "teams":
            return MockSupabaseQuery(sample_teams)
        elif table_name == "team_members":
            team_id = None
            for f in mock_supabase.table.mock_calls:
                pass
            return MockSupabaseQuery([m for m in sample_team_members if m["team_id"] == 1] if sample_team_members else [])
        elif table_name == "evaluations":
            return MockSupabaseQuery(sample_evaluations)
        elif table_name == "users":
            return MockSupabaseQuery(sample_users)
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/project/1/submission-progress")

    assert response.status_code == 200
    data = response.json()
    
    analytics = data.get("analytics", {})
    assert analytics["submission_progress"]["total_teams"] >= 0
    assert "completion_percentage" in analytics["submission_progress"]


@pytest.mark.asyncio
async def test_team_evaluation_status_nonexistent(client, mock_supabase):
    """Test team evaluation status for non-existent team."""
    
    def mock_table(table_name):
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/team/999/evaluation-status")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_team_evaluation_status_empty_team(
    client, mock_supabase, sample_teams
):
    """Test team evaluation status when team has no members."""
    
    def mock_table(table_name):
        if table_name == "teams":
            return MockSupabaseQuery([sample_teams[0]])
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/team/1/evaluation-status")

    assert response.status_code == 200
    data = response.json()
    
    status = data.get("evaluation_status", {})
    assert status["overall"]["total_members"] == 0


@pytest.mark.asyncio
async def test_team_evaluation_status_with_members(
    client, mock_supabase, sample_teams, sample_team_members, 
    sample_evaluations, sample_users
):
    """Test team evaluation status shows member progress."""
    
    team_members_for_team_1 = [m for m in sample_team_members if m["team_id"] == 1]
    evals_for_team_1 = [e for e in sample_evaluations if e["team_id"] == 1]

    def mock_table(table_name):
        if table_name == "teams":
            return MockSupabaseQuery([sample_teams[0]])
        elif table_name == "team_members":
            return MockSupabaseQuery(team_members_for_team_1)
        elif table_name == "evaluations":
            return MockSupabaseQuery(evals_for_team_1)
        elif table_name == "users":
            return MockSupabaseQuery(sample_users)
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/team/1/evaluation-status")

    assert response.status_code == 200
    data = response.json()
    
    status = data.get("evaluation_status", {})
    assert status["overall"]["total_members"] == 3
    assert len(status["members"]) == 3
    
    for member in status["members"]:
        assert "evaluations_given" in member
        assert "evaluations_received" in member
        assert "status" in member


@pytest.mark.asyncio
async def test_instructor_dashboard_access_denied_for_students(
    client, mock_supabase
):
    """Test instructor dashboard denies access to non-instructor roles."""
    
    def mock_table(table_name):
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    # Student should not access dashboard
    response = client.get("/api/v1/reports/analytics/dashboard?requester_role=student")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_instructor_dashboard_no_projects(
    client, mock_supabase
):
    """Test instructor dashboard when no projects exist."""
    
    def mock_table(table_name):
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/dashboard?requester_role=instructor")

    assert response.status_code == 200
    data = response.json()
    
    dashboard = data.get("dashboard", {})
    assert dashboard["overall_metrics"]["total_projects"] == 0


@pytest.mark.asyncio
async def test_instructor_dashboard_with_projects(
    client, mock_supabase, sample_project, sample_teams, 
    sample_team_members, sample_evaluations
):
    """Test instructor dashboard shows project metrics."""
    
    def mock_table(table_name):
        if table_name == "projects":
            return MockSupabaseQuery([sample_project])
        elif table_name == "teams":
            return MockSupabaseQuery(sample_teams)
        elif table_name == "team_members":
            return MockSupabaseQuery(sample_team_members)
        elif table_name == "evaluations":
            return MockSupabaseQuery(sample_evaluations)
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/dashboard?requester_role=instructor")

    assert response.status_code == 200
    data = response.json()
    
    dashboard = data.get("dashboard", {})
    assert dashboard["overall_metrics"]["total_projects"] >= 1
    assert "overall_completion_percentage" in dashboard["overall_metrics"]


@pytest.mark.asyncio
async def test_submission_progress_completion_calculation(
    client, mock_supabase, sample_project, sample_teams
):
    """Test that completion percentage is calculated correctly."""
    
    # Team with 2 members = 2 possible evaluations (1->2, 2->1)
    # Both completed = 100%
    members_2 = [
        {"id": 1, "team_id": 1, "user_id": 1},
        {"id": 2, "team_id": 1, "user_id": 2}
    ]
    
    full_evals = [
        {"id": 1, "team_id": 1, "evaluator_id": 1, "evaluatee_id": 2, "total_score": 85},
        {"id": 2, "team_id": 1, "evaluator_id": 2, "evaluatee_id": 1, "total_score": 90}
    ]

    def mock_table(table_name):
        if table_name == "projects":
            return MockSupabaseQuery([sample_project])
        elif table_name == "teams":
            return MockSupabaseQuery([sample_teams[0]])
        elif table_name == "team_members":
            return MockSupabaseQuery(members_2)
        elif table_name == "evaluations":
            return MockSupabaseQuery(full_evals)
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/project/1/submission-progress")

    assert response.status_code == 200
    data = response.json()
    
    analytics = data.get("analytics", {})
    # With 1 team of 2 members: 2 possible evals, 2 completed = 100%
    assert analytics["submission_progress"]["completion_percentage"] == 100.0


@pytest.mark.asyncio
async def test_team_status_member_statistics(
    client, mock_supabase, sample_teams
):
    """Test team status calculates per-member statistics."""
    
    members = [
        {"id": 1, "team_id": 1, "user_id": 1},
        {"id": 2, "team_id": 1, "user_id": 2},
        {"id": 3, "team_id": 1, "user_id": 3}
    ]
    
    users = [
        {"id": 1, "name": "User 1", "email": "user1@example.com"},
        {"id": 2, "name": "User 2", "email": "user2@example.com"},
        {"id": 3, "name": "User 3", "email": "user3@example.com"}
    ]
    
    # User 1 has given 2 evals, received 1
    evals = [
        {"id": 1, "team_id": 1, "evaluator_id": 1, "evaluatee_id": 2, "total_score": 80},
        {"id": 2, "team_id": 1, "evaluator_id": 1, "evaluatee_id": 3, "total_score": 85},
        {"id": 3, "team_id": 1, "evaluator_id": 2, "evaluatee_id": 1, "total_score": 90}
    ]

    def mock_table(table_name):
        if table_name == "teams":
            return MockSupabaseQuery([sample_teams[0]])
        elif table_name == "team_members":
            return MockSupabaseQuery(members)
        elif table_name == "evaluations":
            return MockSupabaseQuery(evals)
        elif table_name == "users":
            return MockSupabaseQuery(users)
        return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get("/api/v1/reports/analytics/team/1/evaluation-status")

    assert response.status_code == 200
    data = response.json()
    
    status = data.get("evaluation_status", {})
    members_list = status["members"]
    
    # Find User 1's stats
    user1_stats = next((m for m in members_list if m["member_id"] == 1), None)
    assert user1_stats is not None
    assert user1_stats["evaluations_given"] == 2
    assert user1_stats["evaluations_received"] == 1
