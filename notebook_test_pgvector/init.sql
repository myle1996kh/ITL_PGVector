-- Initialization script for pgvector test database
-- This runs automatically when the Docker container starts for the first time

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension enabled successfully';
END
$$;

-- Optional: Create test table to verify vector operations work
CREATE TABLE IF NOT EXISTS _pgvector_test (
    id SERIAL PRIMARY KEY,
    embedding vector(3)
);

INSERT INTO _pgvector_test (embedding) VALUES
    ('[1,2,3]'),
    ('[4,5,6]'),
    ('[7,8,9]');

-- Test vector distance calculation
DO $$
DECLARE
    test_result RECORD;
BEGIN
    SELECT * INTO test_result
    FROM _pgvector_test
    ORDER BY embedding <-> '[3,3,3]'
    LIMIT 1;

    RAISE NOTICE 'Vector similarity test passed. Closest vector ID: %', test_result.id;
END
$$;

-- Cleanup test table
DROP TABLE IF EXISTS _pgvector_test;

-- Log success
SELECT
    extname as extension_name,
    extversion as version
FROM pg_extension
WHERE extname = 'vector';
