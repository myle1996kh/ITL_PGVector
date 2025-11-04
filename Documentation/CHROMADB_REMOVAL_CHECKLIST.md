# ChromaDB Complete Removal Checklist

**Document Version**: 1.0
**Date**: 2025-11-03
**Purpose**: Step-by-step guide to completely remove ChromaDB after pgvector migration

---

## Overview

This checklist ensures complete removal of ChromaDB from your project after successfully migrating to pgvector. Follow these steps **only after** pgvector migration is verified and tested.

**Prerequisites**:
- ✅ pgvector migration completed (all 10 phases)
- ✅ All tests passing with pgvector
- ✅ Production running on pgvector for at least 1 week
- ✅ No rollback needed

---

## Phase 1: Pre-Removal Verification (15 minutes)

### Step 1.1: Verify pgvector is Working

```bash
# Check documents table has data
psql -h localhost -U agenthub -d agenthub -c "SELECT COUNT(*) FROM documents;"

# Expected: Should show document count > 0 if you have RAG data

# Test RAG query via API
curl -X POST "http://localhost:8000/api/test-tenant-id/test/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is our return policy?", "user_id": "test"}'

# Expected: Should return RAG-based answer
```

### Step 1.2: Verify ChromaDB is No Longer Used

```bash
# Check application logs for ChromaDB connections
docker-compose logs backend | grep -i chroma

# Expected: No recent ChromaDB connection attempts

# Check if ChromaDB service is still running
docker-compose ps chromadb

# If still running, it's safe to proceed with removal
```

### Step 1.3: Final Data Backup (Just in Case)

```bash
# Export ChromaDB data as JSON backup (optional - for safety)
python backend/scripts/backup_chromadb_data.py

# Backup PostgreSQL documents table
pg_dump -h localhost -U agenthub -d agenthub -t documents > documents_backup.sql
```

---

## Phase 2: Code Cleanup (30 minutes)

### Step 2.1: Remove ChromaDB Dependencies

**File**: `backend/requirements.txt`

```bash
# Remove these lines:
# chromadb>=0.4.0
# chromadb-client>=0.4.0

# Or comment out:
# chromadb>=0.4.0  # Removed - migrated to pgvector
```

**Uninstall from environment**:
```bash
cd backend
source venv/Scripts/activate  # Windows
pip uninstall chromadb chromadb-client -y
```

### Step 2.2: Remove ChromaDB Imports

**Search for ChromaDB imports across codebase**:
```bash
cd backend
grep -r "import chromadb" src/
grep -r "from chromadb" src/
```

**Expected files with ChromaDB imports** (should be none if migration complete):
- ~~`src/services/rag_service.py`~~ (already refactored to pgvector)
- ~~`src/tools/rag.py`~~ (already refactored to pgvector)

**Action**: If any imports remain, remove them:
```python
# Remove these imports:
# import chromadb
# from chromadb.config import Settings as ChromaSettings
# from chromadb.utils import embedding_functions
```

### Step 2.3: Remove ChromaDB Configuration

**File**: `backend/src/config.py`

```python
# Remove or comment out ChromaDB settings
class Settings(BaseSettings):
    # ... other settings ...

    # REMOVE THESE:
    # CHROMA_URL: str = Field(default="http://localhost:8001")
    # CHROMADB_HOST: str = Field(default="localhost")
    # CHROMADB_PORT: int = Field(default=8001)
```

**File**: `backend/.env`

```bash
# Remove or comment out:
# CHROMA_URL=http://localhost:8001
# CHROMADB_HOST=localhost
# CHROMADB_PORT=8001
```

**File**: `backend/.env.example`

```bash
# Remove these example variables:
# CHROMA_URL=http://localhost:8001
# CHROMADB_HOST=localhost
# CHROMADB_PORT=8001
```

### Step 2.4: Remove Backup Files

```bash
cd backend/src/services

# If you created backup during migration:
rm -f rag_service.chromadb.backup.py

cd backend/src/tools
rm -f rag.chromadb.backup.py
```

---

## Phase 3: Docker & Infrastructure Cleanup (20 minutes)

### Step 3.1: Update docker-compose.yml

**File**: `backend/docker-compose.yml`

**Remove ChromaDB service**:
```yaml
# DELETE THIS ENTIRE SECTION:
# services:
#   chromadb:
#     image: chromadb/chroma:latest
#     container_name: chromadb
#     ports:
#       - "8001:8000"
#     volumes:
#       - chromadb_data:/chroma/chroma
#     environment:
#       - CHROMA_SERVER_HOST=0.0.0.0
#       - CHROMA_SERVER_HTTP_PORT=8000
#     networks:
#       - backend_network
```

