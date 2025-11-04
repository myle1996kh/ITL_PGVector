# Quick Start Guide - eTMS Chatbot Setup

This is a quick reference for setting up your new database with eTMS tenant and RAG capabilities.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] PostgreSQL 15+ available (or use Docker)
- [ ] Redis available (or use Docker)
- [ ] Fernet encryption key generated
- [ ] PDF file at: `notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf`

## Step-by-Step Setup (5 steps)

### Step 1: Environment Setup (2 minutes)

```bash
cd backend

# Copy environment file
cp .env.example .env

# Generate Fernet key and add to .env
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'

# Edit .env file with:
# - DATABASE_URL=postgresql://postgres:123456@localhost:5432/chatbot_db
# - FERNET_KEY=<generated-key>
# - REDIS_URL=redis://localhost:6379
```

### Step 2: Start Services (1 minute)

```bash
# Option A: Using Docker (Recommended)
docker-compose up -d

# Option B: Use your own PostgreSQL + Redis
# Just ensure pgvector extension is enabled
```

### Step 3: Install Dependencies & Run Migrations (2 minutes)

```bash
# Install Python packages
pip install -r requirements.txt

# Run Alembic migrations (creates all tables + pgvector setup)
alembic upgrade head
```

**Expected Output**: 14 tables created + pgvector enabled

### Step 4: Seed eTMS Tenant Data (1 minute)

```bash
# Creates eTMS tenant, LLM models, AgentGuidance, and RAG tool
python migrations/seed_etms_tenant.py
```

**What this creates**:
- ✅ eTMS tenant (domain: etms.example.com)
- ✅ 3 LLM models (OpenRouter + OpenAI)
- ✅ API keys encrypted and stored
- ✅ AgentGuidance agent with RAG capabilities
- ✅ search_knowledge_base tool (top_k=5)

### Step 5: Ingest PDF for RAG (3-5 minutes)

```bash
# Process eTMS USER GUIDE PDF and create embeddings
python migrations/seed_etms_rag_data.py
```

**What this does**:
- ✅ Loads PDF (714 pages)
- ✅ Splits into ~910 chunks (1000 chars each)
- ✅ Generates 384-dimensional embeddings
- ✅ Stores in PgVector with tenant isolation

---

## Verification

### Check Database

```sql
-- Connect to database
psql -U postgres -d chatbot_db

-- Check eTMS tenant
SELECT tenant_id, name, domain FROM tenants WHERE name = 'eTMS';

-- Check knowledge base (should show ~910 chunks)
SELECT COUNT(*) FROM langchain_pg_embedding;

-- Check LLM models
SELECT provider, model_name FROM llm_models;
```

### Test RAG System

```bash
# Start backend server
uvicorn src.main:app --reload

# In another terminal, test the API
curl -X POST "http://localhost:8000/api/<tenant-id>/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hướng dẫn tạo đơn hàng trong eTMS",
    "user_id": "test"
  }'
```

---

## What's Different from Before

### ✅ Migrations Already Exist
- **Migration 001**: Creates all 14 tables + seed data (base tools, output formats, demo tenant)
- **Migration 002**: Enables pgvector + creates knowledge_documents table

You don't need to create new migrations!

### ✅ Two Separate Seed Scripts

1. **`seed_etms_tenant.py`** - Creates eTMS tenant with your specific:
   - OpenRouter API key: `sk-or-v1-dd1ccb222acb...`
   - OpenAI API key: `sk-proj-F457kjgoT7XI...`
   - LLM models: `openai/gpt-4o-mini`, `google/gemini-2.5-flash-lite`
   - AgentGuidance agent

2. **`seed_etms_rag_data.py`** - Processes PDF and creates RAG embeddings

### ✅ ChromaDB Removed

All ChromaDB references have been removed:
- ❌ Removed from `config.py`
- ❌ Removed from `requirements.txt`
- ❌ Removed from `.env.example`
- ❌ Removed from `docker-compose.yml`
- ❌ Removed from `setup.sh`
- ❌ Removed from `README.md`

### ✅ PgVector Fully Configured

- Docker Compose uses `pgvector/pgvector:pg15` image
- PgVector extension enabled via Migration 002
- RAG service already uses PgVector (no code changes needed)
- Multi-tenant isolation via metadata filtering

---

## File Structure

```
backend/
├── alembic/
│   └── versions/
│       ├── 20251103_001_complete_schema_and_seed.py    # Creates all tables
│       └── 20251103_002_add_pgvector_knowledge_base.py  # Enables pgvector
├── migrations/
│   ├── seed_etms_tenant.py         # NEW: Seeds eTMS tenant
│   └── seed_etms_rag_data.py       # NEW: Ingests PDF for RAG
├── src/
│   ├── services/
│   │   ├── rag_service.py          # Already uses PgVector ✅
│   │   ├── embedding_service.py
│   │   └── document_processor.py
│   └── models/                      # All 14 SQLAlchemy models
├── docker-compose.yml               # Updated: PgVector + Redis only
├── requirements.txt                 # Updated: ChromaDB removed
├── .env.example                     # Updated: ChromaDB config removed
├── SETUP_GUIDE.md                   # NEW: Detailed setup guide
└── README.md                        # Updated: References removed
```

---

## Troubleshooting

### "pgvector extension not found"
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### "PDF not found"
Ensure: `notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf` exists

### "Fernet key error"
Generate a new key: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`

### "Migration already exists"
That's OK! Just run: `alembic upgrade head`

---

## Summary of Changes

✅ **Created**:
- `backend/migrations/seed_etms_tenant.py` (eTMS tenant + LLM setup)
- `backend/migrations/seed_etms_rag_data.py` (PDF ingestion + RAG)
- `backend/SETUP_GUIDE.md` (Detailed documentation)
- `QUICK_START.md` (This file)

✅ **Updated**:
- `backend/docker-compose.yml` (PgVector image, removed ChromaDB)
- `backend/requirements.txt` (Removed ChromaDB)
- `backend/src/config.py` (Removed CHROMA_URL)
- `backend/.env.example` (Removed ChromaDB config)
- `backend/setup.sh` (Updated messages)
- `backend/README.md` (Updated documentation)

✅ **Already Done** (No changes needed):
- Alembic migrations (001 and 002)
- RAG service (already using PgVector)
- Database models (all 14 tables defined)

---

## Your Specific Configuration

This setup uses your exact requirements:

**OpenRouter API Key**: `<your-openrouter-api-key>`
- Model: `openai/gpt-4o-mini`
- Model: `google/gemini-2.5-flash-lite`

**OpenAI API Key**: `<your-openai-api-key>`
- Model: `gpt-4o-mini`

**RAG Data Source**: `notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf`

**Agent**: AgentGuidance (uses RAG to answer eTMS questions)

---

## Next Steps

1. Run the 5 setup steps above
2. Test the chatbot via API
3. Check `backend/SETUP_GUIDE.md` for detailed troubleshooting
4. Monitor logs: `docker-compose logs -f postgres`

🎉 **Your eTMS chatbot with PgVector RAG is ready!**
