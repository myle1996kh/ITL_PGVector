# pgvector Migration Plan - Replace ChromaDB with PostgreSQL Vector Extension

**Document Version**: 1.0
**Date Created**: 2025-11-03
**Status**: Planning / Ready for Implementation
**Estimated Effort**: 4-6 hours

---

## Executive Summary

**Objective**: Migrate RAG (Retrieval-Augmented Generation) functionality from ChromaDB to pgvector (PostgreSQL extension) to simplify infrastructure and leverage existing PostgreSQL database.

**Benefits**:
- ✅ **Unified Database**: One database instead of two services
- ✅ **Reduced Complexity**: No separate ChromaDB HTTP service on port 8001
- ✅ **ACID Transactions**: Strong consistency for document operations
- ✅ **Multi-Tenant Security**: Leverage existing PostgreSQL tenant isolation
- ✅ **Simplified Deployment**: One docker-compose service fewer
- ✅ **Better Integration**: SQL joins between vectors and relational data

**Trade-offs**:
- ⚠️ Performance degrades beyond 5M vectors (acceptable for current scale)
- ⚠️ Requires explicit embedding generation (ChromaDB auto-generates)
- ⚠️ Index build times slightly longer for large datasets

**Recommendation**: **Proceed with migration** - Your use case is ideal for pgvector.

---

## Current vs Future Architecture

### Current Architecture (ChromaDB)
```
FastAPI Application
    ↓
RAGService (rag_service.py)
    ↓
ChromaDB HTTP Client (port 8001)
    ↓
ChromaDB Docker Container
    ↓
Vector Storage + Embedding Generation
```

### Future Architecture (pgvector)
```
FastAPI Application
    ↓
RAGService (rag_service.py)
    ↓
PostgreSQL Connection (existing)
    ↓
pgvector Extension
    ↓
documents table with vector columns
```

**Eliminated**: ChromaDB HTTP service, separate port, separate backup/monitoring

---

## pgvector Overview

### What is pgvector?

PostgreSQL extension that adds vector similarity search:
- **Vector Data Type**: `vector(1536)` for storing embeddings
- **Distance Operators**:
  - `<=>` Cosine distance (best for normalized embeddings)
  - `<->` L2 distance (Euclidean)
  - `<#>` Inner product
- **Index Types**:
  - **HNSW**: Better query performance (~1.5ms), higher memory
  - **IVFFlat**: Faster builds (~15s), lower memory
- **Performance**: Excellent for <5M vectors, good for your scale

### Key Advantages

| Feature | ChromaDB | pgvector |
|---------|----------|----------|
| **Infrastructure** | Separate service | PostgreSQL extension |
| **Data Consistency** | Eventual | ACID transactions |
| **Backup** | Separate process | PostgreSQL backup |
| **Tenant Isolation** | Collection-based | SQL WHERE clause |
| **Complex Queries** | Limited | Full SQL power |
| **Operational Cost** | High (2 services) | Low (1 service) |
| **Your Use Case** | Over-engineered | Perfect fit |

---

## Migration Steps

### Phase 1: Database Schema (30 minutes)

#### Step 1.1: Install pgvector Extension
```bash
# Already installed in PostgreSQL 15+, just enable
```

#### Step 1.2: Create Migration Script
**File**: `backend/alembic/versions/20251103_add_pgvector.py`

```python
"""Add pgvector extension and documents table."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector


def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('metadata', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    # Create indexes
    op.create_index('idx_documents_tenant', 'documents', ['tenant_id'])

    # Create HNSW vector index for fast similarity search
    op.execute("""
        CREATE INDEX idx_documents_embedding
        ON documents USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade():
    op.drop_table('documents')
    op.execute('DROP EXTENSION IF EXISTS vector CASCADE')
```

#### Step 1.3: Run Migration
```bash
cd backend
alembic upgrade head
```

**Verification**:
```sql
-- Check extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check table
\d documents

-- Check index
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'documents';
```

---

### Phase 2: Update Dependencies (10 minutes)

