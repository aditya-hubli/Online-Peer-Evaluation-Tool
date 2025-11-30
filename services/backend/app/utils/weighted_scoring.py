"""
Weighted Scoring Utility for OPETSE-14.

This module provides functionality to calculate weighted scores for evaluations
based on criterion weights defined in evaluation forms.
"""

from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP


class WeightedScoringCalculator:
    """Calculate weighted scores for evaluations."""

    @staticmethod
    def validate_weights(criteria: List[Dict]) -> tuple[bool, str]:
        """
        Validate that criterion weights sum to 100% (or 1.0).

        Args:
            criteria: List of criterion dictionaries with 'weight' field

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not criteria:
            return False, "No criteria provided"

        total_weight = sum(
            Decimal(str(c.get('weight', 0)))
            for c in criteria
        )

        # Allow small floating point differences (within 0.01%)
        if abs(total_weight - Decimal('100')) > Decimal('0.01'):
            return False, f"Weights must sum to 100%. Current sum: {total_weight}%"

        # Check individual weights are valid
        for i, criterion in enumerate(criteria):
            weight = Decimal(str(criterion.get('weight', 0)))
            if weight < 0:
                return False, f"Criterion {i+1} has negative weight: {weight}%"
            if weight > 100:
                return False, f"Criterion {i+1} has weight exceeding 100%: {weight}%"

        return True, ""

    @staticmethod
    def calculate_weighted_score(
        scores: List[Dict],
        criteria: List[Dict],
        max_score: int = 100
    ) -> Dict:
        """
        Calculate weighted total score from individual criterion scores.

        Args:
            scores: List of score dicts with 'criterion_id' and 'score'
            criteria: List of criterion dicts with 'id', 'weight', and 'max_points'
            max_score: Maximum possible total score (default: 100)

        Returns:
            Dictionary with:
                - weighted_total: The final weighted score
                - breakdown: List of weighted scores per criterion
                - percentage: Score as percentage of max_score
        """
        # Create lookup maps
        criteria_map = {c['id']: c for c in criteria}
        score_map = {s['criterion_id']: s['score'] for s in scores}

        weighted_breakdown = []
        weighted_sum = Decimal('0')

        for criterion in criteria:
            criterion_id = criterion['id']
            weight = Decimal(str(criterion.get('weight', 0)))
            max_points = Decimal(str(criterion.get('max_points', 0)))
            score = Decimal(str(score_map.get(criterion_id, 0)))

            # Calculate normalized score (0-1 range)
            if max_points > 0:
                normalized_score = score / max_points
            else:
                normalized_score = Decimal('0')

            # Apply weight (weight is in percentage, so divide by 100)
            weighted_value = normalized_score * (weight / Decimal('100')) * Decimal(str(max_score))

            weighted_breakdown.append({
                'criterion_id': criterion_id,
                'criterion_text': criterion.get('text', ''),
                'raw_score': float(score),
                'max_points': float(max_points),
                'weight': float(weight),
                'weighted_score': float(weighted_value.quantize(
                    Decimal('0.01'),
                    rounding=ROUND_HALF_UP
                ))
            })

            weighted_sum += weighted_value

        # Round to 2 decimal places
        final_score = float(weighted_sum.quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        ))

        percentage = (final_score / max_score * 100) if max_score > 0 else 0

        return {
            'weighted_total': final_score,
            'breakdown': weighted_breakdown,
            'percentage': round(percentage, 2),
            'max_score': max_score
        }

    @staticmethod
    def distribute_weights_evenly(num_criteria: int) -> List[Decimal]:
        """
        Distribute weights evenly across criteria.

        Args:
            num_criteria: Number of criteria

        Returns:
            List of weights that sum to 100
        """
        if num_criteria <= 0:
            return []

        base_weight = Decimal('100') / Decimal(str(num_criteria))
        weights = [base_weight] * num_criteria

        # Adjust for rounding to ensure sum is exactly 100
        total = sum(weights)
        if total != Decimal('100'):
            diff = Decimal('100') - total
            weights[0] += diff

        return [w.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) for w in weights]

    @staticmethod
    def get_weight_suggestions(
        criteria: List[Dict],
        importance_levels: Optional[Dict[int, str]] = None
    ) -> List[Decimal]:
        """
        Suggest weights based on importance levels.

        Args:
            criteria: List of criterion dictionaries
            importance_levels: Optional dict mapping criterion_id to importance
                             ('high', 'medium', 'low')

        Returns:
            List of suggested weights
        """
        if not importance_levels:
            return WeightedScoringCalculator.distribute_weights_evenly(len(criteria))

        # Weight mapping: high=2x, medium=1x, low=0.5x
        importance_multipliers = {
            'high': Decimal('2'),
            'medium': Decimal('1'),
            'low': Decimal('0.5')
        }

        # Calculate total units
        total_units = Decimal('0')
        for criterion in criteria:
            importance = importance_levels.get(
                criterion['id'],
                'medium'
            )
            total_units += importance_multipliers.get(importance, Decimal('1'))

        # Distribute weights proportionally
        weights = []
        for criterion in criteria:
            importance = importance_levels.get(
                criterion['id'],
                'medium'
            )
            multiplier = importance_multipliers.get(importance, Decimal('1'))
            weight = (multiplier / total_units) * Decimal('100')
            weights.append(weight.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        # Ensure sum is exactly 100
        total = sum(weights)
        if total != Decimal('100'):
            diff = Decimal('100') - total
            weights[0] += diff

        return weights
