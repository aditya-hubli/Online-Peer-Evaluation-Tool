"""
Tests for student dashboard functionality (OPETSE-13).

OPETSE-13: As a student, I want a dashboard showing my pending and completed evaluations.

This test suite validates:
- Retrieval of pending evaluations (teammates not yet evaluated)
- Retrieval of completed evaluations
- Correct counts and data enrichment
- Handling of students not in any team
- Filtering by active deadlines
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

    def order(self, field, **kwargs):
        """Mock order."""
        return self

    def execute(self):
        """Mock execute - returns filtered data."""
        filtered = self._data

        # Apply filters
        for filter_type, field, value in self._filters:
            if filter_type == 'eq':
                filtered = [item for item in filtered if item.get(field) == value]
            elif filter_type == 'neq':
                filtered = [item for item in filtered if item.get(field) != value]

        return MockSupabaseResponse(filtered)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch('app.api.v1.evaluations.supabase') as mock_sb:
        # Default empty responses
        mock_sb.table = MagicMock(return_value=MockSupabaseQuery([]))
        yield mock_sb


@pytest.mark.asyncio
async def test_student_not_in_any_team(client, mock_supabase):
    """Test dashboard when student is not a member of any team."""
    # Mock: student has no team memberships
    mock_supabase.table.return_value = MockSupabaseQuery([])

    response = client.get("/api/v1/evaluations/student/999")

    assert response.status_code == 200
    data = response.json()

    assert data["pending"] == []
    assert data["completed"] == []
    assert "not a member of any team" in data["message"].lower()


@pytest.mark.asyncio
async def test_student_with_no_evaluations(client, mock_supabase):
    """Test dashboard when student is in a team but has no evaluations."""
    student_id = 1
    team_id = 100

    def mock_table(table_name):
        if table_name == "team_members":
            return MockSupabaseQuery([{"team_id": team_id, "user_id": student_id}])
        elif table_name == "evaluations":
            return MockSupabaseQuery([])
        elif table_name == "teams":
            return MockSupabaseQuery([{"id": team_id, "name": "Team Alpha", "project_id": None}])
        else:
            return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get(f"/api/v1/evaluations/student/{student_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["pending"] == []
    assert data["completed"] == []
    assert data["pending_count"] == 0
    assert data["completed_count"] == 0


@pytest.mark.asyncio
async def test_student_with_completed_evaluations(client, mock_supabase):
    """Test dashboard shows completed evaluations correctly."""
    student_id = 1
    team_id = 100
    evaluatee_id = 2
    form_id = 50

    completed_eval = {
        "id": 1,
        "form_id": form_id,
        "evaluator_id": student_id,
        "evaluatee_id": evaluatee_id,
        "team_id": team_id,
        "total_score": 85,
        "submitted_at": "2025-11-10T10:00:00Z"
    }

    def mock_table(table_name):
        if table_name == "team_members":
            return MockSupabaseQuery([{"team_id": team_id, "user_id": student_id}])
        elif table_name == "evaluations":
            return MockSupabaseQuery([completed_eval])
        elif table_name == "users":
            return MockSupabaseQuery([{"id": evaluatee_id, "name": "Jane Doe", "email": "jane@test.com"}])
        elif table_name == "teams":
            return MockSupabaseQuery([{"id": team_id, "name": "Team Alpha"}])
        elif table_name == "evaluation_forms":
            return MockSupabaseQuery([{"id": form_id, "title": "Peer Review Form", "deadline": None}])
        else:
            return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    response = client.get(f"/api/v1/evaluations/student/{student_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["completed_count"] == 1
    assert len(data["completed"]) == 1
    assert data["completed"][0]["id"] == 1
    assert data["completed"][0]["total_score"] == 85
    assert data["completed"][0]["evaluatee"]["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_student_with_pending_evaluations(client, mock_supabase):
    """Test dashboard shows pending evaluations correctly."""
    student_id = 1
    team_id = 100
    teammate_id = 2
    project_id = 10
    form_id = 50

    def mock_table(table_name):
        if table_name == "team_members":
            # First call: get teams student is in
            # Second call: get teammates in that team
            call_count = getattr(mock_table, 'team_members_calls', 0)
            mock_table.team_members_calls = call_count + 1

            if call_count == 0:
                return MockSupabaseQuery([{"team_id": team_id, "user_id": student_id}])
            else:
                return MockSupabaseQuery([{"team_id": team_id, "user_id": teammate_id}])

        elif table_name == "teams":
            return MockSupabaseQuery([{
                "id": team_id,
                "name": "Team Alpha",
                "project_id": project_id
            }])

        elif table_name == "evaluation_forms":
            return MockSupabaseQuery([{
                "id": form_id,
                "title": "Peer Review Form",
                "deadline": "2025-12-31T23:59:59Z",
                "project_id": project_id
            }])

        elif table_name == "evaluations":
            # No existing evaluation
            return MockSupabaseQuery([])

        elif table_name == "users":
            return MockSupabaseQuery([{
                "id": teammate_id,
                "name": "Teammate Bob",
                "email": "bob@test.com"
            }])

        else:
            return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    # Mock deadline utility to return not passed
    with patch('app.api.v1.evaluations.is_deadline_passed', return_value=False):
        response = client.get(f"/api/v1/evaluations/student/{student_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["pending_count"] >= 1
    assert len(data["pending"]) >= 1

    pending = data["pending"][0]
    assert pending["form_id"] == form_id
    assert pending["form_title"] == "Peer Review Form"
    assert pending["team_id"] == team_id
    assert pending["team_name"] == "Team Alpha"
    assert pending["evaluatee_id"] == teammate_id
    assert pending["evaluatee"]["name"] == "Teammate Bob"


@pytest.mark.asyncio
async def test_student_excludes_past_deadline_pending(client, mock_supabase):
    """Test that pending evaluations with passed deadlines are excluded."""
    student_id = 1
    team_id = 100
    teammate_id = 2
    project_id = 10
    form_id = 50

    def mock_table(table_name):
        if table_name == "team_members":
            call_count = getattr(mock_table, 'team_members_calls', 0)
            mock_table.team_members_calls = call_count + 1

            if call_count == 0:
                return MockSupabaseQuery([{"team_id": team_id, "user_id": student_id}])
            else:
                return MockSupabaseQuery([{"team_id": team_id, "user_id": teammate_id}])

        elif table_name == "teams":
            return MockSupabaseQuery([{
                "id": team_id,
                "name": "Team Alpha",
                "project_id": project_id
            }])

        elif table_name == "evaluation_forms":
            return MockSupabaseQuery([{
                "id": form_id,
                "title": "Expired Form",
                "deadline": "2020-01-01T00:00:00Z",  # Past deadline
                "project_id": project_id
            }])

        elif table_name == "evaluations":
            return MockSupabaseQuery([])

        else:
            return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    # Mock deadline utility to return passed
    with patch('app.api.v1.evaluations.is_deadline_passed', return_value=True):
        response = client.get(f"/api/v1/evaluations/student/{student_id}")

    assert response.status_code == 200
    data = response.json()

    # Should have no pending evaluations because deadline passed
    assert data["pending_count"] == 0
    assert len(data["pending"]) == 0


@pytest.mark.asyncio
async def test_student_excludes_already_evaluated_teammates(client, mock_supabase):
    """Test that teammates already evaluated are not in pending list."""
    student_id = 1
    team_id = 100
    teammate_id = 2
    project_id = 10
    form_id = 50

    def mock_table(table_name):
        if table_name == "team_members":
            call_count = getattr(mock_table, 'team_members_calls', 0)
            mock_table.team_members_calls = call_count + 1

            if call_count == 0:
                return MockSupabaseQuery([{"team_id": team_id, "user_id": student_id}])
            else:
                return MockSupabaseQuery([{"team_id": team_id, "user_id": teammate_id}])

        elif table_name == "teams":
            return MockSupabaseQuery([{
                "id": team_id,
                "name": "Team Alpha",
                "project_id": project_id
            }])

        elif table_name == "evaluation_forms":
            return MockSupabaseQuery([{
                "id": form_id,
                "title": "Peer Review Form",
                "deadline": "2025-12-31T23:59:59Z",
                "project_id": project_id
            }])

        elif table_name == "evaluations":
            # Return existing evaluation
            return MockSupabaseQuery([{
                "id": 1,
                "form_id": form_id,
                "evaluator_id": student_id,
                "evaluatee_id": teammate_id
            }])

        else:
            return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    with patch('app.api.v1.evaluations.is_deadline_passed', return_value=False):
        response = client.get(f"/api/v1/evaluations/student/{student_id}")

    assert response.status_code == 200
    data = response.json()

    # Should have no pending because already evaluated
    assert data["pending_count"] == 0 or all(
        p["evaluatee_id"] != teammate_id for p in data["pending"]
    )


@pytest.mark.asyncio
async def test_student_multiple_teams_and_forms(client, mock_supabase):
    """Test student in multiple teams with multiple forms."""
    student_id = 1
    team1_id = 100
    team2_id = 101
    project1_id = 10
    project2_id = 11

    def mock_table(table_name):
        if table_name == "team_members":
            call_count = getattr(mock_table, 'team_members_calls', 0)
            mock_table.team_members_calls = call_count + 1

            if call_count == 0:
                # Student is in two teams
                return MockSupabaseQuery([
                    {"team_id": team1_id, "user_id": student_id},
                    {"team_id": team2_id, "user_id": student_id}
                ])
            else:
                # Teammates
                return MockSupabaseQuery([
                    {"team_id": team1_id, "user_id": 2},
                    {"team_id": team2_id, "user_id": 3}
                ])

        elif table_name == "teams":
            return MockSupabaseQuery([
                {"id": team1_id, "name": "Team 1", "project_id": project1_id},
                {"id": team2_id, "name": "Team 2", "project_id": project2_id}
            ])

        elif table_name == "evaluations":
            # Student has completed some
            return MockSupabaseQuery([
                {
                    "id": 1,
                    "team_id": team1_id,
                    "evaluator_id": student_id,
                    "evaluatee_id": 2,
                    "form_id": 50,
                    "total_score": 90
                }
            ])

        elif table_name == "evaluation_forms":
            return MockSupabaseQuery([
                {"id": 50, "title": "Form 1", "project_id": project1_id, "deadline": "2025-12-31"},
                {"id": 51, "title": "Form 2", "project_id": project2_id, "deadline": "2025-12-31"}
            ])

        elif table_name == "users":
            return MockSupabaseQuery([
                {"id": 2, "name": "User 2", "email": "u2@test.com"},
                {"id": 3, "name": "User 3", "email": "u3@test.com"}
            ])

        else:
            return MockSupabaseQuery([])

    mock_supabase.table.side_effect = mock_table

    with patch('app.api.v1.evaluations.is_deadline_passed', return_value=False):
        response = client.get(f"/api/v1/evaluations/student/{student_id}")

    assert response.status_code == 200
    data = response.json()

    # Should have at least 1 completed
    assert data["completed_count"] >= 1

    # Response should be well-formed
    assert "pending" in data
    assert "completed" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_dashboard_endpoint_error_handling(client, mock_supabase):
    """Test error handling in dashboard endpoint."""
    # Simulate a database error
    mock_supabase.table.side_effect = Exception("Database connection failed")

    response = client.get("/api/v1/evaluations/student/1")

    assert response.status_code == 500
    assert "Failed to retrieve student evaluations" in response.json()["detail"]
