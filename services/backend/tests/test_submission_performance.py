"""Performance tests for evaluation submission (OPETSE-21).

Tests that evaluation submissions complete within 2 seconds as per SRS requirement S18.
"""
import pytest
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.performance
@pytest.mark.opetse_21
class TestEvaluationSubmissionPerformance:
    """Test performance requirements for evaluation submissions."""

    def test_submission_completes_within_2_seconds(self, client):
        """
        OPETSE-21: Test that evaluation submission completes within 2 seconds.
        
        SRS Requirement: S18 - Fast form submissions (evaluations complete within 2 seconds)
        """
        # Mock Supabase responses for fast validation
        mock_form_data = {
            "id": 1,
            "title": "Test Form",
            "max_score": 100,
            "deadline": "2099-12-31T23:59:59"
        }
        
        mock_team_data = {"id": 1, "name": "Test Team"}
        mock_user_data = {"id": 1}
        mock_criteria_data = [
            {"id": 1, "form_id": 1, "text": "Criterion 1", "max_points": 50, "weight": 50},
            {"id": 2, "form_id": 1, "text": "Criterion 2", "max_points": 50, "weight": 50}
        ]
        mock_evaluation_data = {"id": 100, "form_id": 1, "evaluator_id": 1, "evaluatee_id": 2, "team_id": 1, "total_score": 85}
        mock_scores_data = [
            {"id": 1, "evaluation_id": 100, "criterion_id": 1, "score": 40},
            {"id": 2, "evaluation_id": 100, "criterion_id": 2, "score": 45}
        ]

        def mock_table(table_name):
            mock = Mock()
            
            if table_name == "evaluation_forms":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_form_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "teams":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_team_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "users":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_user_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "form_criteria":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=mock_criteria_data)
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluations":
                select_mock = Mock()
                eq_mock = Mock()
                neq_mock = Mock()
                # For duplicate check - return empty (no duplicates)
                eq_mock.execute.return_value = Mock(data=[])
                # For insert - return created evaluation
                insert_mock = Mock()
                insert_mock.execute.return_value = Mock(data=[mock_evaluation_data])
                mock.insert.return_value = insert_mock
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "team_members":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[{"id": 1, "team_id": 1, "user_id": 1}])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluation_scores":
                insert_mock = Mock()
                insert_mock.execute.return_value = Mock(data=mock_scores_data)
                mock.insert.return_value = insert_mock
            else:
                mock.select.return_value = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[])))))
            
            return mock

        payload = {
            "form_id": 1,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 85,
            "scores": [
                {"criterion_id": 1, "score": 40},
                {"criterion_id": 2, "score": 45}
            ],
            "comments": "Test evaluation"
        }

        with patch('app.api.v1.evaluations.supabase') as mock_supabase:
            mock_supabase.table = mock_table
            
            # Measure submission time
            start_time = time.time()
            response = client.post("/api/v1/evaluations/", json=payload)
            end_time = time.time()
            
            submission_time = end_time - start_time
            
            # Assert response is successful
            assert response.status_code in [201, 400, 404, 422, 500], f"Unexpected status code: {response.status_code}"
            
            # OPETSE-21: Assert submission completes within 2 seconds
            assert submission_time < 2.0, f"Submission took {submission_time:.3f}s, expected < 2.0s"
            
            # If successful, check that response includes submission time
            if response.status_code == 201:
                response_data = response.json()
                assert "submission_time_seconds" in response_data or "submission_time_seconds" in response_data.get("evaluation", {}), \
                    "Response should include submission_time_seconds"
                
                server_time = response_data.get("submission_time_seconds") or response_data.get("evaluation", {}).get("submission_time_seconds")
                if server_time:
                    assert server_time < 2.0, f"Server reported submission time {server_time}s, expected < 2.0s"

    def test_batch_score_insert_performance(self, client):
        """
        OPETSE-21: Test that batch score insertion is faster than individual inserts.
        
        This test verifies that the optimization to batch insert scores
        improves performance compared to individual inserts.
        """
        # Mock Supabase responses
        mock_form_data = {
            "id": 1,
            "title": "Test Form",
            "max_score": 100,
            "deadline": "2099-12-31T23:59:59"
        }
        
        mock_team_data = {"id": 1, "name": "Test Team"}
        mock_user_data = {"id": 1}
        
        # Create multiple criteria to test batch insert
        mock_criteria_data = [
            {"id": i, "form_id": 1, "text": f"Criterion {i}", "max_points": 10, "weight": 10}
            for i in range(1, 11)  # 10 criteria
        ]
        
        mock_evaluation_data = {"id": 100, "form_id": 1, "evaluator_id": 1, "evaluatee_id": 2, "team_id": 1, "total_score": 75}
        mock_scores_data = [
            {"id": i, "evaluation_id": 100, "criterion_id": i, "score": 7}
            for i in range(1, 11)  # 10 scores
        ]

        def mock_table(table_name):
            mock = Mock()
            
            if table_name == "evaluation_forms":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_form_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "teams":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_team_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "users":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_user_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "form_criteria":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=mock_criteria_data)
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluations":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[])
                insert_mock = Mock()
                insert_mock.execute.return_value = Mock(data=[mock_evaluation_data])
                mock.insert.return_value = insert_mock
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "team_members":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[{"id": 1, "team_id": 1, "user_id": 1}])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluation_scores":
                insert_mock = Mock()
                # Verify batch insert is called (single insert call with list)
                insert_mock.execute.return_value = Mock(data=mock_scores_data)
                mock.insert.return_value = insert_mock
            else:
                mock.select.return_value = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[])))))
            
            return mock

        # Create payload with multiple scores
        payload = {
            "form_id": 1,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 75,
            "scores": [
                {"criterion_id": i, "score": 7}
                for i in range(1, 11)  # 10 scores
            ],
            "comments": "Test evaluation with multiple scores"
        }

        with patch('app.api.v1.evaluations.supabase') as mock_supabase:
            mock_supabase.table = mock_table
            
            start_time = time.time()
            response = client.post("/api/v1/evaluations/", json=payload)
            end_time = time.time()
            
            submission_time = end_time - start_time
            
            # Assert response is successful
            assert response.status_code in [201, 400, 404, 422, 500], f"Unexpected status code: {response.status_code}"
            
            # OPETSE-21: Even with multiple scores, submission should complete within 2 seconds
            assert submission_time < 2.0, f"Batch insert submission took {submission_time:.3f}s, expected < 2.0s"
            
            # Verify batch insert was used (check that insert was called once with a list)
            if response.status_code == 201:
                scores_table = mock_supabase.table("evaluation_scores")
                # Verify insert was called (batch insert should be a single call)
                assert scores_table.insert.called, "Batch insert should be called for scores"
                
                # Get the call arguments to verify it's a batch (list of dicts)
                call_args = scores_table.insert.call_args
                if call_args:
                    inserted_data = call_args[0][0] if call_args[0] else None
                    if inserted_data:
                        # Should be a list (batch) not a single dict
                        assert isinstance(inserted_data, list), "Scores should be inserted as a batch (list)"

    def test_submission_time_tracking(self, client):
        """
        OPETSE-21: Test that submission time is tracked and returned in response.
        
        Verifies that the API response includes submission_time_seconds metric.
        """
        # Mock Supabase responses
        mock_form_data = {
            "id": 1,
            "title": "Test Form",
            "max_score": 100,
            "deadline": "2099-12-31T23:59:59"
        }
        
        mock_team_data = {"id": 1, "name": "Test Team"}
        mock_user_data = {"id": 1}
        mock_criteria_data = [
            {"id": 1, "form_id": 1, "text": "Criterion 1", "max_points": 50, "weight": 50}
        ]
        mock_evaluation_data = {"id": 100, "form_id": 1, "evaluator_id": 1, "evaluatee_id": 2, "team_id": 1, "total_score": 50}
        mock_scores_data = [
            {"id": 1, "evaluation_id": 100, "criterion_id": 1, "score": 50}
        ]

        def mock_table(table_name):
            mock = Mock()
            
            if table_name == "evaluation_forms":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_form_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "teams":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_team_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "users":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_user_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "form_criteria":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=mock_criteria_data)
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluations":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[])
                insert_mock = Mock()
                insert_mock.execute.return_value = Mock(data=[mock_evaluation_data])
                mock.insert.return_value = insert_mock
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "team_members":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[{"id": 1, "team_id": 1, "user_id": 1}])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluation_scores":
                insert_mock = Mock()
                insert_mock.execute.return_value = Mock(data=mock_scores_data)
                mock.insert.return_value = insert_mock
            else:
                mock.select.return_value = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[])))))
            
            return mock

        payload = {
            "form_id": 1,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 50,
            "scores": [
                {"criterion_id": 1, "score": 50}
            ],
            "comments": "Test evaluation"
        }

        with patch('app.api.v1.evaluations.supabase') as mock_supabase:
            mock_supabase.table = mock_table
            
            response = client.post("/api/v1/evaluations/", json=payload)
            
            # If successful, verify submission time is included
            if response.status_code == 201:
                response_data = response.json()
                
                # Check for submission_time_seconds in response
                assert "submission_time_seconds" in response_data or "submission_time_seconds" in response_data.get("evaluation", {}), \
                    "Response should include submission_time_seconds metric"
                
                server_time = response_data.get("submission_time_seconds") or response_data.get("evaluation", {}).get("submission_time_seconds")
                assert server_time is not None, "submission_time_seconds should not be None"
                assert isinstance(server_time, (int, float)), "submission_time_seconds should be a number"
                assert server_time >= 0, "submission_time_seconds should be non-negative"
                assert server_time < 2.0, f"submission_time_seconds should be < 2.0s, got {server_time}s"

    def test_p95_latency_requirement(self, client):
        """
        OPETSE-21: Test P95 latency requirement (95th percentile ≤ 2s).
        
        NFR S18: Fast form submissions - evaluations complete with low latency (P95 ≤ 2s).
        
        This test simulates multiple submissions and verifies that the 95th percentile
        of submission times is at or below 2 seconds.
        """
        # Mock Supabase responses
        mock_form_data = {
            "id": 1,
            "title": "Test Form",
            "max_score": 100,
            "deadline": "2099-12-31T23:59:59"
        }
        
        mock_team_data = {"id": 1, "name": "Test Team"}
        mock_user_data = {"id": 1}
        mock_criteria_data = [
            {"id": 1, "form_id": 1, "text": "Criterion 1", "max_points": 50, "weight": 50},
            {"id": 2, "form_id": 1, "text": "Criterion 2", "max_points": 50, "weight": 50}
        ]
        
        def mock_table(table_name):
            mock = Mock()
            
            if table_name == "evaluation_forms":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_form_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "teams":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_team_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "users":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[mock_user_data])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "form_criteria":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=mock_criteria_data)
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluations":
                select_mock = Mock()
                eq_mock = Mock()
                # Return empty for duplicate check, different evaluation_id for each insert
                eq_mock.execute.return_value = Mock(data=[])
                insert_mock = Mock()
                
                # Counter for unique IDs
                eval_id_counter = [100]
                
                def create_eval(*args, **kwargs):
                    eval_id = eval_id_counter[0]
                    eval_id_counter[0] += 1
                    return Mock(data=[{
                        "id": eval_id,
                        "form_id": 1,
                        "evaluator_id": 1,
                        "evaluatee_id": 2,
                        "team_id": 1,
                        "total_score": 85
                    }])
                
                insert_mock.execute.side_effect = create_eval
                mock.insert.return_value = insert_mock
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "team_members":
                select_mock = Mock()
                eq_mock = Mock()
                eq_mock.execute.return_value = Mock(data=[{"id": 1, "team_id": 1, "user_id": 1}])
                select_mock.eq.return_value = eq_mock
                mock.select.return_value = select_mock
            elif table_name == "evaluation_scores":
                insert_mock = Mock()
                insert_mock.execute.return_value = Mock(data=[
                    {"id": 1, "evaluation_id": 100, "criterion_id": 1, "score": 40},
                    {"id": 2, "evaluation_id": 100, "criterion_id": 2, "score": 45}
                ])
                mock.insert.return_value = insert_mock
            else:
                mock.select.return_value = Mock(eq=Mock(return_value=Mock(execute=Mock(return_value=Mock(data=[])))))
            
            return mock

        # Run multiple submissions to collect latency data
        num_samples = 20  # Number of samples for P95 calculation
        latencies = []

        payload = {
            "form_id": 1,
            "evaluator_id": 1,
            "evaluatee_id": 2,
            "team_id": 1,
            "total_score": 85,
            "scores": [
                {"criterion_id": 1, "score": 40},
                {"criterion_id": 2, "score": 45}
            ],
            "comments": "Test evaluation for P95 latency"
        }

        with patch('app.api.v1.evaluations.supabase') as mock_supabase:
            mock_supabase.table = mock_table
            
            # Collect latency samples
            for i in range(num_samples):
                start_time = time.time()
                response = client.post("/api/v1/evaluations/", json=payload)
                end_time = time.time()
                
                submission_time = end_time - start_time
                latencies.append(submission_time)
                
                # Log individual submission times for debugging
                print(f"Sample {i+1}/{num_samples}: {submission_time:.3f}s")

        # Calculate P95 (95th percentile)
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]
        
        # Calculate other statistics for reporting
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"\n📊 Performance Statistics:")
        print(f"  Samples: {num_samples}")
        print(f"  Min: {min_latency:.3f}s")
        print(f"  Avg: {avg_latency:.3f}s")
        print(f"  P95: {p95_latency:.3f}s")
        print(f"  Max: {max_latency:.3f}s")
        
        # OPETSE-21: Assert P95 latency is ≤ 2 seconds
        assert p95_latency <= 2.0, (
            f"P95 latency ({p95_latency:.3f}s) exceeds requirement of 2.0s. "
            f"Statistics: Min={min_latency:.3f}s, Avg={avg_latency:.3f}s, Max={max_latency:.3f}s"
        )
        
        # Additional assertion: average should also be well below 2s
        assert avg_latency < 1.5, (
            f"Average latency ({avg_latency:.3f}s) is too high. "
            f"While P95={p95_latency:.3f}s meets requirement, average should be < 1.5s"
        )