**Remove volume definition**:
```yaml
# DELETE FROM VOLUMES SECTION:
# volumes:
#   chromadb_data:
#     driver: local
```

**Updated docker-compose.yml should only have**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    # ... postgres config ...

  redis:
    image: redis:7-alpine
    # ... redis config ...

# ChromaDB removed - using pgvector in PostgreSQL

volumes:
  postgres_data:
  redis_data:
```

### Step 3.2: Stop and Remove ChromaDB Container

```bash
# Stop ChromaDB service
docker-compose stop chromadb

# Remove container
docker-compose rm -f chromadb

# Verify it's gone
docker-compose ps

# Expected: Should NOT show chromadb in the list
```

### Step 3.3: Remove ChromaDB Docker Volume

**⚠️ WARNING**: This permanently deletes ChromaDB data. Only proceed if pgvector migration verified.

```bash
# List volumes to confirm chromadb_data exists
docker volume ls | grep chromadb

# Remove the volume
docker volume rm backend_chromadb_data
# Or if volume name is different:
# docker volume rm itl_base_2810_chromadb_data

# Verify removal
docker volume ls | grep chromadb
# Expected: No results
```

### Step 3.4: Clean Up Docker Images

```bash
# Remove ChromaDB images to free disk space
docker images | grep chroma

# Remove the image(s)
docker rmi chromadb/chroma:latest
# Or all versions:
# docker rmi $(docker images | grep chromadb/chroma | awk '{print $3}')
```

---

## Phase 4: Remove ChromaDB-Specific Scripts (15 minutes)

### Step 4.1: Identify ChromaDB Scripts

```bash
cd backend

# Find scripts that use ChromaDB
grep -r "chromadb" scripts/
grep -r "chromadb" migrations/
```

### Step 4.2: Remove or Archive Scripts

**Files to remove/archive**:
```bash
# Migration script (keep for reference, but mark as obsolete)
mv scripts/migrate_chromadb_to_pgvector.py scripts/archive/

# Setup scripts (if any)
# mv migrations/setup_chromadb.py migrations/archive/

# Backup script (if created)
# mv scripts/backup_chromadb_data.py scripts/archive/

# Create archive directory if needed
mkdir -p scripts/archive
mkdir -p migrations/archive
```

**Alternative**: Add deprecation comments instead of deleting:
```python
# File: scripts/migrate_chromadb_to_pgvector.py
"""
DEPRECATED: This script was used for one-time migration from ChromaDB to pgvector.
Migration completed on: 2025-11-03
No longer needed - kept for historical reference only.
"""
```

---

## Phase 5: Update Documentation (30 minutes)

### Step 5.1: Update README.md

**File**: `backend/README.md`

**Remove ChromaDB references**:
```markdown
## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (with pgvector extension)
- Redis 7.x
~~- ChromaDB (optional, for RAG features)~~  <!-- REMOVE THIS LINE -->

## Quick Start

### 1. Setup Environment
...

### 2. Start Services with Docker Compose

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

~~ChromaDB service removed - now using pgvector in PostgreSQL~~
```

**Update technology stack**:
```markdown
## Technology Stack

### Data Storage
- **PostgreSQL 15+**: Primary database + vector search (pgvector)
- **SQLAlchemy 2.0+**: ORM with async support
- **Alembic**: Database migration management
- **Redis 7.x**: Configuration cache, session state
~~- **ChromaDB**: Vector database for RAG embeddings~~  <!-- REMOVE -->
+ **pgvector**: PostgreSQL extension for vector similarity search
```

### Step 5.2: Update System Architecture Docs

**File**: `Documentation/02_SYSTEM_ARCHITECTURE.md`

Search and replace ChromaDB references:

```bash
# Find all ChromaDB mentions
grep -n "ChromaDB" Documentation/02_SYSTEM_ARCHITECTURE.md

# Update architecture diagrams
# Change:
#   ┌─────────────┐
#   │  ChromaDB   │
#   │  (Vectors)  │
#   └─────────────┘

# To:
#   ┌─────────────┐
#   │ PostgreSQL  │
#   │ (pgvector)  │
#   └─────────────┘
```

**Update service layer description**:
```markdown
## Service Layer

