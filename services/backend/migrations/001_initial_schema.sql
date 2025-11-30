-- ============================================
-- PEER EVALUATION SYSTEM - DATABASE SETUP
-- ============================================
-- Complete database schema for PESU Online Peer Evaluation Tool
-- Run this SQL in your Supabase SQL Editor
-- Dashboard -> SQL Editor -> New Query -> Paste & Run
-- ============================================

-- ============================================
-- CLEAN UP: DROP ALL EXISTING TABLES
-- ============================================
DROP TABLE IF EXISTS team_messages CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS evaluation_scores CASCADE;
DROP TABLE IF EXISTS evaluations CASCADE;
DROP TABLE IF EXISTS form_criteria CASCADE;
DROP TABLE IF EXISTS evaluation_forms CASCADE;
DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- CREATE TABLES
-- ============================================

-- 1. CREATE USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'student',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. CREATE PROJECTS TABLE
CREATE TABLE IF NOT EXISTS projects (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_date DATE,
    end_date DATE,
    deadline TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_instructor ON projects(instructor_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_deadline ON projects(deadline);

-- 3. CREATE TEAMS TABLE
CREATE TABLE IF NOT EXISTS teams (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teams_project ON teams(project_id);

-- 4. CREATE TEAM_MEMBERS TABLE (Many-to-Many relationship)
CREATE TABLE IF NOT EXISTS team_members (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(team_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id);

-- 5. CREATE EVALUATION_FORMS TABLE (Rubrics)
CREATE TABLE IF NOT EXISTS evaluation_forms (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_template BOOLEAN DEFAULT FALSE,
    template_name VARCHAR(255),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluation_forms_project ON evaluation_forms(project_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_forms_template ON evaluation_forms(is_template);

-- 6. CREATE FORM_CRITERIA TABLE (Rubric criteria with weights)
CREATE TABLE IF NOT EXISTS form_criteria (
    id BIGSERIAL PRIMARY KEY,
    form_id BIGINT NOT NULL REFERENCES evaluation_forms(id) ON DELETE CASCADE,
    criterion_name VARCHAR(255) NOT NULL,
    description TEXT,
    max_score INTEGER NOT NULL DEFAULT 5,
    weight DECIMAL(3, 2) DEFAULT 1.0,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_form_criteria_form ON form_criteria(form_id);

-- 7. CREATE EVALUATIONS TABLE
CREATE TABLE IF NOT EXISTS evaluations (
    id BIGSERIAL PRIMARY KEY,
    form_id BIGINT NOT NULL REFERENCES evaluation_forms(id) ON DELETE CASCADE,
    evaluator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    evaluatee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    total_score DECIMAL(10, 2),
    weighted_score DECIMAL(10, 2),
    comments TEXT,
    is_anonymous BOOLEAN DEFAULT TRUE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    late_submission BOOLEAN DEFAULT FALSE,
    UNIQUE(form_id, evaluator_id, evaluatee_id)
);

CREATE INDEX IF NOT EXISTS idx_evaluations_form ON evaluations(form_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_evaluator ON evaluations(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_evaluatee ON evaluations(evaluatee_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_team ON evaluations(team_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_submitted ON evaluations(submitted_at);

-- 8. CREATE EVALUATION_SCORES TABLE
CREATE TABLE IF NOT EXISTS evaluation_scores (
    id BIGSERIAL PRIMARY KEY,
    evaluation_id BIGINT NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    criterion_id BIGINT NOT NULL REFERENCES form_criteria(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(evaluation_id, criterion_id)
);

CREATE INDEX IF NOT EXISTS idx_evaluation_scores_evaluation ON evaluation_scores(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_scores_criterion ON evaluation_scores(criterion_id);

-- 9. CREATE AUDIT_LOGS TABLE (OPETSE-15)
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id BIGINT,
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- 10. CREATE TEAM_MESSAGES TABLE (OPETSE-18)
CREATE TABLE IF NOT EXISTS team_messages (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

CREATE INDEX IF NOT EXISTS idx_team_messages_team_id ON team_messages(team_id);
CREATE INDEX IF NOT EXISTS idx_team_messages_sender_id ON team_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_team_messages_created_at ON team_messages(created_at DESC);

-- ============================================
-- ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE form_criteria ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_messages ENABLE ROW LEVEL SECURITY;

-- ============================================
-- CREATE RLS POLICIES
-- ============================================

-- Users policies
CREATE POLICY users_select_policy ON users
    FOR SELECT
    USING (true);  -- All authenticated users can view users

CREATE POLICY users_update_policy ON users
    FOR UPDATE
    USING (id = auth.uid());  -- Users can only update themselves

-- Projects policies
CREATE POLICY projects_select_policy ON projects
    FOR SELECT
    USING (true);

CREATE POLICY projects_insert_policy ON projects
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users WHERE id = auth.uid() AND role = 'instructor'
        )
    );

CREATE POLICY projects_update_policy ON projects
    FOR UPDATE
    USING (instructor_id = auth.uid());

-- Teams policies
CREATE POLICY teams_select_policy ON teams
    FOR SELECT
    USING (true);

-- Team members policies
CREATE POLICY team_members_select_policy ON team_members
    FOR SELECT
    USING (true);

-- Evaluation forms policies
CREATE POLICY evaluation_forms_select_policy ON evaluation_forms
    FOR SELECT
    USING (true);

-- Evaluations policies
CREATE POLICY evaluations_select_policy ON evaluations
    FOR SELECT
    USING (
        evaluator_id = auth.uid() OR
        evaluatee_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM projects p
            JOIN evaluation_forms ef ON ef.project_id = p.id
            WHERE ef.id = evaluations.form_id AND p.instructor_id = auth.uid()
        )
    );

CREATE POLICY evaluations_insert_policy ON evaluations
    FOR INSERT
    WITH CHECK (evaluator_id = auth.uid());

-- Team messages policies
CREATE POLICY team_messages_select_policy ON team_messages
    FOR SELECT
    USING (
        team_id IN (
            SELECT team_id FROM team_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY team_messages_insert_policy ON team_messages
    FOR INSERT
    WITH CHECK (
        sender_id = auth.uid() AND
        team_id IN (
            SELECT team_id FROM team_members WHERE user_id = auth.uid()
        )
    );

CREATE POLICY team_messages_delete_policy ON team_messages
    FOR DELETE
    USING (sender_id = auth.uid());

-- Audit logs policies (read-only for instructors)
CREATE POLICY audit_logs_select_policy ON audit_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE id = auth.uid() AND role = 'instructor'
        )
    );

-- ============================================
-- CREATE TRIGGERS
-- ============================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to tables
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER evaluation_forms_updated_at
    BEFORE UPDATE ON evaluation_forms
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER team_messages_updated_at
    BEFORE UPDATE ON team_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- TABLE COMMENTS
-- ============================================

COMMENT ON TABLE users IS 'User accounts with RBAC support';
COMMENT ON TABLE projects IS 'Evaluation projects created by instructors';
COMMENT ON TABLE teams IS 'Teams within projects';
COMMENT ON TABLE team_members IS 'Many-to-many relationship between teams and users';
COMMENT ON TABLE evaluation_forms IS 'Rubrics/forms for evaluations with template support';
COMMENT ON TABLE form_criteria IS 'Evaluation criteria with weighted scoring';
COMMENT ON TABLE evaluations IS 'Peer evaluation submissions';
COMMENT ON TABLE evaluation_scores IS 'Individual criterion scores for each evaluation';
COMMENT ON TABLE audit_logs IS 'OPETSE-15: System audit trail';
COMMENT ON TABLE team_messages IS 'OPETSE-18: Team chat messages';

-- ============================================
-- COMPLETE
-- ============================================

SELECT 'Database schema created successfully!' AS status;
