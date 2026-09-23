-- Search Intelligence Enhancement Migration
-- Adds support for advanced search features: history, synonyms, entities, personalization, facets

-- Search history tracking
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    normalized_query TEXT,
    search_type VARCHAR(50),
    filters JSONB,
    results_count INTEGER,
    clicked_results JSONB,
    intent VARCHAR(50),
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at);
CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query);

-- Synonyms table for query expansion
CREATE TABLE IF NOT EXISTS synonyms (
    id SERIAL PRIMARY KEY,
    term VARCHAR(255) NOT NULL,
    synonym VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(term, synonym, language)
);

CREATE INDEX IF NOT EXISTS idx_synonyms_term ON synonyms(term);
CREATE INDEX IF NOT EXISTS idx_synonyms_language ON synonyms(language);

-- Entities table for entity recognition
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    entity_value TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entities_user_id ON entities(user_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_value ON entities(entity_value);

-- Personalization table for user preferences
CREATE TABLE IF NOT EXISTS personalization (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    interests JSONB,
    preferred_categories JSONB,
    search_preferences JSONB,
    ranking_weights JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_personalization_user_id ON personalization(user_id);

-- Search facets table for faceted search
CREATE TABLE IF NOT EXISTS search_facets (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    facet_name VARCHAR(100) NOT NULL,
    facet_value VARCHAR(255) NOT NULL,
    count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(query_hash, facet_name, facet_value)
);

CREATE INDEX IF NOT EXISTS idx_search_facets_query_hash ON search_facets(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_facets_name ON search_facets(facet_name);

-- Search quality metrics table
CREATE TABLE IF NOT EXISTS search_quality_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    search_type VARCHAR(50),
    precision_at_5 FLOAT,
    precision_at_10 FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    mrr FLOAT,
    ndcg FLOAT,
    click_through_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_quality_user_id ON search_quality_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_search_quality_created_at ON search_quality_metrics(created_at);

-- Insert default synonyms
INSERT INTO synonyms (term, synonym, language) VALUES
    ('car', 'automobile', 'en'),
    ('car', 'vehicle', 'en'),
    ('phone', 'mobile', 'en'),
    ('phone', 'smartphone', 'en'),
    ('laptop', 'notebook', 'en'),
    ('laptop', 'computer', 'en'),
    ('buy', 'purchase', 'en'),
    ('cheap', 'affordable', 'en'),
    ('fast', 'quick', 'en'),
    ('big', 'large', 'en'),
    ('small', 'tiny', 'en'),
    ('happy', 'joyful', 'en'),
    ('sad', 'unhappy', 'en'),
    ('important', 'significant', 'en'),
    ('help', 'assist', 'en')
ON CONFLICT DO NOTHING;

-- Insert default entities
INSERT INTO entities (entity_type, entity_value, frequency) VALUES
    ('technology', 'python', 10),
    ('technology', 'javascript', 10),
    ('technology', 'react', 8),
    ('technology', 'fastapi', 7),
    ('technology', 'postgresql', 7),
    ('technology', 'docker', 8),
    ('technology', 'kubernetes', 6),
    ('technology', 'redis', 6),
    ('technology', 'elasticsearch', 5),
    ('technology', 'mongodb', 5)
ON CONFLICT DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_personalization_updated_at BEFORE UPDATE ON personalization
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_search_facets_updated_at BEFORE UPDATE ON search_facets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to increment entity frequency
CREATE OR REPLACE FUNCTION increment_entity_frequency(
    p_user_id INTEGER,
    p_entity_type VARCHAR(100),
    p_entity_value TEXT
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO entities (user_id, entity_type, entity_value, frequency, last_seen)
    VALUES (p_user_id, p_entity_type, p_entity_value, 1, CURRENT_TIMESTAMP)
    ON CONFLICT DO NOTHING;
    
    UPDATE entities 
    SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id 
    AND entity_type = p_entity_type 
    AND entity_value = p_entity_value;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON search_history TO nebula;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON synonyms TO nebula;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON entities TO nebula;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON personalization TO nebula;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON search_facets TO nebula;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON search_quality_metrics TO nebula;
-- GRANT USAGE, SELECT ON SEQUENCE search_history_id_seq TO nebula;
-- GRANT USAGE, SELECT ON SEQUENCE synonyms_id_seq TO nebula;
-- GRANT USAGE, SELECT ON SEQUENCE entities_id_seq TO nebula;
-- GRANT USAGE, SELECT ON SEQUENCE personalization_id_seq TO nebula;
-- GRANT USAGE, SELECT ON SEQUENCE search_facets_id_seq TO nebula;
-- GRANT USAGE, SELECT ON SEQUENCE search_quality_metrics_id_seq TO nebula;