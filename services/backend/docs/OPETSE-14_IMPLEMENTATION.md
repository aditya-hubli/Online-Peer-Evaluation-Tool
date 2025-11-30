# OPETSE-14: Weighted Scoring Implementation

## Story
**As an instructor, I want to apply weighted scoring for criteria so aggregated scores reflect rubric weights.**

## Overview
This feature allows instructors to assign different weights to evaluation criteria, ensuring that the final score accurately reflects the relative importance of each criterion.

## Implementation Details

### 1. Database Changes
- Added `weight` column to `form_criteria` table (DECIMAL(5,2), range 0-100)
- Weights represent percentage contribution to final score
- Constraint ensures weights are between 0 and 100
- Migration script automatically distributes weights evenly for existing forms

### 2. Backend Components

#### New Module: `app/utils/weighted_scoring.py`
Main utility class for weighted score calculations:

**Key Methods:**
- `validate_weights()`: Ensures criterion weights sum to 100%
- `calculate_weighted_score()`: Computes weighted total from individual scores
- `distribute_weights_evenly()`: Auto-distributes weights equally
- `get_weight_suggestions()`: Suggests weights based on importance levels

**Algorithm:**
```
For each criterion:
1. Normalize score: normalized = score / max_points
2. Apply weight: weighted = normalized * (weight / 100) * max_score
3. Sum all weighted values for final score
```

#### Updated APIs

**Forms API (`app/api/v1/forms.py`):**
- `FormCriterion` model now includes `weight` field
- `create_form()`: Validates that weights sum to 100%
- `update_criterion()`: Allows updating individual criterion weights
- Auto-assigns equal weights if not provided

**Evaluations API (`app/api/v1/evaluations.py`):**
- `calculate_evaluation_score()`: Uses weighted scoring calculation
- Returns both raw scores and weighted total

**Reports API (`app/api/v1/reports.py`):**
- `get_form_report()`: Shows weight distribution analysis
- `get_team_report()`: Uses weighted scores in aggregations
- Includes breakdown of weighted vs unweighted scores

### 3. API Examples

#### Creating a Form with Weighted Criteria
```json
POST /api/v1/forms/
{
  "project_id": 1,
  "title": "Sprint 1 Evaluation",
  "max_score": 100,
  "criteria": [
    {
      "text": "Code Quality",
      "max_points": 25,
      "weight": 40.0,
      "order_index": 0
    },
    {
      "text": "Documentation",
      "max_points": 20,
      "weight": 25.0,
      "order_index": 1
    },
    {
      "text": "Collaboration",
      "max_points": 30,
      "weight": 35.0,
      "order_index": 2
    }
  ]
}
```

#### Weighted Score Calculation Example
```
Given:
- Criterion 1: Score 20/25, Weight 40%
- Criterion 2: Score 15/20, Weight 25%
- Criterion 3: Score 25/30, Weight 35%

Calculation:
- Criterion 1: (20/25) * 0.40 * 100 = 32.0
- Criterion 2: (15/20) * 0.25 * 100 = 18.75
- Criterion 3: (25/30) * 0.35 * 100 = 29.17

Weighted Total: 79.92 / 100
```

### 4. Validation Rules
1. All criterion weights for a form must sum to exactly 100%
2. Individual weights must be between 0 and 100
3. At least one criterion must have weight > 0
4. Weights are stored with 2 decimal precision

### 5. Testing Strategy
- Unit tests for `WeightedScoringCalculator` class
- Integration tests for weighted scoring in evaluations
- Edge cases: zero weights, single criterion, unequal distributions
- Performance tests with large numbers of criteria

### 6. Migration Path
- Existing forms automatically receive equal weight distribution
- Backward compatible: if weights not specified, defaults to equal distribution
- Database migration preserves all existing data

### 7. Frontend Integration Points
- Form creation: weight input fields for each criterion
- Form editing: adjust weights with real-time validation
- Evaluation display: show weighted vs raw scores
- Reports: visualize weight distribution and impact

## Files Modified/Created

### New Files:
- `services/backend/app/utils/weighted_scoring.py`
- `services/backend/docs/weighted_scoring_migration.sql`
- `services/backend/docs/OPETSE-14_IMPLEMENTATION.md` (this file)
- `services/backend/tests/test_weighted_scoring.py`

### Modified Files:
- `services/backend/app/api/v1/forms.py`
- `services/backend/app/api/v1/evaluations.py`
- `services/backend/app/api/v1/reports.py`
- `.github/workflows/ci-cd.yml`

## Acceptance Criteria
- [x] Instructors can assign weights to each criterion when creating a form
- [x] Weights must sum to 100% (validation enforced)
- [x] Evaluation scores are calculated using weighted formula
- [x] Reports display weighted scores
- [x] Migration handles existing data gracefully
- [x] Comprehensive test coverage (>90%)
- [x] API documentation updated
- [x] CI/CD pipeline includes weighted scoring tests

## Future Enhancements
- Weight presets (e.g., "Code-Heavy", "Process-Focused")
- Weight templates that can be reused across forms
- Visual weight distribution editor in frontend
- Analytics on how weights affect score distributions
