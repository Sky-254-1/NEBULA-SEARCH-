-- pgvector extension and vector columns (PostgreSQL only)

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add vector column to documents table for embeddings
ALTER TABLE documents ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create function for hybrid search combining full-text and vector similarity
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    title TEXT,
    content TEXT,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        d.id,
        d.title,
        d.content,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE d.embedding IS NOT NULL
      AND (1 - (d.embedding <=> query_embedding)) >= match_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
$$;