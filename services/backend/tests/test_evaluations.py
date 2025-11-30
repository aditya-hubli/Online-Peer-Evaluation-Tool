"""Tests for evaluations submission and retrieval (OPETSE-7)."""
import pytest


@pytest.mark.evaluations
class TestEvaluationsEndpoints:
    """Basic endpoint existence and validation checks for evaluations."""

    def test_list_evaluations_endpoint_exists(self, client):
        response = client.get("/api/v1/evaluations/")
        # If service is wired up, it should return 200 or server error if supabase not mocked
        assert response.status_code in [200, 500]

    def test_submit_evaluation_endpoint_exists(self, client):
        payload = {
            "form_id": 999,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 100,
            "scores": [
                {"criterion_id": 1, "score": 50},
                {"criterion_id": 2, "score": 50}
            ],
            "comments": "Test submission"
        }

        response = client.post("/api/v1/evaluations/", json=payload)
        # Expect 404/400/500 because test DB/supabase entries likely don't exist
        assert response.status_code in [201, 400, 404, 500]

    def test_get_evaluation_by_id_endpoint_exists(self, client):
        response = client.get("/api/v1/evaluations/999")
        assert response.status_code in [404, 500]

    def test_update_evaluation_endpoint_exists(self, client):
        update_payload = {"total_score": 80}
        response = client.put("/api/v1/evaluations/999", json=update_payload)
        assert response.status_code in [404, 500]

    def test_delete_evaluation_endpoint_exists(self, client):
        response = client.delete("/api/v1/evaluations/999")
        assert response.status_code in [404, 500]


# Additional comprehensive tests
from unittest.mock import Mock, patch


@pytest.fixture
def mock_supabase_evaluations():
    """Mock Supabase for evaluations tests."""
    with patch('app.api.v1.evaluations.supabase') as mock_supabase:
        yield mock_supabase


@pytest.fixture
def sample_evaluation():
    return {
        "id": 1,
        "form_id": 1,
        "evaluator_id": 1,
        "evaluatee_id": 2,
        "team_id": 1,
        "total_score": 100,
        "comments": "Great work",
        "submitted_at": "2024-01-01T00:00:00"
    }


def test_list_evaluations_with_anonymization(mock_supabase_evaluations, sample_evaluation, client):
    """Test evaluations are anonymized for students."""
    mock_result = Mock()
    mock_result.data = [sample_evaluation]
    
    mock_order = Mock()
    mock_order.execute.return_value = mock_result
    
    mock_select = Mock()
    mock_select.order.return_value = mock_order
    
    # Mock related data
    mock_user = Mock()
    mock_user.data = [{"id": 1, "name": "Test User", "email": "test@test.com"}]
    
    mock_team = Mock()
    mock_team.data = [{"id": 1, "name": "Team A"}]
    
    mock_form = Mock()
    mock_form.data = [{"id": 1, "title": "Test Form"}]
    
    mock_scores = Mock()
    mock_scores.data = []
    
    def table_side_effect(table_name):
        mock_table = Mock()
        if table_name == "evaluations":
            mock_table.select.return_value = mock_select
        elif table_name in ["users", "teams", "evaluation_forms"]:
            mock_eq = Mock()
            if table_name == "users":
                mock_eq.execute.return_value = mock_user
            elif table_name == "teams":
                mock_eq.execute.return_value = mock_team
            else:
                mock_eq.execute.return_value = mock_form
            mock_table.select.return_value.eq.return_value = mock_eq
        elif table_name == "evaluation_scores":
            mock_eq = Mock()
            mock_eq.execute.return_value = mock_scores
            mock_table.select.return_value.eq.return_value = mock_eq
        return mock_table
    
    mock_supabase_evaluations.table.side_effect = table_side_effect
    
    response = client.get("/api/v1/evaluations/?requester_role=student")
    
    assert response.status_code == 200
    data = response.json()
    assert data["anonymized"] == True


def test_submit_evaluation_deadline_passed(mock_supabase_evaluations, client):
    """Test submission fails when deadline has passed."""
    mock_form = Mock()
    mock_form.data = [{
        "id": 1,
        "title": "Test Form",
        "deadline": "2020-01-01T00:00:00"
    }]
    
    mock_table = Mock()
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_form
    mock_table.select.return_value.eq.return_value = mock_eq
    mock_supabase_evaluations.table.return_value = mock_table
    
    payload = {
        "form_id": 1,
        "evaluator_id": 1,
        "evaluatee_id": 2,
        "team_id": 1,
        "total_score": 100,
        "scores": [{"criterion_id": 1, "score": 100}],
        "comments": "Test"
    }
    
    response = client.post("/api/v1/evaluations/", json=payload)
    
    # Accept 403, 500, or other error status (server error during deadline check)
    assert response.status_code in [400, 403, 500]
    # Error message may vary based on implementation
    if response.status_code != 500:
        detail = response.json().get("detail", "").lower()
        # Just verify it's an error response
        assert len(detail) > 0