#### Step 2.1: Update requirements.txt
```bash
# Add to backend/requirements.txt
pgvector>=0.3.0

# Optional: Remove if no longer needed
# chromadb>=0.4.0
```

#### Step 2.2: Install Dependencies
```bash
cd backend
pip install pgvector
```

---

### Phase 3: Refactor RAG Service (60 minutes)

#### Step 3.1: Backup Current File
```bash
cp backend/src/services/rag_service.py backend/src/services/rag_service.chromadb.backup.py
```

#### Step 3.2: Rewrite RAG Service
**File**: `backend/src/services/rag_service.py`

**Key Changes**:
1. Remove ChromaDB HTTP client
2. Use PostgreSQL connection (existing SQLAlchemy session)
3. Query `documents` table instead of ChromaDB collections
4. Use pgvector operators (`<=>` for cosine similarity)
5. Require pre-generated embeddings (no auto-generation)

**Core Query Pattern**:
```python
# Old (ChromaDB)
results = collection.query(
    query_texts=[query],
    n_results=top_k
)

# New (pgvector)
results = db.execute(text("""
    SELECT id, content, metadata,
           embedding <=> :query_embedding as distance
    FROM documents
    WHERE tenant_id = :tenant_id
    ORDER BY embedding <=> :query_embedding
    LIMIT :top_k
"""), {"tenant_id": tenant_id, "query_embedding": embedding, "top_k": top_k})
```

**Full Implementation**: See research report above for complete code.

---

### Phase 4: Refactor RAG Tool (45 minutes)

#### Step 4.1: Update Tool Configuration
**File**: `backend/src/tools/rag.py`

**Key Changes**:
1. Remove ChromaDB client initialization
2. Use PostgreSQL connection from `SessionLocal`
3. Update `_execute()` to use SQL queries
4. Add `query_embedding` parameter to input schema
5. Remove `collection_name` parameter (use tenant_id)

**Input Schema Change**:
```json
// Old (ChromaDB)
{
  "query": {"type": "string", "description": "Search query"}
}

// New (pgvector)
{
  "query": {"type": "string", "description": "Search query text"},
  "query_embedding": {"type": "array", "description": "Query embedding vector (1536 dims)"}
}
```

**Execution Change**:
```python
# Old: ChromaDB auto-generates embeddings
def _execute(self, query: str):
    results = self.collection.query(query_texts=[query])

# New: Requires pre-generated embedding
def _execute(self, query: str, query_embedding: List[float]):
    results = db.execute(text("SELECT ... WHERE embedding <=> :emb"),
                         {"emb": query_embedding})
```

---

### Phase 5: Add Embedding Generation (30 minutes)

Since pgvector doesn't auto-generate embeddings, add embedding service:

#### Step 5.1: Create Embedding Service
**File**: `backend/src/services/embedding_service.py`

```python
"""Embedding generation service."""
from typing import List
from sentence_transformers import SentenceTransformer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model."""
        self.model = SentenceTransformer(model_name)
        logger.info("embedding_service_initialized", model=model_name)

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        embedding = self.model.encode(text)
        return embedding.tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts)
        return [emb.tolist() for emb in embeddings]


# Singleton
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
```

#### Step 5.2: Update RAG Service to Use Embeddings
```python
from src.services.embedding_service import get_embedding_service

def ingest_documents(self, tenant_id, documents, metadatas=None):
    # Generate embeddings
    embedding_service = get_embedding_service()
    embeddings = embedding_service.generate_embeddings(documents)

    # Insert with embeddings
    # ... (see full implementation above)
```

#### Step 5.3: Update RAG Tool to Generate Embedding
```python
def _execute(self, query: str, **kwargs):
    # Generate query embedding
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.generate_embedding(query)

    # Search with embedding
    # ... (see full implementation above)
```

---

### Phase 6: Data Migration (60 minutes)

#### Step 6.1: Create Migration Script
**File**: `backend/scripts/migrate_chromadb_to_pgvector.py`

