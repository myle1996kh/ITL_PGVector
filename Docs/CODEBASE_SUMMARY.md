# eTMS AgentHub - Codebase Summary

## 📋 Quick Reference

**Project**: eTMS Multi-Agent Chatbot Framework with Vietnamese RAG
**Tech Stack**: FastAPI + LangChain + LangGraph + PostgreSQL (pgvector) + Redis
**Deployment**: Docker (3 services: app, pgvector, redis)
**Embedding**: all-MiniLM-L6-v2 (384 dims, local model)
**LLM**: GPT-4o-mini via OpenRouter

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                     (Port 8000)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Supervisor   │  │   Domain     │  │    Tools     │     │
│  │   Agent      │→ │   Agents     │→ │   (HTTP,     │     │
│  │ (Routing)    │  │ (Execution)  │  │   RAG, etc)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  LLM Manager │  │  RAG Service │  │  Embedding   │     │
│  │ (OpenRouter) │  │  (PgVector)  │  │  Service     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓             │
├─────────────────────────────────────────────────────────────┤
│                  Database Layer (SQLAlchemy)                │
├─────────────────────────────────────────────────────────────┤
│   PostgreSQL (pgvector)    │         Redis                  │
│   - 14 tables              │         - Agent cache          │
│   - Vector embeddings      │         - Session state        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Structure

```
backend/
├── src/
│   ├── api/                    # API endpoints
│   │   ├── admin/              # Admin CRUD APIs
│   │   │   ├── agents.py       # Agent management
│   │   │   ├── tools.py        # Tool management
│   │   │   └── tenants.py      # Tenant management
│   │   └── chat.py             # Main chat endpoint
│   │
│   ├── models/                 # SQLAlchemy models (14 tables)
│   │   ├── agent.py            # AgentConfig, AgentTools
│   │   ├── base_tool.py        # BaseTool (5 types)
│   │   ├── tool.py             # ToolConfig (instances)
│   │   ├── tenant.py           # Tenants
│   │   ├── permissions.py      # Tenant permissions
│   │   ├── session.py          # Chat sessions
│   │   └── message.py          # Message history
│   │
│   ├── services/               # Core business logic
│   │   ├── supervisor_agent.py # Routing agent (NOT in DB)
│   │   ├── domain_agents.py    # Execution agents (IN DB)
│   │   ├── tool_loader.py      # Tool registry (⚠️ HARDCODED)
│   │   ├── llm_manager.py      # LLM client management
│   │   ├── rag_service.py      # PgVector RAG
│   │   ├── embedding_service.py# all-MiniLM-L6-v2
│   │   ├── document_processor.py# PDF → chunks
│   │   └── cache_service.py    # Redis caching
│   │
│   ├── tools/                  # Tool implementations
│   │   ├── base.py             # BaseTool interface
│   │   ├── http.py             # HTTPGetTool, HTTPPostTool
│   │   └── rag.py              # RAGTool
│   │
│   ├── utils/                  # Utilities
│   │   ├── logging.py          # Structured logging
│   │   ├── encryption.py       # Fernet encryption
│   │   └── formatters.py       # Response formatting
│   │
│   ├── config.py               # Settings (Pydantic)
│   ├── database.py             # DB connection
│   └── main.py                 # FastAPI app
│
├── alembic/                    # Database migrations
│   └── versions/
│       └── 20251104_001_fresh_vietnamese_rag_complete.py
│
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # App container
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── rebuild_database.py         # Database reset script
```

---

## 🗄️ Database Schema (14 Tables)

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **tenants** | Multi-tenant organizations | tenant_id, name, is_active |
| **llm_models** | LLM configurations | provider, model_name, context_window |
| **tenant_llm_configs** | Encrypted API keys per tenant | tenant_id, llm_model_id, encrypted_api_key |

### Tool System (3-Tier Architecture)

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **base_tools** | Tool types (5 total) | base_tool_id, name, handler_class ⚠️ |
| **tool_configs** | Tool instances | tool_id, name, config (JSONB), input_schema |
| **agent_tools** | Agent-tool mapping | agent_id, tool_id, priority |

**⚠️ Key Issue**: `base_tools.handler_class` is in DB but lookup is hardcoded in code

