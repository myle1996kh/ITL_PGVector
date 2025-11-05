# eTMS RAG System - Docker Setup Guide

## Overview

This guide covers the complete Docker deployment of the eTMS Vietnamese RAG (Retrieval-Augmented Generation) system with the following features:

- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions, local, offline)
- **Vector Database**: PostgreSQL 16 with pgvector extension
- **Caching**: Redis 7
- **Backend**: FastAPI with LangChain + LangGraph
- **LLM**: GPT-4o-mini via OpenRouter
- **Database Port**: 5432 (standardized)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Docker Network: etms-network                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   pgvector   │  │    redis     │  │   app        │  │
│  │  (postgres)  │  │   (cache)    │  │  (FastAPI)   │  │
│  │  Port: 5432  │  │  Port: 6379  │  │  Port: 8000  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                     Host Network
```

## Key Changes from Previous Setup

### 1. Removed ProtonX Embeddings (API-based, 768 dims)
   - ❌ Removed `protonx==0.1.6` from requirements.txt
   - ❌ Removed `PROTONX_API_KEY` from .env
   - ❌ Deleted ProtonX-based embedding_service.py

### 2. Switched to all-MiniLM-L6-v2 (Local, 384 dims)
   - ✅ Added `sentence-transformers>=3.3.0` to requirements.txt
   - ✅ Rewrote `embedding_service.py` for local model
   - ✅ Model pre-downloaded during Docker build
   - ✅ Cached in Docker volume for persistence

### 3. Updated AgentGuidance System Prompt
   - ✅ New structured format: `CONTEXT FROM eTMS USER GUIDE:\n{context}\n\n{user_query}: {final_answer}`
   - ✅ Strict citation rules (no hallucination)
   - ✅ Mandatory page number references
   - ✅ Clear format preservation

### 4. Standardized PostgreSQL Port
   - ❌ Old: Port 5433 (conflicted with alembic.ini)
   - ✅ New: Port 5432 (standard PostgreSQL port)
   - ✅ Updated .env, docker-compose.yml, and alembic.ini

## Files Created/Modified

### Created (4 files):
1. ✅ `Dockerfile` - Backend application container
2. ✅ `docker-setup.sh` - Linux/Mac automated setup script
3. ✅ `docker-setup.bat` - Windows automated setup script
4. ✅ `DOCKER_SETUP_README.md` - This documentation

### Modified (7 files):
1. ✅ `requirements.txt` - Removed protonx, added sentence-transformers
2. ✅ `.env` - Removed PROTONX_API_KEY, changed port 5433→5432
3. ✅ `docker-compose.yml` - Added app service, fixed port, added network
4. ✅ `src/services/embedding_service.py` - Complete rewrite for all-MiniLM-L6-v2
5. ✅ `alembic/versions/20251104_001_fresh_vietnamese_rag_complete.py` - Updated prompt + dimensions
6. ✅ `.dockerignore` - Already existed (no changes needed)
7. ✅ `alembic.ini` - Already correct (port 5432)

## Quick Start

### Option 1: Automated Setup (Recommended)

**Linux/Mac:**
```bash
cd backend
chmod +x docker-setup.sh
./docker-setup.sh
```

**Windows:**
```batch
cd backend
docker-setup.bat
```

### Option 2: Manual Setup

```bash
# 1. Build and start services
docker-compose up -d --build

# 2. Wait for services to be healthy
docker-compose ps

# 3. Run migrations
docker-compose exec app alembic upgrade head

# 4. Update API key
docker-compose exec app python update_api_key.py

# 5. Ingest eTMS PDF
docker-compose exec app python ingest_etms_pdf.py

# 6. Test embedding service
docker-compose exec app python -c "from src.services.embedding_service import get_embedding_service; svc = get_embedding_service(); print(f'Model: {svc.model_name}, Dimension: {svc.dimension}')"
```

## Service URLs

After successful deployment:

- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL (pgvector)**: localhost:5432
  - Username: postgres
  - Password: 123456
  - Database: postgres
- **Redis**: localhost:6379

## Testing the RAG System

### 1. Check Service Health

```bash
curl http://localhost:8000/health
```

### 2. Test Chat Endpoint

First, get your tenant ID from the database:
```bash
docker-compose exec app python -c "from src.database import SessionLocal; from src.models.tenant import Tenant; db = SessionLocal(); tenant = db.query(Tenant).filter(Tenant.name == 'eTMS Company').first(); print(f'Tenant ID: {tenant.tenant_id}')"
```

Then test the chat:
```bash
curl -X POST "http://localhost:8000/api/<tenant-id>/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hướng dẫn tạo đơn hàng FCL",
    "user_id": "test"
  }'
```

### 3. Expected Response Format

```json
{
  "response": "CONTEXT FROM eTMS USER GUIDE:\nĐể tạo đơn hàng FCL, người dùng có thể...\n(Nguồn: Trang 69 - 4.8.1 FCL Booking)\n\nCách tạo đơn hàng FCL: Người dùng có thể tạo đơn hàng FCL bằng cách..."
}
```

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f pgvector
docker-compose logs -f redis
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app
```

### Stop Services
```bash
# Stop all services (keep data)
docker-compose stop

# Stop and remove containers (keep data)
docker-compose down

# Stop and remove containers + volumes (delete all data)
docker-compose down -v
```

### Shell Access
```bash
# Backend app shell
docker-compose exec app bash

# PostgreSQL shell
docker-compose exec pgvector psql -U postgres -d postgres

# Redis CLI
docker-compose exec redis redis-cli
```

### Database Operations
```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Rollback migration
docker-compose exec app alembic downgrade -1

# Check migration status
docker-compose exec app alembic current

# Re-ingest PDF
docker-compose exec app python ingest_etms_pdf.py
```