```python
"""Migrate existing ChromaDB data to pgvector."""
import chromadb
from sqlalchemy import text
from src.config import SessionLocal

def migrate_tenant_collection(tenant_id: str):
    # Get ChromaDB data
    chroma_client = chromadb.HttpClient(host="localhost", port=8001)
    collection_name = f"tenant_{tenant_id.replace('-', '')}_knowledge"
    collection = chroma_client.get_collection(collection_name)

    # Fetch all documents
    data = collection.get(include=["documents", "embeddings", "metadatas"])

    # Insert into PostgreSQL
    with SessionLocal() as db:
        for i, doc_id in enumerate(data["ids"]):
            db.execute(text("""
                INSERT INTO documents (id, tenant_id, content, embedding, metadata)
                VALUES (:id, :tenant_id, :content, :embedding, :metadata)
            """), {
                "id": doc_id,
                "tenant_id": tenant_id,
                "content": data["documents"][i],
                "embedding": data["embeddings"][i],
                "metadata": data["metadatas"][i] or {},
            })
        db.commit()

# Run for all tenants
migrate_all_tenants()
```

#### Step 6.2: Run Migration
```bash
cd backend
python scripts/migrate_chromadb_to_pgvector.py
```

#### Step 6.3: Verify Migration
```sql
-- Check document counts match
SELECT tenant_id, COUNT(*) as doc_count
FROM documents
GROUP BY tenant_id;

-- Compare with ChromaDB collection counts
```

---

### Phase 7: Update Configuration (15 minutes)

#### Step 7.1: Update docker-compose.yml
```yaml
# Remove or comment out ChromaDB service
# chromadb:
#   image: chromadb/chroma:latest
#   ports:
#     - "8001:8000"
#   volumes:
#     - chromadb_data:/chroma/chroma

# Also remove from volumes section
# volumes:
#   chromadb_data:
```

#### Step 7.2: Update .env
```bash
# Remove (if present)
# CHROMA_URL=http://localhost:8001
# CHROMADB_HOST=localhost
# CHROMADB_PORT=8001

# No new env vars needed - using existing DATABASE_URL
```

#### Step 7.3: Update config.py
```python
# Remove ChromaDB config
# CHROMA_URL: str = Field(default="http://localhost:8001")

# pgvector uses existing DATABASE_URL
```

---

### Phase 8: Testing (60 minutes)

#### Step 8.1: Unit Tests
**File**: `backend/tests/unit/test_pgvector_rag.py`

```python
"""Tests for pgvector RAG service."""
import pytest
from src.services.rag_service import get_rag_service
from src.services.embedding_service import get_embedding_service


def test_ingest_and_query():
    """Test document ingestion and retrieval."""
    rag = get_rag_service()
    embedding = get_embedding_service()

    tenant_id = "test-tenant-uuid"
    documents = ["Test doc 1", "Test doc 2"]

    # Ingest
    result = rag.ingest_documents(
        tenant_id=tenant_id,
        documents=documents,
    )
    assert result["success"]

    # Query
    query_emb = embedding.generate_embedding("Test query")
    results = rag.query_knowledge_base(
        tenant_id=tenant_id,
        query_embedding=query_emb,
        top_k=5,
    )

    assert results["success"]
    assert len(results["documents"]) > 0


def test_tenant_isolation():
    """Test multi-tenant isolation."""
    rag = get_rag_service()

    # Insert for tenant A
    rag.ingest_documents("tenant-a", ["Doc A"])

    # Insert for tenant B
    rag.ingest_documents("tenant-b", ["Doc B"])

    # Query tenant A - should not see tenant B docs
    results_a = rag.query_knowledge_base("tenant-a", embedding, top_k=10)

    assert all(doc["metadata"]["tenant_id"] == "tenant-a"
               for doc in results_a["documents"])
```

#### Step 8.2: Integration Tests
```bash
# Run existing RAG tool tests
pytest tests/unit/test_rag_tool.py -v

# Run end-to-end chat tests with RAG
pytest tests/integration/test_chat_with_rag.py -v
```

