-- ============================================
-- OPETSE-14: Weighted Scoring Migration
-- ============================================
-- Add weight column to form_criteria table
-- This allows instructors to assign different weights to each criterion
-- Weights should sum to 100% for each form
-- ============================================

-- Add weight column to form_criteria
ALTER TABLE form_criteria
ADD COLUMN IF NOT EXISTS weight DECIMAL(5, 2) DEFAULT 0.00;

-- Add constraint to ensure weight is between 0 and 100
ALTER TABLE form_criteria
ADD CONSTRAINT check_weight_range 
CHECK (weight >= 0 AND weight <= 100);

-- Update existing records to have equal weights
DO $$
DECLARE
    form_record RECORD;
    criteria_count INTEGER;
    equal_weight DECIMAL(5, 2);
BEGIN
    -- For each form, distribute weights equally among criteria
    FOR form_record IN 
        SELECT DISTINCT form_id FROM form_criteria
    LOOP
        -- Count criteria for this form
        SELECT COUNT(*) INTO criteria_count
        FROM form_criteria
        WHERE form_id = form_record.form_id;
        
        -- Calculate equal weight
        IF criteria_count > 0 THEN
            equal_weight := ROUND(100.0 / criteria_count, 2);
            
            -- Update all criteria for this form
            UPDATE form_criteria
            SET weight = equal_weight
            WHERE form_id = form_record.form_id;
            
            -- Adjust first criterion to ensure sum is exactly 100
            UPDATE form_criteria
            SET weight = weight + (100 - (
                SELECT SUM(weight) 
                FROM form_criteria 
                WHERE form_id = form_record.form_id
            ))
            WHERE id = (
                SELECT id 
                FROM form_criteria 
                WHERE form_id = form_record.form_id 
                ORDER BY id 
                LIMIT 1
            );
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Successfully migrated weights for all forms';
END $$;

-- Create index for better performance on weight queries
CREATE INDEX IF NOT EXISTS idx_form_criteria_weight ON form_criteria(weight);

-- Add comment to document the column
COMMENT ON COLUMN form_criteria.weight IS 
'Weight of criterion as percentage (0-100). Sum of weights for all criteria in a form should equal 100.';

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Run this to verify weights sum to 100 for each form:

SELECT 
    form_id,
    COUNT(*) as criteria_count,
    SUM(weight) as total_weight,
    CASE 
        WHEN ABS(SUM(weight) - 100) < 0.01 THEN 'Valid'
        ELSE 'Invalid - Does not sum to 100'
    END as validation_status
FROM form_criteria
GROUP BY form_id
ORDER BY form_id;

-- ============================================
-- ROLLBACK (if needed)
-- ============================================
-- To rollback this migration, run:
-- ALTER TABLE form_criteria DROP COLUMN IF EXISTS weight;
-- DROP INDEX IF EXISTS idx_form_criteria_weight;
