-- Retain refresh-token family identity across rotated token rows.
ALTER TABLE auth_sessions ADD COLUMN family_id TEXT;
UPDATE auth_sessions SET family_id = COALESCE(session_id, 'legacy:' || id)
WHERE family_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_auth_sessions_family_id ON auth_sessions(family_id);
