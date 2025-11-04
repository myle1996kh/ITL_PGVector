# Quick Start Guide - AgentHub Chatbot

**Get running in 10 minutes**
**Last Updated**: 2025-11-03

---

## Prerequisites

- Python 3.11+
- Docker Desktop (for PostgreSQL, Redis, ChromaDB)
- Git

---

## Step 1: Clone and Setup (2 minutes)

```bash
# Navigate to project
cd c:\Users\gensh\Downloads\ITL_Base_28.10\backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Start Services (2 minutes)

```bash
# Start PostgreSQL, Redis, ChromaDB with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                STATUS
# postgres            Up
# redis               Up
# chromadb            Up
```

---

## Step 3: Setup Database (2 minutes)

```bash
# Run database migrations
alembic upgrade head

# Verify tables created
psql -h localhost -U agenthub -d agenthub -c "\dt"

# Expected: 13 tables (tenants, agents, tools, sessions, etc.)
```

---

## Step 4: Start API Server (1 minute)

```bash
# Start FastAPI server
python src/main.py

# Or with uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Server starts at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

---

## Step 5: Test First Chat Query (3 minutes)

### Option A: Using Swagger UI (Easiest)

1. Open browser: http://localhost:8000/docs
2. Find `POST /api/{tenant_id}/test/chat` endpoint
3. Click "Try it out"
4. Fill in:
   - `tenant_id`: Get from database (see below)
   - Request body:
   ```json
   {
     "message": "What is the debt for customer MST 0123456789?",
     "user_id": "test-user"
   }
   ```
5. Click "Execute"
6. See response with agent routing and tool execution!

### Option B: Using curl

```bash
# Get tenant_id from database first
psql -h localhost -U agenthub -d agenthub \
  -c "SELECT tenant_id, name FROM tenants LIMIT 1;"

# Use tenant_id in request
curl -X POST "http://localhost:8000/api/{TENANT_ID}/test/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the debt for customer MST 0123456789?",
    "user_id": "test-user"
  }'
```

### Option C: Using Python

```python
import requests

# Get tenant_id from database
TENANT_ID = "your-tenant-id-here"

response = requests.post(
    f"http://localhost:8000/api/{TENANT_ID}/test/chat",
    json={
        "message": "What is the debt for customer MST 0123456789?",
        "user_id": "test-user"
    }
)

print(response.json())
```

---

## Expected Response

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "660e8400-e29b-41d4-a716-446655440000",
  "response": "Customer MST 0123456789 has total debt of $15,432.50...",
  "agent": "AgentDebt",
  "metadata": {
    "llm_model": "gpt-4o-mini",
    "tool_calls": ["get_customer_debt"],
    "extracted_entities": {"mst": "0123456789"},
    "agent_id": "uuid-agent-debt",
    "tenant_id": "your-tenant-id"
  }
}
```

---

## Understanding What Just Happened

```
Your Message
    │
    ▼
[SupervisorAgent]
    ├─ Detected language: English
    ├─ Detected intent: Debt query
    └─ Routed to: AgentDebt
         │
         ▼
    [AgentDebt]
         ├─ Extracted entity: MST = 0123456789
         ├─ Called tool: get_customer_debt(mst="0123456789")
         │    └─ Made HTTP GET to external API
         ├─ Received debt data
         └─ Formatted response
```

---

## Quick Reference Commands

### Database Access
```bash
# Connect to PostgreSQL
psql -h localhost -U agenthub -d agenthub

# List tenants
SELECT tenant_id, name, status FROM tenants;

# List available agents
SELECT agent_id, name, description FROM agent_configs WHERE is_active = TRUE;

# Check tenant permissions
SELECT ac.name AS agent_name, tap.enabled
FROM tenant_agent_permissions tap
JOIN agent_configs ac ON tap.agent_id = ac.agent_id
WHERE tap.tenant_id = 'your-tenant-id';
```

### Service Management
```bash
# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs postgres
docker-compose logs redis

# Restart services
docker-compose restart

# Clear Redis cache
redis-cli FLUSHALL
```

### Development Workflow
```bash
# Run tests
pytest tests/unit/