### Agent System

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **agent_configs** | Domain agents (IN DB) | agent_id, name, prompt_template, llm_model_id |
| **output_formats** | Response formats | format_name (json, markdown, etc.) |

**Note**: SupervisorAgent is NOT in DB - it's a service only!

### Permissions (Multi-Tenant)

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **tenant_agent_permissions** | Which agents tenants can use | tenant_id, agent_id, enabled |
| **tenant_tool_permissions** | Which tools tenants can use | tenant_id, tool_id, enabled |

### Chat & State

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **sessions** | Chat sessions | session_id, tenant_id, agent_id, user_id |
| **messages** | Conversation history | message_id, session_id, role, content |
| **checkpoints** | LangGraph state | thread_id, checkpoint (JSONB) |
| **tenant_widget_configs** | UI widget settings | tenant_id, widget_title, theme_color |

### PgVector (Auto-created by LangChain)

| Table | Purpose |
|-------|---------|
| **langchain_pg_collection** | Collection metadata |
| **langchain_pg_embedding** | Vector embeddings (384 dims) |

---

## 🔄 Request Flow

### Example: "Hướng dẫn tạo đơn hàng FCL"

```
1. User sends message
   ↓
2. POST /api/{tenant_id}/chat
   ↓
3. SupervisorAgent (routing)
   - Loads available agents from DB (tenant_agent_permissions)
   - Builds dynamic routing prompt
   - LLM selects: "AgentGuidance"
   ↓
4. DomainAgent (AgentGuidance)
   - Loads from agent_configs table
   - Gets prompt_template (Vietnamese)
   - Loads tools via tool_registry.load_agent_tools()
   ↓
5. ToolRegistry.load_agent_tools()
   - Queries agent_tools (priority order)
   - Checks tenant_tool_permissions
   - Loads tool_configs from DB
   - Gets base_tool.handler_class
   - ⚠️ Looks up in HARDCODED registry
   - Creates LangChain StructuredTool
   - Returns to agent
   ↓
6. Agent executes with LLM + tools
   - LLM decides to call search_knowledge_base
   - RAGTool.execute(query="FCL booking")
   ↓
7. RAGService.query_knowledge_base()
   - EmbeddingService.embed_query() → 384-dim vector
   - PgVector similarity search (top_k=7)
   - Returns relevant chunks with metadata
   ↓
8. LLM generates response
   - Uses structured prompt format
   - Includes context + citations
   - Returns Vietnamese answer
   ↓
9. Response formatted and returned to user
```

---

## 🔑 Key Components Deep Dive

### 1. SupervisorAgent (Service Only - NOT in DB)

**File**: `src/services/supervisor_agent.py`

**Purpose**: Routes user queries to appropriate domain agents

**How it works**:
```python
# Dynamically loads agents from database
available_agents = db.query(AgentConfig)
    .join(TenantAgentPermission)
    .filter(tenant_id, enabled=True)
    .all()

# Builds routing prompt with agent descriptions
prompt = f"""You are a supervisor. Available agents:
- AgentGuidance: eTMS user guide queries
- AgentAnalytics: Data analysis (if exists)
Route user query to appropriate agent."""

# LLM selects agent name → creates agent → executes
```

**Key insight**: Supervisor is fully dynamic - add agents to DB and they automatically appear in routing!

---

### 2. DomainAgent (Stored in DB)

**File**: `src/services/domain_agents.py`

**Purpose**: Executes specific domain tasks with tools

**Configuration** (from `agent_configs` table):
```python
{
  "agent_id": "uuid",
  "name": "AgentGuidance",
  "prompt_template": "Bạn là trợ lý eTMS...",  # Plain text, Vietnamese
  "llm_model_id": "gpt-4o-mini-uuid",
  "handler_class": "services.domain_agents.DomainAgent"  # Dynamic loading! ✅
}
```

**Flow**:
1. Load config from DB
2. Load tools via `tool_registry.load_agent_tools(agent_id)`
3. Get LLM client via `llm_manager.get_llm_for_tenant()`
4. Create LangChain agent with prompt + tools + LLM
5. Execute query
6. Return formatted response

