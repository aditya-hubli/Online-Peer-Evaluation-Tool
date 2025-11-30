-- ============================================
-- OPETSE-15: AUDIT LOGGING SYSTEM
-- ============================================
-- Migration to create audit_logs table for tracking all key actions
-- Run this in your Supabase SQL Editor after deploying OPETSE-15
-- ============================================

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    resource_type VARCHAR(50),
    resource_id BIGINT,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id 
ON audit_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action 
ON audit_logs(action);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource 
ON audit_logs(resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp 
ON audit_logs(timestamp DESC);

-- Create composite index for common filter combinations
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action_timestamp 
ON audit_logs(user_id, action, timestamp DESC);

-- Add comment to table
COMMENT ON TABLE audit_logs IS 'Audit trail for all significant system actions (OPETSE-15)';
COMMENT ON COLUMN audit_logs.action IS 'Type of action performed (e.g., user.created, form.deleted)';
COMMENT ON COLUMN audit_logs.user_id IS 'User who performed the action (NULL for system actions)';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource affected (e.g., user, form, evaluation)';
COMMENT ON COLUMN audit_logs.resource_id IS 'ID of the affected resource';
COMMENT ON COLUMN audit_logs.details IS 'Additional context as JSON (e.g., changed fields, old values)';
COMMENT ON COLUMN audit_logs.ip_address IS 'IP address of the user';
COMMENT ON COLUMN audit_logs.user_agent IS 'User agent string from the request';
COMMENT ON COLUMN audit_logs.timestamp IS 'When the action occurred';

-- ============================================
-- OPTIONAL: Create view for human-readable logs
-- ============================================

CREATE OR REPLACE VIEW audit_logs_with_user AS
SELECT 
    al.id,
    al.action,
    al.user_id,
    u.name as user_name,
    u.email as user_email,
    u.role as user_role,
    al.resource_type,
    al.resource_id,
    al.details,
    al.ip_address,
    al.timestamp
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
ORDER BY al.timestamp DESC;

COMMENT ON VIEW audit_logs_with_user IS 'Audit logs enriched with user information';

-- ============================================
-- OPTIONAL: Function to clean old audit logs
-- ============================================

CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_audit_logs IS 'Delete audit logs older than specified retention period (default 365 days)';

-- Example usage: SELECT cleanup_old_audit_logs(180); -- Keep only last 180 days

-- ============================================
-- VERIFICATION
-- ============================================

-- Check table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'audit_logs'
ORDER BY ordinal_position;

-- Check indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'audit_logs';

-- ============================================
-- SAMPLE QUERIES
-- ============================================

-- Get recent activity for a user
-- SELECT * FROM audit_logs WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 20;

-- Get all form deletions
-- SELECT * FROM audit_logs WHERE action = 'form.deleted' ORDER BY timestamp DESC;

-- Get change history for a specific evaluation
-- SELECT * FROM audit_logs 
-- WHERE resource_type = 'evaluation' AND resource_id = 5 
-- ORDER BY timestamp DESC;

-- Get all admin actions in the last 7 days
-- SELECT al.*, u.name, u.email 
-- FROM audit_logs al
-- JOIN users u ON al.user_id = u.id
-- WHERE u.role = 'admin' 
-- AND al.timestamp > NOW() - INTERVAL '7 days'
-- ORDER BY al.timestamp DESC;

-- Count actions by type
-- SELECT action, COUNT(*) as count
-- FROM audit_logs
-- GROUP BY action
-- ORDER BY count DESC;

-- ============================================
-- SUCCESS! 🎉
-- ============================================
-- Audit logging table created and ready.
-- All key actions will now be tracked with full traceability.