# Check code quality
ruff check src/

# Format code
black src/

# Create database migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Common Test Scenarios

### Scenario 1: Customer Debt Query
```json
{
  "message": "Show me debt for customer MST 0104985841",
  "user_id": "user-123"
}
```
Expected agent: **AgentDebt**

### Scenario 2: Shipment Tracking
```json
{
  "message": "Track shipment ABC123",
  "user_id": "user-123"
}
```
Expected agent: **AgentShipment**

### Scenario 3: Knowledge Base Query
```json
{
  "message": "What is our return policy?",
  "user_id": "user-123"
}
```
Expected agent: **AgentAnalysis** (if RAG configured)

### Scenario 4: Multi-Language (Vietnamese)
```json
{
  "message": "Tra cứu công nợ mst 0104985841",
  "user_id": "user-123"
}
```
Expected: Response in Vietnamese

---

## Configuration Overview

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://agenthub:secret@localhost:5432/agenthub

# Redis
REDIS_URL=redis://localhost:6379

# ChromaDB
CHROMA_URL=http://localhost:8001

# Security (for production)
JWT_PUBLIC_KEY=<RS256 public key>
FERNET_KEY=<encryption key>

# Development
DISABLE_AUTH=true  # For testing without JWT
TEST_BEARER_TOKEN=<external API token>
```

### Key Configuration Files

| File | Purpose |
|------|---------|
| `backend/src/config.py` | Application configuration |
| `backend/.env` | Environment variables |
| `backend/alembic.ini` | Database migration config |
| `backend/docker-compose.yml` | Service definitions |
| `backend/requirements.txt` | Python dependencies |

---

## Troubleshooting

### Problem: Services won't start
```bash
# Check Docker is running
docker ps

# Check ports are available
netstat -an | findstr "5432"  # PostgreSQL
netstat -an | findstr "6379"  # Redis
netstat -an | findstr "8000"  # FastAPI

# Kill conflicting processes or change ports in docker-compose.yml
```

### Problem: Database connection error
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check connection
psql -h localhost -U agenthub -d agenthub

# If password error, check docker-compose.yml POSTGRES_PASSWORD
```

### Problem: "No LLM configured"
```bash
# Check tenant_llm_configs table
psql -h localhost -U agenthub -d agenthub \
  -c "SELECT * FROM tenant_llm_configs;"

# If empty, run seed script or configure via admin API
```

### Problem: "No agents available"
```bash
# Check agent permissions
psql -h localhost -U agenthub -d agenthub \
  -c "SELECT * FROM tenant_agent_permissions WHERE enabled = TRUE;"

# If empty, grant permissions (see Tenant Onboarding Guide)
```

---

## Next Steps

### For Developers
1. Read **[Developer Setup](06_DEVELOPER_SETUP.md)** for detailed environment setup
2. Study **[System Architecture](02_SYSTEM_ARCHITECTURE.md)** to understand components
3. Review **[API Reference](05_API_REFERENCE.md)** for all endpoints
4. Check **[Testing Guide](12_TESTING_GUIDE.md)** for writing tests

### For Administrators
1. Review **[Tenant Onboarding Guide](03_TENANT_ONBOARDING_GUIDE.md)** to add tenants
2. Understand **[Security Guide](08_SECURITY_GUIDE.md)** for production setup
3. Study **[Operations Guide](11_OPERATIONS_GUIDE.md)** for monitoring
4. Follow **[Deployment Guide](07_DEPLOYMENT_GUIDE.md)** for production

### For Integrators
1. Read **[Tool Development](09_TOOL_DEVELOPMENT.md)** to create custom tools
2. Study **[Agent Development](10_AGENT_DEVELOPMENT.md)** for custom agents
3. Review **[API Reference](05_API_REFERENCE.md)** for integration
4. Check existing tools in `backend/src/tools/` for examples

---

## Helpful Links

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **GitHub Issues**: (Add your repository link)
- **LangChain Docs**: https://python.langchain.com/docs/introduction/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

**You're ready to build!** 🚀

For questions, check **[Troubleshooting FAQ](14_TROUBLESHOOTING_FAQ.md)** or review the comprehensive documentation.