---

### 3. ToolRegistry (⚠️ HARDCODED ISSUE)

**File**: `src/services/tool_loader.py`

**Purpose**: Load and cache tool implementations

**Current Implementation**:
```python
class ToolRegistry:
    def __init__(self):
        self._cache: Dict[str, StructuredTool] = {}
        self._tool_handlers = {
            "tools.http.HTTPGetTool": HTTPGetTool,      # ← HARDCODED!
            "tools.http.HTTPPostTool": HTTPPostTool,    # ← HARDCODED!
            "tools.rag.RAGTool": RAGTool,               # ← HARDCODED!
        }

    def create_tool_from_db(self, ...):
        # 1. Load tool_config from database ✅
        tool_config = db.query(ToolConfig).filter(tool_id=tool_id).first()

        # 2. Load base_tool to get handler_class ✅
        base_tool = db.query(BaseTool).filter(base_tool_id=...).first()

        # 3. Get handler from HARDCODED dict ❌
        handler_class = self._tool_handlers.get(base_tool.handler_class)
        if not handler_class:
            raise ValueError(f"Unsupported tool handler: {base_tool.handler_class}")

        # 4. Create LangChain tool
        # 5. Cache and return
```

**Problem**: Even though `handler_class` is in database, it must exist in hardcoded dict!

**Solution**: See `DYNAMIC_TOOL_LOADING.md` for implementation guide

---

### 4. RAG Service (PgVector)

**File**: `src/services/rag_service.py`

**Purpose**: Semantic search over eTMS USER GUIDE

**Configuration**:
- **Embedding**: all-MiniLM-L6-v2 (384 dims)
- **Chunk size**: 1500 characters
- **Chunk overlap**: 300 characters (20%)
- **Top-K**: 7 chunks
- **Similarity**: Cosine distance

**Flow**:
```python
def query_knowledge_base(tenant_id, query, top_k=7):
    # 1. Embed query → 384-dim vector
    query_embedding = embedding_service.embed_query(query)

    # 2. PgVector similarity search with metadata filter
    results = vector_store.similarity_search_with_score(
        query_embedding,
        k=top_k,
        filter={"tenant_id": tenant_id}  # Multi-tenant isolation
    )

    # 3. Return chunks with metadata (page numbers, sources)
    return [{
        "content": doc.page_content,
        "metadata": doc.metadata,  # page, source, ingested_at
        "score": score
    }]
```

**Ingestion**:
```python
def ingest_pdf(pdf_path, tenant_id):
    # 1. Load PDF
    docs = PyPDFLoader(pdf_path).load()

    # 2. Split into chunks (1500 chars, 300 overlap)
    chunks = RecursiveCharacterTextSplitter(...).split_documents(docs)

    # 3. Enrich with metadata
    for chunk in chunks:
        chunk.metadata.update({"tenant_id": tenant_id, "ingested_at": now})

    # 4. Generate embeddings (batch)
    embeddings = embedding_service.embed_documents([c.page_content for c in chunks])

    # 5. Store in PgVector
    vector_store.add_documents(chunks)
```

---

### 5. LLM Manager

**File**: `src/services/llm_manager.py`

**Purpose**: Manage LLM clients per tenant with caching

**Configuration** (Vietnamese-optimized):
```python
ChatOpenAI(
    model="openai/gpt-4o-mini",  # Via OpenRouter
    api_key=tenant_api_key,      # Decrypted from DB
    base_url="https://openrouter.ai/api/v1",
    temperature=0.2,             # Factual responses (was 0.7)
    max_tokens=6144,             # Longer Vietnamese (was 4096)
    streaming=True
)
```

**Caching**:
```python
# Cache key: f"{tenant_id}:{model_name}"
# LLM clients cached per tenant to avoid recreating
```

---

### 6. Embedding Service

**File**: `src/services/embedding_service.py`

**Model**: `all-MiniLM-L6-v2` (sentence-transformers)

**Key Methods**:
```python
class LocalEmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = 384

    def embed_query(self, text: str) -> List[float]:
        """Single text → 384-dim vector"""
        return self.model.encode(text).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch texts → 384-dim vectors"""
        return self.model.encode(texts, batch_size=32).tolist()
```

