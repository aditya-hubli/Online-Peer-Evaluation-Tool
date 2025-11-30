-- ============================================
-- OPETSE-9: ADD DEADLINE ENFORCEMENT
-- ============================================
-- Migration to add deadline column to evaluation_forms table
-- Run this in your Supabase SQL Editor after deploying OPETSE-9
-- ============================================

-- Add deadline column to evaluation_forms table
DO $$ 
BEGIN
    -- Check if column doesn't exist before adding
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'evaluation_forms' 
        AND column_name = 'deadline'
    ) THEN
        ALTER TABLE evaluation_forms 
        ADD COLUMN deadline TIMESTAMP WITH TIME ZONE;
        
        RAISE NOTICE 'Added deadline column to evaluation_forms table';
    ELSE
        RAISE NOTICE 'Deadline column already exists in evaluation_forms table';
    END IF;
END $$;

-- Create an index on deadline for faster queries
CREATE INDEX IF NOT EXISTS idx_evaluation_forms_deadline 
ON evaluation_forms(deadline);

-- ============================================
-- OPTIONAL: Add sample deadlines to existing forms
-- ============================================
-- Uncomment the following to set deadlines for existing forms
-- (7 days from now as an example)

-- UPDATE evaluation_forms 
-- SET deadline = NOW() + INTERVAL '7 days'
-- WHERE deadline IS NULL;

-- ============================================
-- VERIFICATION
-- ============================================
-- Check that the column was added successfully

SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'evaluation_forms' 
    AND column_name = 'deadline';

-- Show forms with deadlines
SELECT 
    id,
    title,
    deadline,
    CASE 
        WHEN deadline IS NULL THEN 'No deadline'
        WHEN deadline < NOW() THEN 'Expired'
        ELSE 'Active'
    END as status
FROM evaluation_forms
ORDER BY deadline NULLS LAST;

-- ============================================
-- SUCCESS! 🎉
-- ============================================
-- Deadline column added. Forms can now have deadlines.
-- Submissions after deadline will be automatically blocked by the API.
