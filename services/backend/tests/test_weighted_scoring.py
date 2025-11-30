"""
Tests for Weighted Scoring Functionality (OPETSE-14).

Tests the WeightedScoringCalculator and integration with forms and evaluations.
"""

import pytest
from decimal import Decimal
from app.utils.weighted_scoring import WeightedScoringCalculator


class TestWeightValidation:
    """Test weight validation logic."""

    def test_validate_weights_sum_to_100(self):
        """Test that weights summing to 100% are valid."""
        criteria = [
            {'weight': 40, 'id': 1},
            {'weight': 35, 'id': 2},
            {'weight': 25, 'id': 3}
        ]
        is_valid, msg = WeightedScoringCalculator.validate_weights(criteria)
        assert is_valid is True
        assert msg == ""

    def test_validate_weights_with_decimals(self):
        """Test that decimal weights are validated correctly."""
        criteria = [
            {'weight': 33.33, 'id': 1},
            {'weight': 33.33, 'id': 2},
            {'weight': 33.34, 'id': 3}
        ]
        is_valid, msg = WeightedScoringCalculator.validate_weights(criteria)
        assert is_valid is True

    def test_validate_weights_not_summing_to_100(self):
        """Test that weights not summing to 100% are invalid."""
        criteria = [
            {'weight': 40, 'id': 1},
            {'weight': 40, 'id': 2},
            {'weight': 25, 'id': 3}
        ]
        is_valid, msg = WeightedScoringCalculator.validate_weights(criteria)
        assert is_valid is False
        assert "must sum to 100%" in msg

    def test_validate_negative_weight(self):
        """Test that negative weights are invalid."""
        criteria = [
            {'weight': -10, 'id': 1},
            {'weight': 60, 'id': 2},
            {'weight': 50, 'id': 3}
        ]
        is_valid, msg = WeightedScoringCalculator.validate_weights(criteria)
        assert is_valid is False
        assert "negative weight" in msg

    def test_validate_weight_exceeds_100(self):
        """Test that weight exceeding 100% is rejected."""
        criteria = [
            {'weight': 150, 'id': 1}
        ]
        is_valid, msg = WeightedScoringCalculator.validate_weights(criteria)
        assert is_valid is False
        assert "150%" in msg or "exceeding 100%" in msg

    def test_validate_empty_criteria(self):
        """Test that empty criteria list is invalid."""
        is_valid, msg = WeightedScoringCalculator.validate_weights([])
        assert is_valid is False
        assert "No criteria" in msg

    def test_validate_single_criterion_100_percent(self):
        """Test that single criterion with 100% weight is valid."""
        criteria = [{'weight': 100, 'id': 1}]
        is_valid, msg = WeightedScoringCalculator.validate_weights(criteria)
        assert is_valid is True