**Performance**:
- Model pre-downloaded in Docker build
- Cached in volume: `/root/.cache/torch/sentence_transformers`
- ~100ms for single query embedding

---

## 🔧 Configuration Files

### .env (Environment Variables)

```bash
# Database (Port 5432 - standardized)
DATABASE_URL=postgresql://postgres:123456@localhost:5432/postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# LLM API
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Security
FERNET_KEY=...                 # For encrypting tenant API keys
DISABLE_AUTH=true              # Development only!

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### docker-compose.yml (3 Services)

```yaml
services:
  pgvector:    # PostgreSQL 16 + pgvector, Port 5432
  redis:       # Redis 7 Alpine, Port 6379
  app:         # FastAPI backend, Port 8000
    volumes:
      - .:/app                                          # Hot reload
      - model-cache:/root/.cache/torch/sentence_transformers  # Model cache
```

### alembic.ini (Migrations)

**Important**: Uses port 5432 (matches .env now)

---

## 🎯 Key Design Patterns

### 1. Multi-Tenancy

**Strategy**: Tenant ID in every table + permission checks

```python
# Tenant isolation in RAG
vector_store.similarity_search(
    query,
    filter={"tenant_id": tenant_id}  # Only this tenant's documents
)

# Tenant permissions check
permission = db.query(TenantToolPermission).filter(
    tenant_id=tenant_id,
    tool_id=tool_id,
    enabled=True
).first()
```

### 2. Singleton Services

**Examples**:
- `tool_registry` (global instance)
- `llm_manager` (per-tenant caching)
- `embedding_service` (model loaded once)
- `rag_service` (vector store connection)

**Why**: Avoid reloading heavy resources (models, DB connections)

### 3. Database-Driven Configuration

**What's in DB**:
- ✅ Agent prompts (can update without redeployment)
- ✅ Tool configurations (endpoints, parameters)
- ✅ Tenant permissions (enable/disable features)
- ✅ LLM models (add new providers)

**What's in Code**:
- ❌ Tool handler registry (see DYNAMIC_TOOL_LOADING.md)
- ❌ Supervisor agent implementation
- ❌ Core business logic

### 4. Caching Strategy (2-Level)

**Level 1: Redis** (shared across instances)
- Agent configurations: `agenthub:{tenant_id}:cache:agent:{agent_id}`
- LLM clients: `agenthub:{tenant_id}:llm:{model_name}`
- TTL: 3600 seconds (1 hour)

**Level 2: In-Memory** (per process)
- Tool instances: `{tenant_id}:{tool_id}`
- Embedding service: Singleton model
- No TTL (cleared on restart)

---

## 🚀 Common Operations

### Add New Tool Instance (No Redeployment)

```bash
# 1. Create via Admin API
curl -X POST http://localhost:8000/api/admin/tools \
  -H "Content-Type: application/json" \
  -d '{
    "base_tool_id": "<http-get-uuid>",
    "name": "get_customer_info",
    "config": {
      "base_url": "https://api.etms.com",
      "endpoint": "/customers/{customer_id}"
    },
    "input_schema": {
      "type": "object",
      "properties": {
        "customer_id": {"type": "string"}
      }
    }
  }'

# 2. Assign to agent
curl -X PATCH http://localhost:8000/api/admin/agents/<agent-id> \
  -d '{"tool_ids": ["<tool-1>", "<new-tool>"]}'

# 3. Grant tenant permission
curl -X POST http://localhost:8000/api/admin/tenants/<tenant-id>/tools \
  -d '{"tool_id": "<new-tool>", "enabled": true}'

# 4. Clear cache (optional)
curl -X POST http://localhost:8000/api/admin/agents/reload?tenant_id=<tenant-id>

# 5. DONE! Tool available immediately
```

### Add New Agent (No Redeployment)

```bash
# 1. Create via Admin API
curl -X POST http://localhost:8000/api/admin/agents \
  -d '{
    "name": "AgentAnalytics",
    "prompt_template": "You are a data analyst...",
    "llm_model_id": "<gpt-4o-mini-uuid>",
    "tool_ids": ["<tool-1>", "<tool-2>"]
  }'

