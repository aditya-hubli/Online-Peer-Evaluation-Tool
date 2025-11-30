-- Add missing columns to evaluation_forms and fix form_criteria schema
-- Run this in Supabase SQL Editor

-- ========================================
-- EVALUATION_FORMS TABLE - Add missing columns
-- ========================================

-- Add deadline column to evaluation_forms
ALTER TABLE evaluation_forms 
ADD COLUMN IF NOT EXISTS deadline TIMESTAMP WITH TIME ZONE;

-- Add max_score column to evaluation_forms
ALTER TABLE evaluation_forms
ADD COLUMN IF NOT EXISTS max_score INTEGER DEFAULT 100;

-- Create index for deadline queries
CREATE INDEX IF NOT EXISTS idx_evaluation_forms_deadline ON evaluation_forms(deadline);

-- ========================================
-- FORM_CRITERIA TABLE - Fix columns to match API expectations
-- ========================================

-- The API uses: text, max_points, order_index, weight
-- Database has: criterion_name, max_score, display_order, weight

-- First, drop the NOT NULL constraints on old columns
ALTER TABLE form_criteria
ALTER COLUMN criterion_name DROP NOT NULL;

ALTER TABLE form_criteria
ALTER COLUMN max_score DROP NOT NULL;

-- Add new columns if they don't exist
ALTER TABLE form_criteria
ADD COLUMN IF NOT EXISTS text VARCHAR(255);

ALTER TABLE form_criteria
ADD COLUMN IF NOT EXISTS max_points INTEGER;

ALTER TABLE form_criteria
ADD COLUMN IF NOT EXISTS order_index INTEGER;

-- Copy data from old columns to new columns (for existing data)
UPDATE form_criteria 
SET text = criterion_name 
WHERE text IS NULL AND criterion_name IS NOT NULL;

UPDATE form_criteria 
SET max_points = max_score 
WHERE max_points IS NULL AND max_score IS NOT NULL;

UPDATE form_criteria 
SET order_index = display_order 
WHERE order_index IS NULL;

-- FIX: Change weight column from DECIMAL(3,2) to DECIMAL(5,2) to support 0-100 percentages
ALTER TABLE form_criteria
ALTER COLUMN weight TYPE DECIMAL(5, 2);

-- Set default value for weight if needed
ALTER TABLE form_criteria
ALTER COLUMN weight SET DEFAULT 1.0;

-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON COLUMN evaluation_forms.deadline IS 'OPETSE-9: Deadline for form submission';
COMMENT ON COLUMN evaluation_forms.max_score IS 'Maximum total score for the evaluation form';
COMMENT ON COLUMN form_criteria.text IS 'Criterion description text';
COMMENT ON COLUMN form_criteria.max_points IS 'Maximum points for this criterion';
COMMENT ON COLUMN form_criteria.order_index IS 'Display order of criterion';
COMMENT ON COLUMN form_criteria.weight IS 'OPETSE-14: Criterion weight as percentage (0-100)';

SELECT 'Schema columns updated successfully!' AS status;