### RAG Service (rag_service.py)
- Manages tenant knowledge bases using **pgvector**
- Stores document embeddings in PostgreSQL `documents` table
- Performs vector similarity search using pgvector indexes
~~- Manages ChromaDB collections~~
~~- Performs vector similarity search~~
```

### Step 5.3: Update Database Schema Docs

**File**: `Documentation/04_DATABASE_SCHEMA_ERD.md`

**Add documents table** (if not already added):
```markdown
### 14. documents (NEW - pgvector)
**Purpose**: Store document embeddings for RAG knowledge base

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_documents_tenant ON documents(tenant_id);
CREATE INDEX idx_documents_embedding ON documents
    USING hnsw (embedding vector_cosine_ops);
```
```

### Step 5.4: Update API Documentation

**File**: `Documentation/05_API_REFERENCE_AND_GUIDES.md`

**Update Knowledge Base section**:
```markdown
### POST /api/admin/knowledge/upload
**Purpose**: Upload documents to pgvector knowledge base
~~**Purpose**: Upload documents to ChromaDB for RAG~~

**Implementation**: Documents are embedded and stored in PostgreSQL `documents` table
~~**Implementation**: Documents are stored in ChromaDB collections~~
```

### Step 5.5: Update Quick Start Guide

**File**: `Documentation/13_QUICKSTART.md`

**Update Step 2**:
```markdown
## Step 2: Start Services (2 minutes)

```bash
# Start PostgreSQL and Redis with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                STATUS
# postgres            Up
# redis               Up
~~# chromadb            Up~~  <!-- REMOVE -->
```
```

### Step 5.6: Create Migration Completion Notice

**File**: `Documentation/CHROMADB_TO_PGVECTOR_MIGRATION_COMPLETE.md`

```markdown
# ChromaDB to pgvector Migration - COMPLETED

**Migration Date**: 2025-11-03
**Status**: ✅ Complete - ChromaDB fully removed

## Summary

The AgentHub Multi-Agent Chatbot Framework has been successfully migrated from ChromaDB to pgvector for vector similarity search.

### What Changed

**Before**:
- Separate ChromaDB HTTP service on port 8001
- ChromaDB collections for document storage
- Automatic embedding generation

**After**:
- pgvector extension in existing PostgreSQL database
- `documents` table with vector columns
- Explicit embedding generation via `EmbeddingService`

### Benefits Achieved

✅ **Simplified Infrastructure**: One database instead of two services
✅ **Reduced Complexity**: Removed ChromaDB dependency
✅ **Better Integration**: SQL joins between vectors and relational data
✅ **ACID Transactions**: Consistent document operations
✅ **Lower Costs**: Fewer services to run and maintain

### Breaking Changes

⚠️ **RAG Tool Input Schema Changed**:
- Old: `{"query": "search text"}`
- New: `{"query": "search text", "query_embedding": [0.1, 0.2, ...]}`

⚠️ **Embedding Generation Required**:
- Applications must generate embeddings before calling RAG APIs
- Use `EmbeddingService` or external embedding API

### Rollback Information

**ChromaDB Data**: Backed up on 2025-11-03 to `chromadb_backup_20251103.tar.gz`
**Rollback Window**: Expired (migration verified for 1+ weeks)

### Support

For questions about the migration or pgvector usage:
- See: [pgvector Migration Plan](PGVECTOR_MIGRATION_PLAN.md)
- See: [System Architecture](02_SYSTEM_ARCHITECTURE.md)
- See: [Database Schema](04_DATABASE_SCHEMA_ERD.md)
```

---

## Phase 6: Update Project Configuration Files (10 minutes)

### Step 6.1: Update .gitignore

**File**: `backend/.gitignore`

```bash
# Remove ChromaDB-specific ignores (if any):
# /chromadb/
# /chroma/
# chromadb.log
```

### Step 6.2: Update pyproject.toml or setup.py

If using `pyproject.toml`:

```toml
[tool.poetry.dependencies]
# ... other dependencies ...
pgvector = "^0.3.0"
# chromadb = "^0.4.0"  # REMOVED - migrated to pgvector
```

### Step 6.3: Update CI/CD Configuration

**File**: `.github/workflows/test.yml` (or similar)

```yaml
# Remove ChromaDB from CI services
services:
  postgres:
    image: postgres:15
    # ... postgres config ...

  redis:
    image: redis:7
    # ... redis config ...

  # chromadb:  # REMOVE THIS SERVICE
  #   image: chromadb/chroma:latest
  #   ports:
  #     - 8001:8000
```