class TestWeightedScoreCalculation:
    """Test weighted score calculation."""

    def test_calculate_simple_weighted_score(self):
        """Test basic weighted score calculation."""
        criteria = [
            {'id': 1, 'weight': 50, 'max_points': 10, 'text': 'Quality'},
            {'id': 2, 'weight': 50, 'max_points': 10, 'text': 'Timeliness'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 8},
            {'criterion_id': 2, 'score': 6}
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        # (8/10 * 0.5 * 100) + (6/10 * 0.5 * 100) = 40 + 30 = 70
        assert result['weighted_total'] == 70.0
        assert result['percentage'] == 70.0
        assert len(result['breakdown']) == 2

    def test_calculate_unequal_weights(self):
        """Test weighted score with unequal weights."""
        criteria = [
            {'id': 1, 'weight': 60, 'max_points': 20, 'text': 'Code Quality'},
            {'id': 2, 'weight': 40, 'max_points': 10, 'text': 'Documentation'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 15},  # 15/20 = 0.75
            {'criterion_id': 2, 'score': 10}   # 10/10 = 1.0
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        # (15/20 * 0.6 * 100) + (10/10 * 0.4 * 100) = 45 + 40 = 85
        assert result['weighted_total'] == 85.0
        assert result['percentage'] == 85.0

    def test_calculate_with_zero_score(self):
        """Test weighted calculation with zero scores."""
        criteria = [
            {'id': 1, 'weight': 100, 'max_points': 10, 'text': 'Quality'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 0}
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        assert result['weighted_total'] == 0.0
        assert result['percentage'] == 0.0

    def test_calculate_perfect_score(self):
        """Test weighted calculation with perfect scores."""
        criteria = [
            {'id': 1, 'weight': 40, 'max_points': 25, 'text': 'A'},
            {'id': 2, 'weight': 30, 'max_points': 20, 'text': 'B'},
            {'id': 3, 'weight': 30, 'max_points': 15, 'text': 'C'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 25},
            {'criterion_id': 2, 'score': 20},
            {'criterion_id': 3, 'score': 15}
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        assert result['weighted_total'] == 100.0
        assert result['percentage'] == 100.0

    def test_breakdown_includes_all_criteria(self):
        """Test that breakdown includes details for each criterion."""
        criteria = [
            {'id': 1, 'weight': 50, 'max_points': 10, 'text': 'Criterion 1'},
            {'id': 2, 'weight': 50, 'max_points': 10, 'text': 'Criterion 2'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 8},
            {'criterion_id': 2, 'score': 9}
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        breakdown = result['breakdown']
        assert len(breakdown) == 2

        # Check first criterion
        assert breakdown[0]['criterion_id'] == 1
        assert breakdown[0]['raw_score'] == 8
        assert breakdown[0]['max_points'] == 10
        assert breakdown[0]['weight'] == 50
        assert breakdown[0]['weighted_score'] == 40.0

        # Check second criterion
        assert breakdown[1]['criterion_id'] == 2
        assert breakdown[1]['raw_score'] == 9
        assert breakdown[1]['weighted_score'] == 45.0

    def test_rounding_precision(self):
        """Test that scores are rounded to 2 decimal places."""
        criteria = [
            {'id': 1, 'weight': 33.33, 'max_points': 9, 'text': 'A'},
            {'id': 2, 'weight': 33.33, 'max_points': 9, 'text': 'B'},
            {'id': 3, 'weight': 33.34, 'max_points': 9, 'text': 'C'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 7},
            {'criterion_id': 2, 'score': 8},
            {'criterion_id': 3, 'score': 6}
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        # Result should be rounded to 2 decimals
        assert isinstance(result['weighted_total'], float)
        assert round(result['weighted_total'], 2) == result['weighted_total']


class TestWeightDistribution:
    """Test automatic weight distribution."""

    def test_distribute_weights_evenly_three_criteria(self):
        """Test even distribution among 3 criteria."""
        weights = WeightedScoringCalculator.distribute_weights_evenly(3)

        assert len(weights) == 3
        assert abs(sum(weights) - Decimal('100')) < Decimal('0.02')
        # Should be approximately 33.33, 33.33, 33.34
        for w in weights:
            assert Decimal('33') <= w <= Decimal('34')

    def test_distribute_weights_evenly_four_criteria(self):
        """Test even distribution among 4 criteria."""
        weights = WeightedScoringCalculator.distribute_weights_evenly(4)

        assert len(weights) == 4
        assert sum(weights) == Decimal('100')
        # Should be 25, 25, 25, 25
        assert all(w == Decimal('25.00') for w in weights)

    def test_distribute_weights_single_criterion(self):
        """Test distribution for single criterion."""
        weights = WeightedScoringCalculator.distribute_weights_evenly(1)

        assert len(weights) == 1
        assert weights[0] == Decimal('100.00')

    def test_distribute_weights_zero_criteria(self):
        """Test distribution for zero criteria."""
        weights = WeightedScoringCalculator.distribute_weights_evenly(0)
        assert weights == []

    def test_distribute_weights_many_criteria(self):
        """Test distribution with many criteria."""
        weights = WeightedScoringCalculator.distribute_weights_evenly(7)

        assert len(weights) == 7
        assert abs(sum(weights) - Decimal('100')) < Decimal('0.04')


class TestWeightSuggestions:
    """Test weight suggestion based on importance."""

    def test_suggest_weights_all_medium(self):
        """Test suggestions when all criteria have medium importance."""
        criteria = [
            {'id': 1, 'text': 'A'},
            {'id': 2, 'text': 'B'},
            {'id': 3, 'text': 'C'}
        ]
        importance_levels = {
            1: 'medium',
            2: 'medium',
            3: 'medium'
        }

        weights = WeightedScoringCalculator.get_weight_suggestions(
            criteria,
            importance_levels
        )

        assert len(weights) == 3
        assert sum(weights) == Decimal('100')
        # All should be approximately equal for all medium
        assert abs(weights[0] - weights[1]) <= Decimal('0.01')
        assert abs(weights[1] - weights[2]) <= Decimal('0.01')

    def test_suggest_weights_mixed_importance(self):
        """Test suggestions with mixed importance levels."""
        criteria = [
            {'id': 1, 'text': 'High Importance'},
            {'id': 2, 'text': 'Medium Importance'},
            {'id': 3, 'text': 'Low Importance'}
        ]
        importance_levels = {
            1: 'high',
            2: 'medium',
            3: 'low'
        }

        weights = WeightedScoringCalculator.get_weight_suggestions(
            criteria,
            importance_levels
        )

        assert len(weights) == 3
        assert sum(weights) == Decimal('100')
        # High should be greater than medium, medium greater than low
        assert weights[0] > weights[1] > weights[2]

    def test_suggest_weights_no_importance_provided(self):
        """Test suggestions when no importance levels provided."""
        criteria = [
            {'id': 1, 'text': 'A'},
            {'id': 2, 'text': 'B'}
        ]

        weights = WeightedScoringCalculator.get_weight_suggestions(criteria, None)

        # Should default to even distribution
        assert len(weights) == 2
        assert sum(weights) == Decimal('100')
        assert weights[0] == weights[1] == Decimal('50.00')

    def test_suggest_weights_all_high(self):
        """Test suggestions when all criteria are high importance."""
        criteria = [
            {'id': 1, 'text': 'A'},
            {'id': 2, 'text': 'B'}
        ]
        importance_levels = {
            1: 'high',
            2: 'high'
        }

        weights = WeightedScoringCalculator.get_weight_suggestions(
            criteria,
            importance_levels
        )

        # All high importance should result in equal distribution
        assert weights[0] == weights[1] == Decimal('50.00')


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_missing_scores_for_criterion(self):
        """Test calculation when scores are missing for a criterion."""
        criteria = [
            {'id': 1, 'weight': 50, 'max_points': 10, 'text': 'A'},
            {'id': 2, 'weight': 50, 'max_points': 10, 'text': 'B'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 8}
            # Missing score for criterion 2
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        # Should treat missing score as 0
        assert result['weighted_total'] == 40.0  # Only criterion 1 counted

    def test_zero_max_points(self):
        """Test calculation with zero max_points."""
        criteria = [
            {'id': 1, 'weight': 100, 'max_points': 0, 'text': 'A'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 10}
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=100
        )

        # Should handle gracefully without division by zero
        assert result['weighted_total'] == 0.0

    def test_custom_max_score(self):
        """Test calculation with custom max_score."""
        criteria = [
            {'id': 1, 'weight': 100, 'max_points': 10, 'text': 'A'}
        ]
        scores = [
            {'criterion_id': 1, 'score': 5}
        ]

        result = WeightedScoringCalculator.calculate_weighted_score(
            scores=scores,
            criteria=criteria,
            max_score=50  # Custom max score
        )

        # (5/10) * 1.0 * 50 = 25
        assert result['weighted_total'] == 25.0
        assert result['max_score'] == 50
        assert result['percentage'] == 50.0  # 25/50 = 50%


# Integration test markers
@pytest.mark.integration
class TestWeightedScoringIntegration:
    """Integration tests for weighted scoring with API endpoints."""

    # These tests would require a test database and API client
    # Placeholder for actual integration tests

    def test_create_form_with_weights(self):
        """Test creating a form with weighted criteria via API."""
        # TODO: Implement with actual API client
        pass

    def test_submit_evaluation_calculates_weighted_score(self):
        """Test that evaluation submission uses weighted scoring."""
        # TODO: Implement with actual API client
        pass

    def test_report_shows_weighted_scores(self):
        """Test that reports display weighted scores correctly."""
        # TODO: Implement with actual API client
        pass