# 2. Grant tenant permission
# (via Admin API or SQL)

# 3. Supervisor automatically includes in routing!
```

### Re-ingest PDF

```bash
docker-compose exec app python ingest_etms_pdf.py

# Or manually:
docker-compose exec app python -c "
from src.services.rag_service import get_rag_service
from src.database import SessionLocal

db = SessionLocal()
rag = get_rag_service()

# Delete old documents
rag.delete_documents(db, tenant_id, doc_ids=['all'])

# Ingest new PDF
rag.ingest_pdf(
    db,
    pdf_path='../notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf',
    tenant_id=tenant_id
)
"
```

### Database Reset

```bash
cd backend
python rebuild_database.py

# This will:
# 1. Drop all tables
# 2. Run fresh migration
# 3. Seed base data (tools, formats, models, eTMS tenant)
```

---

## 🐛 Debugging Guide

### Tool Not Loading

**Symptom**: `ValueError: Unsupported tool handler: tools.custom.MyTool`

**Cause**: Handler not in hardcoded registry

**Solution**:
1. Check `tool_loader.py` line 21-28
2. Add to `_tool_handlers` dict OR
3. Implement dynamic loading (see DYNAMIC_TOOL_LOADING.md)

### Agent Not Appearing in Chat

**Checklist**:
1. ✅ Agent exists in `agent_configs` table
2. ✅ Agent `is_active = true`
3. ✅ `tenant_agent_permissions` has `enabled = true`
4. ✅ Clear Redis cache: `POST /api/admin/agents/reload`

### RAG Returns No Results

**Checklist**:
1. ✅ Documents ingested: `SELECT COUNT(*) FROM langchain_pg_embedding WHERE cmetadata->>'tenant_id' = '<id>'`
2. ✅ Query embeddings working: Test `embedding_service.embed_query("test")`
3. ✅ Tenant ID matches
4. ✅ top_k > 0 in tool config

### CORS Errors in Browser

**Solution**: Update `.env`
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,file://
```

Then restart: `docker-compose restart app`

---

## 📊 Performance Metrics

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| **Query embedding** | 50-100ms | all-MiniLM-L6-v2, CPU |
| **PgVector search** | 10-30ms | 700 chunks, top_k=7 |
| **LLM response** | 1-3s | Streaming, GPT-4o-mini |
| **Tool execution** | 100-500ms | HTTP GET/POST |
| **Full chat flow** | 2-5s | End to end |

---

## 🔐 Security Checklist

### Development (Current)
- ⚠️ `DISABLE_AUTH=true` - No JWT validation
- ⚠️ Default passwords (postgres:123456)
- ⚠️ CORS allows all origins
- ⚠️ Hardcoded API keys in .env

### Production (TODO)
- [ ] `DISABLE_AUTH=false` + real JWT keys
- [ ] Strong database password
- [ ] Restrict CORS origins
- [ ] Use Docker secrets for API keys
- [ ] Enable PostgreSQL SSL
- [ ] Rate limiting per tenant
- [ ] Audit logging
- [ ] Input validation (SQL injection, XSS)

---

## 📚 Key Files Quick Reference

| What You Need | File Path | Line(s) |
|---------------|-----------|---------|
| **Main app entry** | `src/main.py` | All |
| **Chat endpoint** | `src/api/chat.py` | 50-120 |
| **Supervisor routing** | `src/services/supervisor_agent.py` | 40-80 |
| **Agent execution** | `src/services/domain_agents.py` | 60-150 |
| **Tool loading** | `src/services/tool_loader.py` | 21-28 (registry), 77 (lookup) |
| **RAG search** | `src/services/rag_service.py` | 80-120 |
| **Embedding** | `src/services/embedding_service.py` | 55-67 (embed methods) |
| **LLM clients** | `src/services/llm_manager.py` | 50-120 |
| **Database models** | `src/models/*.py` | All |
| **Migration** | `alembic/versions/20251104_001_...py` | 295-330 (prompt) |
| **Environment** | `.env` | All |
| **Docker config** | `docker-compose.yml` | All |

---

## 💡 Best Practices

