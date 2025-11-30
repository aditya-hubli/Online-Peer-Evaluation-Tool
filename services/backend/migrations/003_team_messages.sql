-- OPETSE-18: Team Chat Feature
-- Create team_messages table for team communication

CREATE TABLE IF NOT EXISTS team_messages (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_team_messages_team_id ON team_messages(team_id);
CREATE INDEX IF NOT EXISTS idx_team_messages_sender_id ON team_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_team_messages_created_at ON team_messages(created_at DESC);

-- Add RLS policies
ALTER TABLE team_messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view messages from their teams
CREATE POLICY team_messages_select_policy ON team_messages
    FOR SELECT
    USING (
        team_id IN (
            SELECT team_id FROM team_members WHERE user_id = auth.uid()
        )
    );

-- Policy: Team members can insert messages
CREATE POLICY team_messages_insert_policy ON team_messages
    FOR INSERT
    WITH CHECK (
        sender_id = auth.uid() AND
        team_id IN (
            SELECT team_id FROM team_members WHERE user_id = auth.uid()
        )
    );

-- Policy: Users can only delete their own messages
CREATE POLICY team_messages_delete_policy ON team_messages
    FOR DELETE
    USING (sender_id = auth.uid());

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_team_messages_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER team_messages_updated_at
    BEFORE UPDATE ON team_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_team_messages_updated_at();

COMMENT ON TABLE team_messages IS 'OPETSE-18: Stores team chat messages for student collaboration';
COMMENT ON COLUMN team_messages.team_id IS 'Foreign key to teams table';
COMMENT ON COLUMN team_messages.sender_id IS 'Foreign key to users table (message author)';
COMMENT ON COLUMN team_messages.message IS 'Chat message content';
COMMENT ON COLUMN team_messages.created_at IS 'Message creation timestamp (UTC)';
COMMENT ON COLUMN team_messages.updated_at IS 'Message last update timestamp (UTC)';