---

## Phase 7: Final Verification (15 minutes)

### Step 7.1: Search for Remaining References

```bash
# Search entire project for "chroma" references
cd c:\Users\gensh\Downloads\ITL_Base_28.10

# Case-insensitive search
grep -ri "chroma" backend/src/
grep -ri "chroma" backend/tests/
grep -ri "chroma" Documentation/
grep -ri "chroma" backend/*.yml
grep -ri "chroma" backend/*.txt
grep -ri "chroma" backend/.env*

# Expected: Only results should be in:
# - Documentation/PGVECTOR_MIGRATION_PLAN.md (historical reference)
# - Documentation/CHROMADB_REMOVAL_CHECKLIST.md (this file)
# - scripts/archive/migrate_chromadb_to_pgvector.py (archived)
```

### Step 7.2: Verify Application Starts Clean

```bash
# Stop all services
docker-compose down

# Start services (ChromaDB should not be mentioned)
docker-compose up -d

# Check logs for ChromaDB errors
docker-compose logs backend | grep -i chroma

# Expected: No ChromaDB-related logs

# Test application
curl http://localhost:8000/health

# Expected: {"status": "healthy", ...}
```

### Step 7.3: Run Test Suite

```bash
cd backend

# Run all tests
pytest tests/ -v

# Expected: All tests pass, no ChromaDB import errors

# Specifically test RAG functionality
pytest tests/unit/test_rag*.py -v
pytest tests/integration/ -k rag -v
```

### Step 7.4: Verify Disk Space Freed

```bash
# Check docker volume space (ChromaDB volume should be gone)
docker volume ls

# Check disk usage
df -h

# Check docker images (ChromaDB image should be gone)
docker images | grep -i chroma

# Expected: No ChromaDB volumes or images
```

---

## Phase 8: Team Communication (10 minutes)

### Step 8.1: Update Team

**Send notification to team**:

```
Subject: ChromaDB Completely Removed - Now Using pgvector

Team,

ChromaDB has been completely removed from the ITL_Base_28.10 project after successful migration to pgvector.

✅ What's Changed:
- ChromaDB service removed from docker-compose.yml
- All RAG queries now use PostgreSQL pgvector
- Simplified infrastructure (one less service to manage)

⚠️ Action Required:
1. Pull latest changes: `git pull origin main`
2. Rebuild environment: `docker-compose down && docker-compose up -d`
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Run migrations if needed: `alembic upgrade head`

📚 Documentation:
- Migration details: Documentation/PGVECTOR_MIGRATION_PLAN.md
- Removal checklist: Documentation/CHROMADB_REMOVAL_CHECKLIST.md
- Updated architecture: Documentation/02_SYSTEM_ARCHITECTURE.md

Questions? Contact [team lead]
```

### Step 8.2: Update README

Add migration notice to main README:

```markdown
## Recent Changes

### 2025-11-03: Migrated from ChromaDB to pgvector
The RAG (Retrieval-Augmented Generation) system now uses pgvector (PostgreSQL extension) instead of ChromaDB. This simplifies infrastructure and improves integration with existing PostgreSQL data.

**Impact**:
- ChromaDB service removed from docker-compose.yml
- RAG queries now use PostgreSQL `documents` table
- See [Migration Plan](Documentation/PGVECTOR_MIGRATION_PLAN.md) for details
```

---

## Phase 9: Cleanup Checklist - Final Summary

Run through this checklist to ensure complete removal:

### Code Cleanup
- [ ] ✅ Removed `chromadb` from `requirements.txt`
- [ ] ✅ Uninstalled chromadb package from virtual environment
- [ ] ✅ Removed all `import chromadb` statements
- [ ] ✅ Removed ChromaDB config from `src/config.py`
- [ ] ✅ Removed ChromaDB variables from `.env` and `.env.example`
- [ ] ✅ Deleted or archived ChromaDB backup files

### Infrastructure Cleanup
- [ ] ✅ Removed ChromaDB service from `docker-compose.yml`
- [ ] ✅ Removed ChromaDB volume definition from `docker-compose.yml`
- [ ] ✅ Stopped and removed ChromaDB Docker container
- [ ] ✅ Deleted ChromaDB Docker volume
- [ ] ✅ Removed ChromaDB Docker images

### Scripts & Migrations Cleanup
- [ ] ✅ Archived ChromaDB migration scripts
- [ ] ✅ Marked old scripts as deprecated

