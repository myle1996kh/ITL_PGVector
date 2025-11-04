# Complete Setup Guide for eTMS Chatbot with PgVector RAG

This guide walks you through setting up the ITL AgentHub chatbot framework with the eTMS tenant, including database schema, seed data, and RAG capabilities using PgVector.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Alembic Migrations](#alembic-migrations)
4. [Seed eTMS Tenant Data](#seed-etms-tenant-data)
5. [Ingest RAG Data from PDF](#ingest-rag-data-from-pdf)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed
- **PostgreSQL 15+** with **pgvector extension**
- **Redis 7.x** (for caching)
- **Fernet encryption key** (for API key encryption)
- **API Keys**:
  - OpenRouter API key
  - OpenAI API key (optional)

---

## Database Setup

### Option 1: Using Docker Compose (Recommended)

The project includes a `docker-compose.yml` that sets up PostgreSQL with pgvector and Redis:

```bash
# Navigate to backend directory
cd backend

# Start services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs postgres
docker-compose logs redis
```

This will create:
- PostgreSQL 15 with pgvector extension on port 5432
- Redis on port 6379

### Option 2: Manual PostgreSQL Setup

If you're using an existing PostgreSQL instance:

```sql
-- Connect to your database
psql -U postgres

-- Create database
CREATE DATABASE chatbot_db;

-- Connect to the database
\c chatbot_db

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## Alembic Migrations

The project already includes two Alembic migrations:

1. **Migration 001**: Creates all database tables and seed data
2. **Migration 002**: Creates pgvector-enabled knowledge_documents table

### Configure Environment

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your configuration:
   ```bash
   # Database
   DATABASE_URL=postgresql://postgres:123456@localhost:5432/chatbot_db

   # Generate Fernet key
   FERNET_KEY=<generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'>

   # Redis
   REDIS_URL=redis://localhost:6379
   ```

### Run Migrations

```bash
# Install Python dependencies first
pip install -r requirements.txt

# Run migrations to create all tables
alembic upgrade head
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, complete_schema_and_seed
======================================================================
DATABASE SETUP COMPLETE!
======================================================================
✓ 14 tables created
✓ 5 base tools seeded
✓ 4 output formats seeded
✓ 4 LLM models seeded
...

INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add_pgvector_knowledge_base
======================================================================
PGVECTOR SCHEMA CREATED SUCCESSFULLY
======================================================================
✓ pgvector extension enabled
✓ knowledge_documents table created
...
```

### Verify Tables

```bash
# Connect to database
psql -U postgres -d chatbot_db

# List all tables
\dt

# You should see:
# - tenants
# - llm_models
# - tenant_llm_configs
# - base_tools
# - output_formats
# - tool_configs
# - agent_configs
# - agent_tools
# - tenant_agent_permissions
# - tenant_tool_permissions
# - sessions
# - messages
# - checkpoints
# - tenant_widget_configs
# - langchain_pg_collection (for pgvector)
# - langchain_pg_embedding (for pgvector)
```

---

## Seed eTMS Tenant Data

Now we'll create the eTMS tenant with specific LLM configurations and the AgentGuidance agent.

### Script: `migrations/seed_etms_tenant.py`

This script creates:
- **eTMS tenant** (domain: etms.example.com)
- **LLM Models**:
  - OpenRouter: openai/gpt-4o-mini
  - OpenRouter: google/gemini-2.5-flash-lite
  - OpenAI: gpt-4o-mini
- **Base Tools** (HTTP_GET, HTTP_POST, RAG, DB_QUERY, OCR)
- **RAG Tool Config** (search_knowledge_base with top_k=5)
- **AgentGuidance** agent linked to RAG tool
- **Tenant permissions** for agent and tool access
- **Encrypted API keys** for OpenRouter and OpenAI

### Run Seed Script

```bash
cd backend

# Run the seed script
python migrations/seed_etms_tenant.py
```

**Expected Output**:
```
======================================================================
SEEDING eTMS TENANT DATA
======================================================================

✓ Generated UUIDs for all entities

📦 Creating base tools...
✓ Base tools created

📄 Creating output formats...
✓ Output formats created

🤖 Creating LLM models...
✓ LLM models created
  - OpenRouter: openai/gpt-4o-mini
  - OpenRouter: google/gemini-2.5-flash-lite
  - OpenAI: gpt-4o-mini

🏢 Creating eTMS tenant...
✓ eTMS tenant created (ID: <uuid>)

🔑 Creating tenant LLM configs with encrypted API keys...
✓ OpenRouter config created
  - Provider: openrouter
  - Model: openai/gpt-4o-mini
  - API Key: sk-or-v1-dd1ccb222ac...

🔍 Creating RAG tool configuration...
✓ RAG tool configured (top_k: 5)

🤖 Creating AgentGuidance agent...
✓ AgentGuidance created (ID: <uuid>)

🔗 Linking AgentGuidance to RAG tool...
✓ Agent-tool link created

✅ Granting tenant permissions...
✓ Permissions granted

======================================================================
✅ eTMS TENANT SEEDING COMPLETE!
======================================================================

📊 Summary:
  Tenant ID: <uuid>
  Tenant Name: eTMS
  Domain: etms.example.com

🤖 LLM Models:
  - OpenRouter: openai/gpt-4o-mini (ID: <uuid>)
  - OpenRouter: google/gemini-2.5-flash-lite (ID: <uuid>)
  - OpenAI: gpt-4o-mini (ID: <uuid>)

🔧 Tools:
  - search_knowledge_base (RAG) (ID: <uuid>)

👤 Agents:
  - AgentGuidance (ID: <uuid>)

📚 Next Steps:
  1. Run: python migrations/seed_etms_rag_data.py
     (This will process the eTMS PDF and create RAG embeddings)
```

### Verify Data

```sql
-- Check eTMS tenant
SELECT * FROM tenants WHERE name = 'eTMS';

-- Check LLM models
SELECT provider, model_name FROM llm_models;

-- Check AgentGuidance agent
SELECT name, description FROM agent_configs WHERE name = 'AgentGuidance';

-- Check RAG tool
SELECT name, description FROM tool_configs WHERE name = 'search_knowledge_base';

-- Check tenant LLM config (API keys are encrypted)
SELECT tenant_id, llm_model_id FROM tenant_llm_configs
JOIN tenants ON tenant_llm_configs.tenant_id = tenants.tenant_id
WHERE tenants.name = 'eTMS';
```

---

## Ingest RAG Data from PDF

Now we'll process the eTMS USER GUIDE PDF and create vector embeddings for RAG.

### Script: `migrations/seed_etms_rag_data.py`

This script:
- Loads the eTMS USER GUIDE PDF (714 pages)
- Splits into chunks (1000 characters, 200 overlap)
- Generates 384-dimensional embeddings using all-MiniLM-L6-v2
- Stores in PgVector with tenant isolation

### Verify PDF Location

The script expects the PDF at:
```
notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf
```

### Run Ingestion Script

```bash
cd backend

# This will take 3-5 minutes to complete
python migrations/seed_etms_rag_data.py
```

**Expected Output**:
```
======================================================================
SEEDING eTMS RAG DATA FROM PDF
======================================================================

✓ PDF found: C:\Users\...\notebook_test_pgvector\eTMS USER GUIDE DOCUMENT.pdf
  Size: 15.23 MB

📋 Looking up eTMS tenant...
✓ Found eTMS tenant (ID: <uuid>)

🔧 Initializing RAG service (PgVector + all-MiniLM-L6-v2)...
✓ RAG service initialized

📦 Verifying PgVector collection...
✓ Collection ready: knowledge_documents

🔍 Checking for existing documents...

📄 Processing PDF...
   This may take several minutes for large documents...
   Steps:
   1. Loading PDF pages
   2. Splitting into chunks (1000 chars, 200 overlap)
   3. Generating embeddings (384 dimensions)
   4. Storing in PgVector

======================================================================
✅ RAG DATA SEEDING COMPLETE!
======================================================================

📊 Summary:
  Tenant: eTMS (<uuid>)
  PDF: eTMS USER GUIDE DOCUMENT.pdf
  Chunks ingested: 910
  Total chunks in KB: 910
  Embedding model: all-MiniLM-L6-v2 (384 dimensions)
  Backend: PostgreSQL + PgVector

✅ Knowledge base is ready!
```

### Verify RAG Data

```sql
-- Check total chunks in knowledge base
SELECT COUNT(*) FROM langchain_pg_embedding;

-- Check eTMS tenant chunks
SELECT COUNT(*) FROM langchain_pg_embedding
WHERE cmetadata->>'tenant_id' = '<your-etms-tenant-id>';

-- View sample chunk
SELECT
    document AS content,
    cmetadata->>'page' AS page,
    cmetadata->>'source' AS source
FROM langchain_pg_embedding
LIMIT 1;
```

---

## Testing

### Test RAG Query

```bash
cd backend

# Test RAG service directly
python -c "
from src.services.rag_service import get_rag_service

rag = get_rag_service()
result = rag.query_knowledge_base(
    tenant_id='<your-etms-tenant-id>',
    query='Hướng dẫn tạo đơn hàng trong eTMS',
    top_k=3
)

print('Top 3 Results:')
for i, doc in enumerate(result['documents'], 1):
    print(f'\n{i}. Similarity: {(1 - doc[\"distance\"]) * 100:.2f}%')
    print(f'   Page: {doc[\"metadata\"].get(\"page\")}')
    print(f'   Content: {doc[\"content\"][:200]}...')
"
```

### Test via API

1. **Start the backend server**:
   ```bash
   cd backend
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Send test request**:
   ```bash
   curl -X POST "http://localhost:8000/api/<tenant-id>/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hướng dẫn tạo đơn hàng trong eTMS",
       "user_id": "test_user"
     }'
   ```

3. **Expected response**:
   - AgentGuidance will search the knowledge base
   - Return relevant information from the eTMS guide
   - Cite specific pages

---

## Troubleshooting

### Issue: pgvector extension not found

```sql
-- Install pgvector extension manually
CREATE EXTENSION IF NOT EXISTS vector;
```

If this fails, ensure PostgreSQL has pgvector installed:
```bash
# Using Docker (recommended)
docker-compose up -d

# Or install manually on Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector

# Or on macOS with Homebrew
brew install pgvector
```

### Issue: Python dependencies missing

```bash
# Reinstall all dependencies
pip install -r requirements.txt --upgrade
```

### Issue: Alembic migration fails

```bash
# Check current migration status
alembic current

# If stuck, downgrade and re-run
alembic downgrade -1
alembic upgrade head
```

### Issue: Fernet key not found

```bash
# Generate a new Fernet key
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'

# Add to .env file
echo "FERNET_KEY=<generated-key>" >> .env
```

### Issue: PDF not found

Ensure the PDF is at the correct location:
```
project_root/
├── backend/
│   └── migrations/
│       └── seed_etms_rag_data.py
└── notebook_test_pgvector/
    └── eTMS USER GUIDE DOCUMENT.pdf
```

### Issue: API key errors

Check that API keys are properly encrypted in the database:
```sql
SELECT encrypted_api_key FROM tenant_llm_configs LIMIT 1;
```

The value should be a long encrypted string starting with `gAAAAA...`

---

## Summary

You now have:

✅ **Database Schema**: All 14 tables created via Alembic migrations
✅ **PgVector**: Enabled and configured for RAG
✅ **eTMS Tenant**: Created with LLM configurations
✅ **LLM Models**: OpenRouter and OpenAI models configured
✅ **AgentGuidance**: RAG-powered agent ready
✅ **Knowledge Base**: 910 chunks from eTMS USER GUIDE
✅ **Embeddings**: 384-dimensional vectors for similarity search

Your eTMS chatbot is now ready to answer questions about the eTMS system using RAG! 🎉

---

## Files Created

This setup created the following key files:

1. **`backend/migrations/seed_etms_tenant.py`** - Seeds eTMS tenant, LLM models, tools, and agent
2. **`backend/migrations/seed_etms_rag_data.py`** - Ingests PDF and creates RAG embeddings
3. **`backend/alembic/versions/20251103_001_complete_schema_and_seed.py`** - Initial schema migration
4. **`backend/alembic/versions/20251103_002_add_pgvector_knowledge_base.py`** - PgVector setup migration

---

## Next Steps

1. **Test the chatbot** via API or web interface
2. **Monitor performance** and adjust `top_k` parameter if needed
3. **Add more documents** to the knowledge base as needed
4. **Configure additional agents** for different use cases
5. **Set up authentication** for production deployment

For more information, see:
- `backend/README.md` - General backend documentation
- `backend/RAG_SYSTEM_STATUS.md` - RAG system status report
- API documentation at `http://localhost:8000/docs` when server is running