## Troubleshooting

### 1. Services Not Starting

**Check logs:**
```bash
docker-compose logs -f
```

**Common issues:**
- Port 5432 or 8000 already in use → Stop conflicting services
- Out of disk space → Clean up Docker: `docker system prune -a`
- Network issues → Recreate network: `docker-compose down && docker-compose up -d`

### 2. Database Connection Errors

**Verify PostgreSQL is healthy:**
```bash
docker-compose exec pgvector pg_isready -U postgres
```

**Check connection from app:**
```bash
docker-compose exec app python -c "from src.database import engine; print(engine)"
```

### 3. Embedding Model Not Loading

**Check model cache:**
```bash
docker-compose exec app ls -la /root/.cache/torch/sentence_transformers/
```

**Manually download model:**
```bash
docker-compose exec app python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### 4. Migration Errors

**Reset database (WARNING: Deletes all data):**
```bash
docker-compose down -v
docker-compose up -d pgvector redis
sleep 10
docker-compose up -d app
docker-compose exec app alembic upgrade head
```

### 5. RAG Query Returns No Results

**Check document count:**
```bash
docker-compose exec app python -c "from src.database import SessionLocal; db = SessionLocal(); from sqlalchemy import text; result = db.execute(text('SELECT COUNT(*) FROM langchain_pg_embedding')).scalar(); print(f'Document chunks: {result}')"
```

**Re-ingest if count is 0:**
```bash
docker-compose exec app python ingest_etms_pdf.py
```

## Performance Optimization

### 1. Increase PostgreSQL Resources

Edit `docker-compose.yml`:
```yaml
pgvector:
  environment:
    - POSTGRES_SHARED_BUFFERS=256MB
    - POSTGRES_WORK_MEM=16MB
    - POSTGRES_MAINTENANCE_WORK_MEM=64MB
```

### 2. Adjust Redis Memory

Edit `docker-compose.yml`:
```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3. Scale Backend Workers

```bash
# Run multiple app containers
docker-compose up -d --scale app=3
```

## Environment Variables

Key environment variables in `.env`:

```bash
# Database (standardized to port 5432)
DATABASE_URL=postgresql://postgres:123456@localhost:5432/postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# OpenRouter LLM API
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Security
FERNET_KEY=kN8j3xP5mR7qT9wV2yB4nL6oC1eH3fA8gD0iK5sU9jM=
DISABLE_AUTH=true  # Set to false in production!

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## RAG Configuration

### Embedding Parameters
- **Model**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Batch size**: 32
- **Location**: Local (cached in Docker volume)

### Document Processing
- **Chunk size**: 1500 characters
- **Chunk overlap**: 300 characters (20%)
- **Separators**: `["\n\n", "\n", ". ", " ", ""]`

### Retrieval
- **Top-K**: 7 chunks
- **Similarity**: Cosine distance
- **Metadata filtering**: By tenant_id

### LLM Generation
- **Model**: `openai/gpt-4o-mini` (via OpenRouter)
- **Temperature**: 0.2 (factual responses)
- **Max tokens**: 6144 (longer Vietnamese)
- **Context window**: 128,000 tokens

## Security Considerations

### Production Checklist:
- [ ] Change default PostgreSQL password
- [ ] Set `DISABLE_AUTH=false` in .env
- [ ] Use proper JWT public/private keys
- [ ] Enable HTTPS/TLS for API
- [ ] Restrict CORS origins
- [ ] Use Docker secrets for sensitive keys
- [ ] Enable PostgreSQL SSL connections
- [ ] Set up firewall rules
- [ ] Implement rate limiting
- [ ] Enable audit logging

### Docker Security:
```yaml
# Add to app service in docker-compose.yml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
user: "1000:1000"  # Non-root user
```

## Monitoring

### Health Checks

All services have health checks configured:
- **pgvector**: `pg_isready` every 10s
- **redis**: `redis-cli ping` every 10s
- **app**: HTTP GET to `/health` every 30s

### View Health Status
```bash
docker-compose ps
```

### Metrics Collection

Add Prometheus exporter:
```yaml
# In docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## Backup and Restore

### Backup PostgreSQL
```bash
# Backup database
docker-compose exec pgvector pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql

# Backup with compression
docker-compose exec pgvector pg_dump -U postgres postgres | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore PostgreSQL
```bash
# Restore from backup
cat backup_20251104.sql | docker-compose exec -T pgvector psql -U postgres -d postgres
```

### Backup Volumes
```bash
# Backup pgvector data volume
docker run --rm -v ITL_Base_28_10_backend_pgvector_data:/data -v $(pwd):/backup ubuntu tar czf /backup/pgvector_backup.tar.gz /data

# Restore pgvector data volume
docker run --rm -v ITL_Base_28_10_backend_pgvector_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/pgvector_backup.tar.gz -C /
```

## Upgrading

### Update Dependencies
```bash
# Update requirements.txt
docker-compose build --no-cache app
docker-compose up -d app
```

### Run New Migrations
```bash
# Create new migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Apply migration
docker-compose exec app alembic upgrade head
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review this documentation
3. Check PostgreSQL logs: `docker-compose logs pgvector`
4. Verify embedding service: Test with simple query
5. Re-run setup scripts if needed

## Summary

This Docker setup provides a complete, production-ready eTMS RAG system with:
- ✅ Local embedding model (no API dependencies)
- ✅ Standardized ports (5432 for PostgreSQL)
- ✅ Updated Vietnamese-specific system prompt
- ✅ Automated setup scripts for Windows, Linux, Mac
- ✅ Health checks and monitoring
- ✅ Persistent data volumes
- ✅ Network isolation
- ✅ Easy scaling and maintenance

**Next steps:** Run the setup script and test the system with Vietnamese queries!