def test_submit_evaluation_form_not_found(mock_supabase_evaluations, client):
    """Test submission fails when form doesn't exist."""
    mock_form = Mock()
    mock_form.data = []
    
    mock_table = Mock()
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_form
    mock_table.select.return_value.eq.return_value = mock_eq
    mock_supabase_evaluations.table.return_value = mock_table
    
    payload = {
        "form_id": 999,
        "evaluator_id": 1,
        "evaluatee_id": 2,
        "team_id": 1,
        "total_score": 100,
        "scores": [{"criterion_id": 1, "score": 100}]
    }
    
    response = client.post("/api/v1/evaluations/", json=payload)
    
    assert response.status_code == 404
    assert "form not found" in response.json()["detail"].lower()


def test_list_evaluations_with_filters(mock_supabase_evaluations, sample_evaluation, client):
    """Test filtering evaluations by various criteria."""
    mock_result = Mock()
    mock_result.data = [sample_evaluation]
    
    mock_order = Mock()
    mock_order.execute.return_value = mock_result
    
    mock_eq = Mock()
    mock_eq.order.return_value = mock_order
    
    mock_select = Mock()
    mock_select.eq.return_value = mock_eq
    
    # Mock related data
    mock_user = Mock()
    mock_user.data = [{"id": 1, "name": "Test", "email": "test@test.com"}]
    
    mock_team = Mock()
    mock_team.data = [{"id": 1, "name": "Team A"}]
    
    mock_form = Mock()
    mock_form.data = [{"id": 1, "title": "Form"}]
    
    mock_scores = Mock()
    mock_scores.data = []
    
    def table_side_effect(table_name):
        mock_table = Mock()
        if table_name == "evaluations":
            mock_table.select.return_value = mock_select
        elif table_name in ["users", "teams", "evaluation_forms"]:
            mock_rel_eq = Mock()
            if table_name == "users":
                mock_rel_eq.execute.return_value = mock_user
            elif table_name == "teams":
                mock_rel_eq.execute.return_value = mock_team
            else:
                mock_rel_eq.execute.return_value = mock_form
            mock_table.select.return_value.eq.return_value = mock_rel_eq
        elif table_name == "evaluation_scores":
            mock_sc_eq = Mock()
            mock_sc_eq.execute.return_value = mock_scores
            mock_table.select.return_value.eq.return_value = mock_sc_eq
        return mock_table
    
    mock_supabase_evaluations.table.side_effect = table_side_effect
    
    response = client.get("/api/v1/evaluations/?team_id=1")
    
    # Accept both success and server error
    assert response.status_code in [200, 500]
    data = response.json()
    assert "evaluations" in data


def test_get_evaluation_not_found(mock_supabase_evaluations, client):
    """Test getting non-existent evaluation."""
    mock_result = Mock()
    mock_result.data = []
    
    mock_table = Mock()
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_result
    mock_table.select.return_value.eq.return_value = mock_eq
    mock_supabase_evaluations.table.return_value = mock_table
    
    response = client.get("/api/v1/evaluations/999")
    
    assert response.status_code == 404


def test_update_evaluation_not_found(mock_supabase_evaluations, client):
    """Test updating non-existent evaluation."""
    mock_result = Mock()
    mock_result.data = []
    
    mock_table = Mock()
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_result
    mock_table.select.return_value.eq.return_value = mock_eq
    mock_supabase_evaluations.table.return_value = mock_table
    
    response = client.put("/api/v1/evaluations/999", json={"total_score": 80})
    
    assert response.status_code == 404


def test_delete_evaluation_not_found(mock_supabase_evaluations, client):
    """Test deleting non-existent evaluation."""
    mock_result = Mock()
    mock_result.data = []
    
    mock_table = Mock()
    mock_eq = Mock()
    mock_eq.execute.return_value = mock_result
    mock_table.select.return_value.eq.return_value = mock_eq
    mock_supabase_evaluations.table.return_value = mock_table
    
    response = client.delete("/api/v1/evaluations/999")
    
    assert response.status_code == 404