#### Step 8.3: Performance Testing
```python
# Test query latency
import time

query_embedding = embedding.generate_embedding("test query")

start = time.time()
results = rag.query_knowledge_base(tenant_id, query_embedding, top_k=5)
latency = time.time() - start

print(f"Query latency: {latency*1000:.2f}ms")
# Target: <50ms for <100K docs, <150ms for <1M docs
```

---

### Phase 9: Documentation Updates (30 minutes)

#### Update Documentation Files:

1. **`Documentation/02_SYSTEM_ARCHITECTURE.md`**
   - Update "Tool Loading System" section
   - Change ChromaDB references to pgvector
   - Update architecture diagram

2. **`Documentation/04_DATABASE_SCHEMA_ERD.md`**
   - Add `documents` table to ERD
   - Document vector column and indexes

3. **`Documentation/05_API_REFERENCE_AND_GUIDES.md`**
   - Update RAG tool examples
   - Add embedding generation step

4. **`README.md`**
   - Update technology stack (remove ChromaDB, add pgvector)
   - Update docker-compose instructions

---

### Phase 10: Deployment (30 minutes)

#### Step 10.1: Staging Deployment
```bash
# 1. Deploy code changes
git checkout -b feature/pgvector-migration
git add .
git commit -m "Migrate RAG from ChromaDB to pgvector"
git push origin feature/pgvector-migration

# 2. Run database migration on staging
alembic upgrade head

# 3. Run data migration script
python scripts/migrate_chromadb_to_pgvector.py

# 4. Test RAG functionality
curl -X POST http://staging-api/test/chat \
  -d '{"message": "What is our return policy?"}'

# 5. Verify ChromaDB data migrated
SELECT COUNT(*) FROM documents;
```

#### Step 10.2: Production Deployment
```bash
# 1. Backup PostgreSQL
pg_dump -h localhost -U postgres chatbot_db > backup_before_pgvector.sql

# 2. Backup ChromaDB (if needed to rollback)
# (Document ChromaDB backup procedure)

# 3. Deploy to production
git checkout main
git merge feature/pgvector-migration
git push origin main

# 4. Run migration
alembic upgrade head

# 5. Migrate data
python scripts/migrate_chromadb_to_pgvector.py

# 6. Smoke test
# Test RAG queries for all tenants

# 7. Stop ChromaDB service (after verification)
docker-compose stop chromadb
# Keep for 1 week before removing permanently
```

---

## Performance Tuning

### Index Optimization

**HNSW Parameters** (current defaults):
```sql
-- Good for most use cases
CREATE INDEX idx_documents_embedding
ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Query-time tuning
SET hnsw.ef_search = 40;  -- Higher = better recall, slower
```

**If memory constrained, switch to IVFFlat**:
```sql
-- Drop HNSW
DROP INDEX idx_documents_embedding;

-- Create IVFFlat
CREATE INDEX idx_documents_embedding
ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1000);  -- Adjust based on document count

-- Query-time tuning
SET ivfflat.probes = 10;  -- Higher = better recall, slower
```

### Query Optimization

**Add distance threshold** to reduce irrelevant results:
```sql
SELECT * FROM documents
WHERE tenant_id = :tenant_id
  AND (embedding <=> :query) < 0.5  -- Distance threshold
ORDER BY embedding <=> :query
LIMIT 5;
```

**Use CTE for complex filters**:
```sql
WITH relevant_docs AS (
    SELECT id, content, embedding <=> :query as distance
    FROM documents
    WHERE tenant_id = :tenant_id
    ORDER BY embedding <=> :query
    LIMIT 20
)
SELECT * FROM relevant_docs
WHERE distance < 0.5
  AND metadata->>'category' = 'support'
LIMIT 5;
```

### Monitoring Queries

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename = 'documents';

-- Check query performance
EXPLAIN ANALYZE
SELECT * FROM documents
WHERE tenant_id = :tenant_id
ORDER BY embedding <=> :query
LIMIT 5;

