-- Research Hub Migration
-- Creates tables for projects, notes, bookmarks, and citations

-- Create research_projects table
CREATE TABLE IF NOT EXISTS research_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create research_notes table
CREATE TABLE IF NOT EXISTS research_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create research_bookmarks table
CREATE TABLE IF NOT EXISTS research_bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create research_citations table
CREATE TABLE IF NOT EXISTS research_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    note_id UUID REFERENCES research_notes(id) ON DELETE SET NULL,
    source_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    authors JSONB NOT NULL DEFAULT '[]',
    publication_date TIMESTAMP,
    url TEXT,
    quote TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_research_projects_owner ON research_projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_research_projects_updated ON research_projects(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_notes_project ON research_notes(project_id);
CREATE INDEX IF NOT EXISTS idx_research_notes_author ON research_notes(author_id);
CREATE INDEX IF NOT EXISTS idx_research_bookmarks_project ON research_bookmarks(project_id);
CREATE INDEX IF NOT EXISTS idx_research_citations_project ON research_citations(project_id);
CREATE INDEX IF NOT EXISTS idx_research_citations_note ON research_citations(note_id);

-- Create triggers to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_research_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_research_projects_updated_at
    BEFORE UPDATE ON research_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_research_updated_at();

CREATE TRIGGER update_research_notes_updated_at
    BEFORE UPDATE ON research_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_research_updated_at();

-- Add RLS (Row Level Security) policies
ALTER TABLE research_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_citations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own projects
CREATE POLICY "Users can view own projects" ON research_projects
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can create own projects" ON research_projects
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own projects" ON research_projects
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own projects" ON research_projects
    FOR DELETE USING (auth.uid() = owner_id);

-- Policy: Users can only see notes from their projects
CREATE POLICY "Users can view notes from own projects" ON research_notes
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_notes.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can create notes in own projects" ON research_notes
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_notes.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update notes in own projects" ON research_notes
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_notes.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete notes in own projects" ON research_notes
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_notes.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

-- Policy: Users can only see bookmarks from their projects
CREATE POLICY "Users can view bookmarks from own projects" ON research_bookmarks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_bookmarks.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can create bookmarks in own projects" ON research_bookmarks
    FOR INSERT WITH CHECK (
        auth.uid() = user_id
        AND EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_bookmarks.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete bookmarks from own projects" ON research_bookmarks
    FOR DELETE USING (
        auth.uid() = user_id
        AND EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_bookmarks.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

-- Policy: Users can only see citations from their projects
CREATE POLICY "Users can view citations from own projects" ON research_citations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_citations.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can create citations in own projects" ON research_citations
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_citations.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete citations from own projects" ON research_citations
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM research_projects
            WHERE research_projects.id = research_citations.project_id
            AND research_projects.owner_id = auth.uid()
        )
    );