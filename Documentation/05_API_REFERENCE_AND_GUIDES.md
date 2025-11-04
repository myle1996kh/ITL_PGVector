# API Reference & Essential Guides

**Document Version**: 1.0
**Last Updated**: 2025-11-03
**Base URL**: `http://localhost:8000` (development) | `https://api.example.com` (production)

---

## Table of Contents

1. [API Reference](#api-reference)
2. [Authentication & Security](#authentication--security)
3. [Developer Setup](#developer-setup)
4. [Troubleshooting & FAQ](#troubleshooting--faq)

---

# API Reference

## Authentication

All endpoints (except `/health` and `/test/*`) require JWT authentication.

### Headers
```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### JWT Token Format
```json
{
  "sub": "user-123",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "roles": ["user"],
  "exp": 1699999999,
  "iat": 1699900000
}
```

---

## Chat Endpoints

### POST /api/{tenant_id}/chat
**Purpose**: Send message and get agent response
**Authentication**: Required (JWT)

**Request**:
```http
POST /api/550e8400-e29b-41d4-a716-446655440000/chat
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "message": "What is the debt for customer MST 0123456789?",
  "session_id": "optional-session-uuid",  // Optional: continue existing conversation
  "user_id": "user-123"  // Optional: extracted from JWT if not provided
}
```

**Response** (200 OK):
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440000",
  "message_id": "770e8400-e29b-41d4-a716-446655440000",
  "response": "Customer MST 0123456789 has total debt of $15,432.50, with $5,200.00 overdue...",
  "agent": "AgentDebt",
  "metadata": {
    "llm_model": "gpt-4o-mini",
    "tool_calls": ["get_customer_debt"],
    "extracted_entities": {
      "mst": "0123456789"
    },
    "agent_id": "uuid-agent-debt",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "intent": "customer_debt_query",
    "language": "en",
    "tokens": {
      "input": 120,
      "output": 80
    },
    "duration_ms": 1234
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired JWT token
- `403 Forbidden`: Tenant_id mismatch or unauthorized access
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Agent/tool execution error

---

### POST /api/{tenant_id}/test/chat
**Purpose**: Test endpoint without JWT authentication
**Authentication**: None (development only)
**Use Case**: Testing, development, debugging

**Request**:
```http
POST /api/550e8400-e29b-41d4-a716-446655440000/test/chat
Content-Type: application/json

{
  "message": "Show me debt for MST 0104985841",
  "user_id": "test-user"
}
```

**Response**: Same as `/chat` endpoint above

**Security Note**: Disable in production by setting `DISABLE_AUTH=false`

---

## Session Endpoints

### GET /api/{tenant_id}/sessions
**Purpose**: List user's conversation sessions
**Authentication**: Required (JWT)

**Request**:
```http
GET /api/550e8400-e29b-41d4-a716-446655440000/sessions?user_id=user-123&limit=10&offset=0
Authorization: Bearer eyJhbGc...
```

**Query Parameters**:
- `user_id` (optional): Filter by user (defaults to JWT user)
- `limit` (optional): Results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "sessions": [
    {
      "session_id": "660e8400-e29b-41d4-a716-446655440000",
      "user_id": "user-123",
      "agent_id": "uuid-agent-debt",
      "agent_name": "AgentDebt",
      "created_at": "2025-11-03T10:00:00Z",
      "last_message_at": "2025-11-03T10:05:30Z",
      "message_count": 8
    },
    ...
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

---

### GET /api/{tenant_id}/sessions/{session_id}
**Purpose**: Get session details with message history
**Authentication**: Required (JWT)

**Request**:
```http
GET /api/550e8400-e29b-41d4-a716-446655440000/sessions/660e8400-e29b-41d4-a716-446655440000
Authorization: Bearer eyJhbGc...
```

**Response** (200 OK):
```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "agent_id": "uuid-agent-debt",
  "created_at": "2025-11-03T10:00:00Z",
  "last_message_at": "2025-11-03T10:05:30Z",
  "messages": [
    {
      "message_id": "msg-1",
      "role": "user",
      "content": "What is debt for MST 0123456789?",
      "timestamp": "2025-11-03T10:00:00Z"
    },
    {
      "message_id": "msg-2",
      "role": "assistant",
      "content": "Customer MST 0123456789 has...",
      "timestamp": "2025-11-03T10:00:02Z",
      "metadata": {
        "agent": "AgentDebt",
        "tool_calls": ["get_customer_debt"]
      }
    },
    ...
  ]
}
```

---

## Admin Endpoints

### Agent Management

#### GET /api/admin/agents
**Purpose**: List all agents
**Authentication**: Required (Admin JWT)

**Response** (200 OK):
```json
{
  "agents": [
    {
      "agent_id": "uuid-agent-debt",
      "name": "AgentDebt",
      "description": "Handles customer debt queries",
      "llm_model": "gpt-4o-mini",
      "is_active": true,
      "tool_count": 3,
      "created_at": "2025-10-28T00:00:00Z"
    },
    ...
  ]
}
```

#### POST /api/admin/agents
**Purpose**: Create new agent
**Authentication**: Required (Admin JWT)

**Request**:
```http
POST /api/admin/agents
Authorization: Bearer <admin_jwt>
Content-Type: application/json

{
  "name": "AgentInventory",
  "prompt_template": "You are an inventory management assistant...",
  "llm_model_id": "uuid-gpt4o-mini",
  "default_output_format_id": "uuid-format-json",
  "description": "Handles warehouse inventory queries",
  "handler_class": "services.domain_agents.DomainAgent"
}
```

**Response** (201 Created):
```json
{
  "agent_id": "uuid-new-agent",
  "name": "AgentInventory",
  "message": "Agent created successfully"
}
```

#### PATCH /api/admin/agents/{agent_id}
**Purpose**: Update agent configuration
**Authentication**: Required (Admin JWT)

**Request**:
```http
PATCH /api/admin/agents/uuid-agent-debt
Authorization: Bearer <admin_jwt>
Content-Type: application/json

{
  "prompt_template": "Updated prompt...",
  "is_active": true
}
```

---

### Tool Management

#### POST /api/admin/tools
**Purpose**: Create new tool
**Authentication**: Required (Admin JWT)

**Request**:
```http
POST /api/admin/tools
Authorization: Bearer <admin_jwt>
Content-Type: application/json

{
  "name": "get_warehouse_inventory",
  "base_tool_id": "uuid-http-get",
  "config": {
    "endpoint": "https://erp.example.com/api/inventory/{sku}",
    "method": "GET",
    "headers": {
      "X-API-Version": "v2"
    },
    "timeout": 30
  },
  "input_schema": {
    "type": "object",
    "properties": {
      "sku": {
        "type": "string",
        "pattern": "^SKU-[0-9]{5}$"
      }
    },
    "required": ["sku"]
  },
  "output_format_id": "uuid-format-json",
  "description": "Get warehouse inventory by SKU"
}
```

**Response** (201 Created):
```json
{
  "tool_id": "uuid-new-tool",
  "name": "get_warehouse_inventory",
  "message": "Tool created successfully"
}
```

---

### Tenant Management

#### POST /api/admin/tenants
**Purpose**: Create new tenant
**Authentication**: Required (Admin JWT)

**Request**:
```http
POST /api/admin/tenants
Authorization: Bearer <admin_jwt>
Content-Type: application/json

{
  "name": "Acme Corporation",
  "domain": "acme.com",
  "status": "active"
}
```

#### POST /api/admin/tenants/{tenant_id}/permissions/agents
**Purpose**: Grant agent permissions to tenant

**Request**:
```json
{
  "agent_permissions": [
    {"agent_id": "uuid-agent-debt", "enabled": true},
    {"agent_id": "uuid-agent-shipment", "enabled": true}
  ]
}
```

---

### Knowledge Base Management

#### POST /api/admin/knowledge/upload
**Purpose**: Upload documents to ChromaDB for RAG
**Authentication**: Required (Admin JWT)

**Request**:
```http
POST /api/admin/knowledge/upload
Authorization: Bearer <admin_jwt>
Content-Type: multipart/form-data

collection_name: company_policies
files: [file1.pdf, file2.docx, file3.txt]
tenant_id: 550e8400-e29b-41d4-a716-446655440000
```

**Response** (200 OK):
```json
{
  "collection_name": "company_policies",
  "documents_uploaded": 3,
  "total_chunks": 127,
  "message": "Documents uploaded successfully"
}
```

---

## Health Check

### GET /health
**Purpose**: Service health status
**Authentication**: None

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-03T10:00:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "chromadb": "connected"
  }
}
```

---

# Authentication & Security

## JWT Authentication

### Token Generation (External Auth Provider)

The system expects JWT tokens to be generated by an external authentication provider (SSO, OAuth2).

**Required Claims**:
```json
{
  "sub": "user-123",           // User ID
  "tenant_id": "tenant-uuid",  // Tenant ID
  "email": "user@example.com",
  "roles": ["user"],           // Or ["admin"]
  "exp": 1699999999,           // Expiration timestamp
  "iat": 1699900000            // Issued at timestamp
}
```

### Token Validation

**Middleware** (`backend/src/middleware/auth.py`):
1. Extract token from `Authorization: Bearer <token>` header
2. Validate RS256 signature using `JWT_PUBLIC_KEY`
3. Check expiration (`exp` claim)
4. Verify `tenant_id` matches URL parameter
5. Attach user context to request

**Example Public Key** (.env):
```env
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----
```

---

## API Key Encryption

### Fernet Symmetric Encryption

Tenant LLM API keys are encrypted before storage in `tenant_llm_configs` table.

**Encryption** (on tenant onboarding):
```python
from cryptography.fernet import Fernet

# Generate key (one-time setup)
FERNET_KEY = Fernet.generate_key()  # Store in .env

# Encrypt API key
fernet = Fernet(FERNET_KEY)
encrypted_key = fernet.encrypt("sk-abc123...".encode())

# Store in database
tenant_llm_config.encrypted_api_key = encrypted_key.decode()
```

**Decryption** (at runtime):
```python
fernet = Fernet(FERNET_KEY)
plaintext_key = fernet.decrypt(encrypted_key.encode()).decode()
llm = ChatOpenAI(api_key=plaintext_key)
```

**Key Rotation**:
1. Generate new `FERNET_KEY`
2. Decrypt all API keys with old key
3. Re-encrypt with new key
4. Update `.env` with new key
5. Restart application

---

## Security Best Practices

### Development
- Use `DISABLE_AUTH=true` for local testing only
- Never commit `.env` files to version control
- Use `.env.example` template with placeholder values

### Production
- Enable `DISABLE_AUTH=false`
- Use strong, rotated JWT keys (RS256)
- Rotate `FERNET_KEY` quarterly
- Enable HTTPS/TLS 1.3
- Set rate limits per tenant
- Monitor for suspicious activity
- Implement IP whitelisting (optional)

---

# Developer Setup

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7.x
- Docker Desktop
- Git

---

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd ITL_Base_28.10/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
cp .env.example .env

# Edit .env with your configuration
# Key variables:
# - DATABASE_URL
# - REDIS_URL
# - CHROMA_URL
# - JWT_PUBLIC_KEY
# - FERNET_KEY
# - DISABLE_AUTH=true (for development)
```

### 5. Start Services
```bash
# Start PostgreSQL, Redis, ChromaDB
docker-compose up -d

# Verify services
docker-compose ps
```

### 6. Initialize Database
```bash
# Run migrations
alembic upgrade head

# Verify tables
psql -h localhost -U agenthub -d agenthub -c "\dt"
```

### 7. Start API Server
```bash
# Development mode (auto-reload)
python src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

## Development Workflow

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_chat_api.py

# With coverage
pytest --cov=src --cov-report=term --cov-fail-under=80

# Verbose output
pytest -v -s
```

### Code Quality
```bash
# Lint code
ruff check src/

# Format code
black src/

# Type checking
mypy src/

# All checks
ruff check src/ && black --check src/ && mypy src/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history

# Check current version
alembic current
```

### Viewing Logs
```bash
# Application logs
docker-compose logs -f backend

# PostgreSQL logs
docker-compose logs postgres

# Redis logs
docker-compose logs redis

# All logs
docker-compose logs -f
```

---

# Troubleshooting & FAQ

## Common Issues

### Issue 1: "Database connection failed"

**Symptoms**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Solutions**:
```bash
# 1. Check PostgreSQL is running
docker-compose ps postgres

# 2. Check DATABASE_URL in .env
cat .env | grep DATABASE_URL
# Should be: postgresql://agenthub:secret@localhost:5432/agenthub

# 3. Test connection manually
psql -h localhost -U agenthub -d agenthub

# 4. Restart PostgreSQL
docker-compose restart postgres

# 5. Check logs
docker-compose logs postgres
```

---

### Issue 2: "No LLM configured for tenant"

**Symptoms**:
```
HTTPException: 500 - No LLM configuration found for tenant
```

**Solutions**:
```sql
-- 1. Check tenant_llm_configs table
SELECT * FROM tenant_llm_configs WHERE tenant_id = 'your-tenant-id';

-- 2. If missing, create config
INSERT INTO tenant_llm_configs (tenant_id, llm_model_id, encrypted_api_key)
VALUES (
  'your-tenant-id',
  (SELECT llm_model_id FROM llm_models WHERE model_name = 'gpt-4o-mini'),
  'gAAAAABf...'  -- Encrypted API key
);

-- 3. Clear Redis cache
redis-cli DEL "agenthub:your-tenant-id:llm"
```

---

### Issue 3: "Tool execution failed: 401 Unauthorized"

**Symptoms**:
```
Tool 'get_customer_debt' failed: 401 Unauthorized from external API
```

**Causes**:
- User JWT not injected correctly
- External API credentials invalid
- TEST_BEARER_TOKEN not set

**Solutions**:
```bash
# 1. Check TEST_BEARER_TOKEN in .env
cat .env | grep TEST_BEARER_TOKEN

# 2. Verify tool config includes JWT injection
psql -h localhost -U agenthub -d agenthub
SELECT config FROM tool_configs WHERE name = 'get_customer_debt';
# Should have: "inject_jwt": true

# 3. Test external API manually
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://erp.example.com/api/customers/0123456789/debt

# 4. Check backend logs
docker-compose logs backend | grep "Tool execution"
```

---

### Issue 4: "Agent returns UNCLEAR intent"

**Symptoms**:
SupervisorAgent cannot determine which agent to route to

**Solutions**:
1. **Check Agent Descriptions**: Ensure agent descriptions are clear and distinct
```sql
SELECT name, description FROM agent_configs WHERE is_active = TRUE;
```

2. **Improve Query Clarity**: Use more specific language
```
❌ "Check this" → Unclear
✅ "Check debt for customer MST 0123456789" → Clear
```

3. **Verify Agent Permissions**:
```sql
SELECT ac.name
FROM agent_configs ac
JOIN tenant_agent_permissions tap ON ac.agent_id = tap.agent_id
WHERE tap.tenant_id = 'your-tenant-id' AND tap.enabled = TRUE;
```

4. **Review SupervisorAgent Logs**:
```bash
docker-compose logs backend | grep "SupervisorAgent"
# Look for intent detection LLM response
```

---

### Issue 5: "Redis connection refused"

**Symptoms**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions**:
```bash
# 1. Check Redis is running
docker-compose ps redis

# 2. Test connection
redis-cli ping
# Should return: PONG

# 3. Check REDIS_URL in .env
cat .env | grep REDIS_URL
# Should be: redis://localhost:6379

# 4. Restart Redis
docker-compose restart redis

# 5. Clear all cache (if needed)
redis-cli FLUSHALL
```

---

### Issue 6: "Alembic migration conflicts"

**Symptoms**:
```
sqlalchemy.exc.ProgrammingError: relation "table_name" already exists
```

**Solutions**:
```bash
# 1. Check current migration version
alembic current

# 2. View migration history
alembic history

# 3. Rollback to clean state
alembic downgrade base

# 4. Re-run migrations
alembic upgrade head

# 5. If persistent, reset database (⚠️ destroys all data)
docker-compose down -v
docker-compose up -d
alembic upgrade head
```

---

### Issue 7: "Permission denied for tool"

**Symptoms**:
```
Tool 'get_customer_debt' not permitted for tenant
```

**Solutions**:
```sql
-- 1. Check tool permission
SELECT * FROM tenant_tool_permissions
WHERE tenant_id = 'your-tenant-id'
  AND tool_id = (SELECT tool_id FROM tool_configs WHERE name = 'get_customer_debt');

-- 2. If missing, grant permission
INSERT INTO tenant_tool_permissions (tenant_id, tool_id, enabled)
VALUES (
  'your-tenant-id',
  (SELECT tool_id FROM tool_configs WHERE name = 'get_customer_debt'),
  TRUE
);

-- 3. Clear cache
redis-cli DEL "agenthub:your-tenant-id:cache:permissions:tools"
```

---

## FAQ

### Q: How do I add a new tenant?
**A**: Follow the [Tenant Onboarding Guide](03_TENANT_ONBOARDING_GUIDE.md) for complete steps.

### Q: How do I create a custom agent?
**A**: Use `POST /api/admin/agents` endpoint or insert directly into `agent_configs` table. See [Agent Development Guide](10_AGENT_DEVELOPMENT.md).

### Q: Can tenants use different LLM providers?
**A**: Yes! Each tenant can configure their own LLM provider (OpenAI, Gemini, Claude, OpenRouter) in `tenant_llm_configs` table.

### Q: How do I clear the cache?
**A**:
```bash
# Clear all cache
redis-cli FLUSHALL

# Clear specific tenant cache
redis-cli DEL "agenthub:tenant-id:*"

# Clear agent cache
POST /api/admin/agents/reload
```

### Q: How do I monitor costs per tenant?
**A**: Query `messages` table metadata for token counts:
```sql
SELECT
  t.name,
  SUM((m.metadata->>'tokens'->>'input')::int) as input_tokens,
  SUM((m.metadata->>'tokens'->>'output')::int) as output_tokens
FROM tenants t
JOIN sessions s ON t.tenant_id = s.tenant_id
JOIN messages m ON s.session_id = m.session_id
WHERE m.role = 'assistant'
  AND m.timestamp >= NOW() - INTERVAL '30 days'
GROUP BY t.name;
```

### Q: What's the difference between `/chat` and `/test/chat`?
**A**:
- `/chat`: Requires JWT authentication (production)
- `/test/chat`: No authentication required (development only)

### Q: How do I rotate encryption keys?
**A**: See [Security Guide](08_SECURITY_GUIDE.md) - Key Rotation section.

---

## Getting Help

### Resources
- **Documentation**: `Documentation/` folder
- **API Docs**: http://localhost:8000/docs
- **Logs**: `docker-compose logs -f`
- **Database**: `psql -h localhost -U agenthub -d agenthub`

### Support Channels
- Check [Troubleshooting & FAQ](#troubleshooting--faq)
- Review code comments in `backend/src/`
- Consult LangChain docs: https://python.langchain.com/
- FastAPI docs: https://fastapi.tiangolo.com/

---

**Document Status**: ✅ Complete
**Last Updated**: 2025-11-03
**Maintained By**: Development Team