### When Adding New Tools
1. ✅ Use existing base types (HTTP_GET/POST) when possible
2. ✅ Test in development first
3. ✅ Document input schema clearly
4. ✅ Add error handling
5. ✅ Consider tenant isolation

### When Modifying Agents
1. ✅ Test prompt changes in playground first
2. ✅ Clear Redis cache after updates
3. ✅ Verify LLM can parse tool schemas
4. ✅ Monitor token usage
5. ✅ Keep prompts focused and clear

### When Scaling
1. ✅ Enable connection pooling (already configured)
2. ✅ Add caching layers
3. ✅ Use read replicas for PostgreSQL
4. ✅ Scale app horizontally (stateless)
5. ✅ Monitor Redis memory usage

---

## 🎓 Learning Resources

### Understanding the Codebase
1. Start with: `src/main.py` → `src/api/chat.py`
2. Follow flow: SupervisorAgent → DomainAgent → Tools
3. Read: `DYNAMIC_TOOL_LOADING.md` for tool system
4. Read: `DOCKER_SETUP_README.md` for deployment

### Key Concepts
- **LangChain**: Framework for LLM apps
- **LangGraph**: State management for agents
- **PgVector**: PostgreSQL vector extension
- **Multi-tenancy**: Tenant ID filtering everywhere
- **RAG**: Retrieval-Augmented Generation

### External Docs
- LangChain: https://python.langchain.com/docs
- PgVector: https://github.com/pgvector/pgvector
- FastAPI: https://fastapi.tiangolo.com
- Sentence Transformers: https://www.sbert.net

---

## 🔄 Maintenance

### Daily
- [ ] Monitor Docker logs: `docker-compose logs -f app`
- [ ] Check error rates in structured logs
- [ ] Verify RAG query performance

### Weekly
- [ ] Review agent performance metrics
- [ ] Check Redis memory usage
- [ ] Clear stale cache keys if needed

### Monthly
- [ ] Update dependencies: `pip list --outdated`
- [ ] Review and archive old sessions
- [ ] Optimize PgVector indexes if needed
- [ ] Review and update agent prompts based on feedback

---

## 🆘 Support

### Common Issues
1. **Tool not found**: See `DYNAMIC_TOOL_LOADING.md`
2. **Agent not routing**: Check supervisor agent logs
3. **RAG no results**: Verify documents ingested
4. **CORS errors**: Update `.env` CORS_ORIGINS

### Getting Help
1. Check logs: `docker-compose logs -f`
2. Read this summary for architecture understanding
3. Review specific component documentation
4. Test with curl commands first

---

## ✅ Quick Start Checklist

```bash
# 1. Start Docker
cd backend
docker-compose up -d --build

# 2. Wait for services (30 seconds)
docker-compose ps

# 3. Run migrations
docker-compose exec app alembic upgrade head

# 4. Update API key
docker-compose exec app python update_api_key.py

# 5. Ingest PDF
docker-compose exec app python ingest_etms_pdf.py

# 6. Get tenant ID
docker-compose exec app python -c "from src.database import SessionLocal; from src.models.tenant import Tenant; db = SessionLocal(); tenant = db.query(Tenant).first(); print(f'Tenant ID: {tenant.tenant_id}')"

# 7. Test chat
curl -X POST "http://localhost:8000/api/<tenant-id>/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hướng dẫn tạo đơn hàng FCL", "user_id": "test"}'

# 8. Open test chatbot
# Open: backend/test-chatbot.html in browser
```

---

## 📖 Summary

This codebase implements a production-ready multi-tenant chatbot framework with:

- ✅ **Dynamic agent routing** (supervisor → domain agents)
- ✅ **Database-driven configuration** (agents, tools, permissions)
- ✅ **Vietnamese-optimized RAG** (all-MiniLM-L6-v2, pgvector)
- ⚠️ **Partially dynamic tool loading** (instances yes, types require code)
- ✅ **Multi-tenant isolation** (database + cache layers)
- ✅ **Production-ready architecture** (Docker, health checks, caching)

**Key Limitation**: Tool handler registry is hardcoded (see DYNAMIC_TOOL_LOADING.md for fix)

**Key Strength**: Everything else is database-driven and can be updated without redeployment!