### Documentation Updates
- [ ] ✅ Updated `backend/README.md`
- [ ] ✅ Updated `Documentation/02_SYSTEM_ARCHITECTURE.md`
- [ ] ✅ Updated `Documentation/04_DATABASE_SCHEMA_ERD.md`
- [ ] ✅ Updated `Documentation/05_API_REFERENCE_AND_GUIDES.md`
- [ ] ✅ Updated `Documentation/13_QUICKSTART.md`
- [ ] ✅ Created migration completion notice

### Configuration Updates
- [ ] ✅ Updated `.gitignore` if needed
- [ ] ✅ Updated `pyproject.toml` or `setup.py`
- [ ] ✅ Updated CI/CD configuration

### Verification
- [ ] ✅ Searched entire codebase for remaining "chroma" references
- [ ] ✅ Application starts without ChromaDB errors
- [ ] ✅ All tests pass
- [ ] ✅ Disk space freed (volumes and images removed)
- [ ] ✅ Team notified of changes

---

## Rollback Instructions (Emergency Only)

If critical issues discovered after ChromaDB removal:

### Quick Rollback (Within 24 hours)

```bash
# 1. Restore docker-compose.yml from git
git checkout HEAD~1 -- docker-compose.yml

# 2. Start ChromaDB
docker-compose up -d chromadb

# 3. Restore ChromaDB data from backup
# (If you created backup in Phase 1)
tar -xzf chromadb_backup_20251103.tar.gz -C /path/to/chromadb/volume

# 4. Revert code changes
git revert <commit-hash>

# 5. Reinstall ChromaDB
pip install chromadb>=0.4.0

# 6. Restart application
docker-compose restart backend
```

### Restore from PostgreSQL Backup

```bash
# If ChromaDB data lost, can regenerate from PostgreSQL documents table
python scripts/export_pgvector_to_chromadb.py
```

---

## Success Criteria

✅ **Removal Complete When**:
- No `import chromadb` in any Python files
- No ChromaDB service in `docker-compose.yml`
- No ChromaDB volumes or images in Docker
- Application runs successfully without ChromaDB
- All tests pass
- Documentation updated
- Team notified

---

## Post-Removal Benefits

### Infrastructure Simplified
- **Before**: 3 services (PostgreSQL, Redis, ChromaDB)
- **After**: 2 services (PostgreSQL, Redis)
- **Savings**: -1 HTTP service, -1 backup process, -1 monitoring target

### Operational Improvements
- **Backup**: Single PostgreSQL backup instead of two separate backups
- **Monitoring**: Fewer services to monitor
- **Deployment**: Simpler docker-compose configuration
- **Costs**: Lower infrastructure costs (fewer running containers)

### Developer Experience
- **Setup Time**: Faster local environment setup
- **Dependencies**: Fewer external dependencies
- **Debugging**: Easier to debug (SQL queries vs HTTP API calls)

---

## Timeline

| Phase | Time | When to Execute |
|-------|------|-----------------|
| Phase 1: Verification | 15 min | After 1 week on pgvector |
| Phase 2: Code Cleanup | 30 min | After verification |
| Phase 3: Docker Cleanup | 20 min | After code cleanup |
| Phase 4: Scripts Cleanup | 15 min | After docker cleanup |
| Phase 5: Documentation | 30 min | After all cleanup |
| Phase 6: Config Files | 10 min | After documentation |
| Phase 7: Final Verification | 15 min | After all changes |
| Phase 8: Team Communication | 10 min | After verification |

**Total Time**: ~2.5 hours

**Recommended Schedule**: Execute during maintenance window or low-traffic period

---

## Support & Troubleshooting

### Common Issues

**Issue**: Application fails to start after removal
**Solution**: Check for missed ChromaDB imports - search codebase with `grep -r chromadb`

**Issue**: Tests failing after removal
**Solution**: Update test fixtures that referenced ChromaDB

**Issue**: Docker won't remove volume
**Solution**: Ensure no containers are using it - `docker-compose down` first

### Getting Help

- Review: [pgvector Migration Plan](PGVECTOR_MIGRATION_PLAN.md)
- Check: [System Architecture](02_SYSTEM_ARCHITECTURE.md)
- Search: `git log --grep="chromadb" --all` for historical changes

---

**Document Status**: ✅ Ready to Use
**Last Updated**: 2025-11-03
**Maintained By**: Platform Team
