-- Research Hub tables use the application's integer user IDs.

CREATE TABLE IF NOT EXISTS research_projects (
    id UUID PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_notes (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_bookmarks (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_citations (
    id UUID PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS idx_research_projects_owner ON research_projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_research_projects_updated ON research_projects(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_notes_project ON research_notes(project_id);
CREATE INDEX IF NOT EXISTS idx_research_notes_author ON research_notes(author_id);
CREATE INDEX IF NOT EXISTS idx_research_bookmarks_project ON research_bookmarks(project_id);
CREATE INDEX IF NOT EXISTS idx_research_citations_project ON research_citations(project_id);
CREATE INDEX IF NOT EXISTS idx_research_citations_note ON research_citations(note_id);