-- Monitor index size
SELECT pg_size_pretty(pg_relation_size('idx_documents_embedding'));
```

---

## Rollback Plan

If issues arise, rollback procedure:

### Option 1: Keep ChromaDB Running (Recommended for 1 week)
```bash
# Don't stop ChromaDB immediately
# Keep both systems running in parallel

# Revert code changes
git revert <commit-hash>
git push

# Switch back to ChromaDB in config
# (restore rag_service.chromadb.backup.py)
```

### Option 2: Full Rollback
```bash
# 1. Restore code
git revert <commit-hash>

# 2. Rollback database migration
alembic downgrade -1

# 3. Restart ChromaDB
docker-compose up -d chromadb

# 4. Verify data in ChromaDB still intact
```

---

## Success Criteria

✅ **Phase 1 Complete**: documents table created with vector index
✅ **Phase 2 Complete**: pgvector dependency installed
✅ **Phase 3 Complete**: RAG service refactored, tests pass
✅ **Phase 4 Complete**: RAG tool refactored, tests pass
✅ **Phase 5 Complete**: Embedding service integrated
✅ **Phase 6 Complete**: All ChromaDB data migrated, counts match
✅ **Phase 7 Complete**: Configuration updated, ChromaDB removed
✅ **Phase 8 Complete**: All tests pass, performance acceptable
✅ **Phase 9 Complete**: Documentation updated
✅ **Phase 10 Complete**: Deployed to production, verified

**Performance Targets**:
- Query latency: <50ms for <100K docs
- Index build time: <1 minute for <100K docs
- Memory usage: <2GB for vector indexes

**Verification**:
- All existing RAG queries return correct results
- Multi-tenant isolation maintained
- No ChromaDB dependencies remain in codebase
- Docker Compose simplified (one fewer service)

---

## Timeline Estimate

| Phase | Estimated Time | Can Parallelize |
|-------|---------------|-----------------|
| Phase 1: Database Schema | 30 min | No |
| Phase 2: Dependencies | 10 min | No |
| Phase 3: RAG Service | 60 min | No |
| Phase 4: RAG Tool | 45 min | With Phase 3 |
| Phase 5: Embeddings | 30 min | With Phase 3/4 |
| Phase 6: Data Migration | 60 min | After Phase 1-5 |
| Phase 7: Configuration | 15 min | With Phase 3-5 |
| Phase 8: Testing | 60 min | After all phases |
| Phase 9: Documentation | 30 min | Parallel anytime |
| Phase 10: Deployment | 30 min | After testing |

**Sequential (worst case)**: 6 hours
**Parallel (optimized)**: **4 hours**

---

## Next Steps

### Immediate Actions
1. ✅ Review this plan with team
2. ✅ Schedule migration window (low-traffic period)
3. ✅ Create feature branch: `feature/pgvector-migration`
4. ✅ Backup current ChromaDB data
5. ✅ Start with Phase 1 (database schema)

### Go/No-Go Decision Points

**Before Phase 6 (Data Migration)**:
- All unit tests pass
- Performance tests show acceptable latency
- Code review completed

**Before Phase 10 (Production Deployment)**:
- Staging fully tested and verified
- Data migration script tested on staging
- Rollback plan documented and reviewed
- Team trained on new architecture

---

## References

**Internal Documentation**:
- [System Architecture](02_SYSTEM_ARCHITECTURE.md)
- [Database Schema](04_DATABASE_SCHEMA_ERD.md)
- [API Reference](05_API_REFERENCE_AND_GUIDES.md)

**External Resources**:
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [pgvector Documentation](https://github.com/pgvector/pgvector-python)
- [PostgreSQL Extension Docs](https://www.postgresql.org/docs/current/extend.html)

**Files to Modify**:
- `backend/src/services/rag_service.py` (major refactor)
- `backend/src/tools/rag.py` (major refactor)
- `backend/requirements.txt` (add pgvector)
- `backend/docker-compose.yml` (remove chromadb)
- `backend/alembic/versions/` (new migration)
- `backend/tests/unit/test_rag*.py` (update tests)

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: 2025-11-03
**Prepared By**: AI Technical Documentation Team
**Approved By**: Pending team review
