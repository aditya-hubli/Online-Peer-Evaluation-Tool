-- ============================================
-- FORM ROLLBACK CAPABILITY - DATABASE MIGRATION
-- OPETSE-25: Form version history and rollback
-- ============================================
-- Run this SQL in your Supabase SQL Editor
-- ============================================

-- Create form_versions table to store historical snapshots
CREATE TABLE IF NOT EXISTS form_versions (
    id BIGSERIAL PRIMARY KEY,
    form_id BIGINT NOT NULL,
    version_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    max_score INTEGER DEFAULT 100,
    deadline TIMESTAMP WITH TIME ZONE,
    criteria JSONB NOT NULL,  -- Store all criteria as JSON
    created_by BIGINT,  -- User who made the change (optional)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(form_id, version_number)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_form_versions_form_id ON form_versions(form_id);
CREATE INDEX IF NOT EXISTS idx_form_versions_created_at ON form_versions(created_at DESC);

-- Add foreign key constraint (optional, for referential integrity)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_form_versions_form_id'
    ) THEN
        ALTER TABLE form_versions
        ADD CONSTRAINT fk_form_versions_form_id
        FOREIGN KEY (form_id) REFERENCES evaluation_forms(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add comment to table
COMMENT ON TABLE form_versions IS 'Historical snapshots of evaluation forms for rollback capability (OPETSE-25)';
COMMENT ON COLUMN form_versions.criteria IS 'JSON array of all criteria with their properties';
COMMENT ON COLUMN form_versions.version_number IS 'Sequential version number for each form (starts at 1)';

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check if table was created successfully
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'form_versions'
ORDER BY ordinal_position;

-- Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'form_versions';

-- ============================================
-- ROLLBACK (if needed)
-- ============================================
-- Uncomment to drop the table and undo changes
-- DROP TABLE IF EXISTS form_versions CASCADE;
