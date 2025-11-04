# Database Schema & Entity Relationship Diagram

**Document Version**: 1.0
**Last Updated**: 2025-11-03
**Database**: PostgreSQL 15+
**Tables**: 13 core tables

---

## Complete ERD Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION LAYER                          │
└────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────────┐       ┌────────────┐
│   tenants    │◄──1:1─┤tenant_llm_configs├──N:1─►│ llm_models │
├──────────────┤       ├──────────────────┤       ├────────────┤
│ tenant_id PK │       │ config_id PK     │       │llm_model_id│
│ name         │       │ tenant_id FK     │       │ provider   │
│ domain       │       │ llm_model_id FK  │       │ model_name │
│ status       │       │ encrypted_api_key│       │ cost_per_  │
│ created_at   │       │ rate_limit_rpm   │       │  1k_tokens │
└──────┬───────┘       └──────────────────┘       └────────────┘
       │
       │ 1:N
       ├─────────────────────────────────┬────────────────────────┐
       │                                 │                        │
       ▼                                 ▼                        ▼
┌──────────────────┐            ┌─────────────────────┐  ┌────────────────────┐
│tenant_agent_perms│            │tenant_tool_perms    │  │    sessions        │
├──────────────────┤            ├─────────────────────┤  ├────────────────────┤
│tenant_id PK,FK   │            │tenant_id PK,FK      │  │session_id PK       │
│agent_id PK,FK    │            │tool_id PK,FK        │  │tenant_id FK        │
│enabled           │            │enabled              │  │user_id             │
│output_override_id│            │created_at           │  │agent_id FK         │
└────────┬─────────┘            └──────────┬──────────┘  │created_at          │
         │                                 │              │last_message_at     │
         │ N:1                             │ N:1          └────────┬───────────┘
         ▼                                 ▼                       │
┌────────────────┐                  ┌────────────────┐            │ 1:N
│ agent_configs  │                  │ tool_configs   │            ▼
├────────────────┤                  ├────────────────┤    ┌───────────────┐
│agent_id PK     │◄────N:M─────────►│tool_id PK      │    │   messages    │
│name            │   (agent_tools)  │name            │    ├───────────────┤
│prompt_template │                  │base_tool_id FK │    │message_id PK  │
│llm_model_id FK │                  │config JSONB    │    │session_id FK  │
│default_output_ │                  │input_schema    │    │role           │
│  format_id FK  │                  │output_format_id│    │content        │
│description     │                  │description     │    │timestamp      │
│is_active       │                  │is_active       │    │metadata JSONB │
└────────┬───────┘                  └────────┬───────┘    └───────────────┘
         │                                   │
         │ N:1                               │ N:1
         │                          ┌────────┴─────────┐
         │                          │                  │
         ▼                          ▼                  ▼
┌──────────────┐            ┌──────────────┐   ┌──────────────┐
│ llm_models   │            │ base_tools   │   │output_formats│
├──────────────┤            ├──────────────┤   ├──────────────┤
│llm_model_id  │            │base_tool_id  │   │format_id PK  │
│provider      │            │type          │   │name          │
│model_name    │            │handler_class │   │schema JSONB  │
│context_window│            │description   │   │renderer_hint │
└──────────────┘            └──────────────┘   └──────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   JUNCTION TABLE                                │
└────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ agent_tools  │  (Many-to-Many: agents ↔ tools)
├──────────────┤
│agent_id PK,FK│
│tool_id PK,FK │
│priority      │  ← Controls tool visibility (lower = higher priority)
│created_at    │
└──────────────┘

┌────────────────────────────────────────────────────────────────┐
│                  STATE MANAGEMENT                               │
└────────────────────────────────────────────────────────────────┘

┌──────────────┐
│ checkpoints  │  (LangGraph PostgresSaver - auto-managed)
├──────────────┤
│thread_id PK  │  ← tenant_{id}__user_{id}__session_{id}
│checkpoint_id │
│parent_id     │
│checkpoint    │  (BYTEA - serialized state)
│metadata JSONB│
└──────────────┘
```

---

## Table Details

### 1. tenants
**Purpose**: Organizations using the system
**Relationships**: Hub table connecting to all tenant-scoped data

```sql
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_domain ON tenants(domain);
```

**Sample Data**:
```sql
INSERT INTO tenants (tenant_id, name, domain, status)
VALUES
  ('550e8400-e29b-41d4-a716-446655440001', 'Acme Corp', 'acme.com', 'active'),
  ('550e8400-e29b-41d4-a716-446655440002', 'TechStart Inc', 'techstart.io', 'active');
```

---

### 2. llm_models
**Purpose**: Available LLM providers and models
**Relationships**: Referenced by tenant_llm_configs and agent_configs

```sql
CREATE TABLE llm_models (
    llm_model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    context_window INTEGER NOT NULL,
    cost_per_1k_input_tokens DECIMAL(10,6) NOT NULL,
    cost_per_1k_output_tokens DECIMAL(10,6) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    capabilities JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_llm_models_provider ON llm_models(provider, model_name);
CREATE INDEX idx_llm_models_active ON llm_models(is_active);
```

**Sample Data**:
```sql
INSERT INTO llm_models (llm_model_id, provider, model_name, context_window, cost_per_1k_input_tokens, cost_per_1k_output_tokens)
VALUES
  ('llm-1', 'openai', 'gpt-4o-mini', 128000, 0.00015, 0.0006),
  ('llm-2', 'openai', 'gpt-4o', 128000, 0.0025, 0.01),
  ('llm-3', 'gemini', 'gemini-1.5-pro', 1048576, 0.00125, 0.00375),
  ('llm-4', 'anthropic', 'claude-3-5-sonnet-20241022', 200000, 0.003, 0.015);
```

---

### 3. tenant_llm_configs
**Purpose**: Tenant-specific LLM settings and encrypted API keys
**Security**: API keys encrypted with Fernet before storage

```sql
CREATE TABLE tenant_llm_configs (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    llm_model_id UUID NOT NULL REFERENCES llm_models(llm_model_id),
    encrypted_api_key TEXT NOT NULL,
    rate_limit_rpm INTEGER DEFAULT 60,
    rate_limit_tpm INTEGER DEFAULT 10000,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id)  -- One LLM config per tenant
);

CREATE INDEX idx_tenant_llm_tenant ON tenant_llm_configs(tenant_id);
CREATE INDEX idx_tenant_llm_model ON tenant_llm_configs(llm_model_id);
```

---

### 4. base_tools
**Purpose**: Tool type templates
**Tool Types**: HTTP_GET, HTTP_POST, RAG, DB_QUERY, OCR

```sql
CREATE TABLE base_tools (
    base_tool_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL UNIQUE,
    handler_class VARCHAR(255) NOT NULL,
    description TEXT,
    default_config_schema JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Sample Data**:
```sql
INSERT INTO base_tools (base_tool_id, type, handler_class, description)
VALUES
  ('base-1', 'HTTP_GET', 'tools.http.HTTPGetTool', 'HTTP GET request tool'),
  ('base-2', 'HTTP_POST', 'tools.http.HTTPPostTool', 'HTTP POST request tool'),
  ('base-3', 'RAG', 'tools.rag.RAGTool', 'RAG vector search tool'),
  ('base-4', 'DB_QUERY', 'tools.db.DBQueryTool', 'Database query tool'),
  ('base-5', 'OCR', 'tools.ocr.OCRTool', 'OCR document processing tool');
```

---

### 5. output_formats
**Purpose**: Response format definitions
**Formats**: structured_json, markdown_table, chart_data, summary_text

```sql
CREATE TABLE output_formats (
    format_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    schema JSONB,
    renderer_hint JSONB,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Sample Data**:
```sql
INSERT INTO output_formats (format_id, name, schema, renderer_hint)
VALUES
  ('fmt-1', 'structured_json', '{"type": "object"}', '{"type": "json"}'),
  ('fmt-2', 'markdown_table', '{"type": "string"}', '{"type": "table", "sortable": true}'),
  ('fmt-3', 'chart_data', '{"type": "object"}', '{"type": "chart", "chartType": "bar"}'),
  ('fmt-4', 'summary_text', '{"type": "string"}', '{"type": "text"}');
```

---

### 6. tool_configs
**Purpose**: Specific tool instances
**Configuration**: Endpoint, headers, input/output schemas

```sql
CREATE TABLE tool_configs (
    tool_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    base_tool_id UUID NOT NULL REFERENCES base_tools(base_tool_id),
    config JSONB NOT NULL,
    input_schema JSONB NOT NULL,
    output_format_id UUID REFERENCES output_formats(format_id),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_configs_base ON tool_configs(base_tool_id);
CREATE INDEX idx_tool_configs_active ON tool_configs(is_active);
```

**Example Tool Config**:
```json
{
  "endpoint": "https://erp.example.com/api/customers/{mst}/debt",
  "method": "GET",
  "headers": {"X-API-Version": "v1"},
  "timeout": 30
}
```

**Example Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "mst": {
      "type": "string",
      "description": "Customer tax code (10 digits)",
      "pattern": "^[0-9]{10}$"
    }
  },
  "required": ["mst"]
}
```

---

### 7. agent_configs
**Purpose**: Domain-specific agent configurations
**Agents**: AgentDebt, AgentShipment, AgentAnalysis, AgentOCR

```sql
CREATE TABLE agent_configs (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    prompt_template TEXT NOT NULL,
    llm_model_id UUID NOT NULL REFERENCES llm_models(llm_model_id),
    default_output_format_id UUID REFERENCES output_formats(format_id),
    handler_class VARCHAR(255),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_configs_name ON agent_configs(name);
CREATE INDEX idx_agent_configs_active ON agent_configs(is_active);
```

---

### 8. agent_tools
**Purpose**: Many-to-many relationship between agents and tools
**Priority**: Controls tool visibility (lower number = higher priority)

```sql
CREATE TABLE agent_tools (
    agent_id UUID NOT NULL REFERENCES agent_configs(agent_id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tool_configs(tool_id) ON DELETE CASCADE,
    priority INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (agent_id, tool_id)
);

CREATE INDEX idx_agent_tools_agent_priority ON agent_tools(agent_id, priority ASC);
CREATE INDEX idx_agent_tools_tool ON agent_tools(tool_id);
```

**Priority System**:
- System queries: `SELECT * FROM agent_tools WHERE agent_id = ? ORDER BY priority ASC LIMIT 5`
- Top 5 tools loaded (pre-filtered)
- LLM chooses semantically from filtered set

---

### 9. tenant_agent_permissions
**Purpose**: Enable agents for specific tenants
**Override**: Optional tenant-specific output format

```sql
CREATE TABLE tenant_agent_permissions (
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agent_configs(agent_id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    output_override_id UUID REFERENCES output_formats(format_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, agent_id)
);

CREATE INDEX idx_tenant_agent_perms_tenant ON tenant_agent_permissions(tenant_id, enabled);
CREATE INDEX idx_tenant_agent_perms_agent ON tenant_agent_permissions(agent_id);
```

---

### 10. tenant_tool_permissions
**Purpose**: Enable tools for specific tenants

```sql
CREATE TABLE tenant_tool_permissions (
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tool_configs(tool_id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, tool_id)
);

CREATE INDEX idx_tenant_tool_perms_tenant ON tenant_tool_permissions(tenant_id, enabled);
CREATE INDEX idx_tenant_tool_perms_tool ON tenant_tool_permissions(tool_id);
```

---

### 11. sessions
**Purpose**: Conversation sessions
**Thread ID Pattern**: `tenant_{id}__user_{id}__session_{id}`

```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    agent_id UUID REFERENCES agent_configs(agent_id),
    thread_id VARCHAR(500),  -- LangGraph thread identifier
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_sessions_tenant_user ON sessions(tenant_id, user_id, created_at DESC);
CREATE INDEX idx_sessions_thread ON sessions(thread_id);
```

---

### 12. messages
**Purpose**: Individual chat messages
**Metadata**: Stores intent, tool_calls, entities, token counts

```sql
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_messages_session_time ON messages(session_id, timestamp ASC);
CREATE INDEX idx_messages_role ON messages(role);
```

**Example Metadata**:
```json
{
  "intent": "customer_debt_query",
  "agent_used": "AgentDebt",
  "tool_calls": ["get_customer_debt"],
  "extracted_entities": {"mst": "0123456789"},
  "llm_model": "gpt-4o-mini",
  "token_count": {"input": 120, "output": 80},
  "duration_ms": 1234
}
```

---

### 13. checkpoints
**Purpose**: LangGraph conversation state persistence
**Managed By**: LangGraph PostgresSaver (auto-created)

```sql
-- Created automatically by LangGraph PostgresSaver.setup()
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    parent_id TEXT,
    checkpoint BYTEA NOT NULL,
    metadata JSONB,
    PRIMARY KEY (thread_id, checkpoint_id)
);

CREATE INDEX idx_checkpoints_parent ON checkpoints(parent_id);
```

---

## Key Queries

### Query 1: Get Tenant's Available Agents
```sql
SELECT ac.agent_id, ac.name, ac.description, tap.enabled
FROM agent_configs ac
JOIN tenant_agent_permissions tap ON ac.agent_id = tap.agent_id
WHERE tap.tenant_id = '550e8400-e29b-41d4-a716-446655440001'
  AND tap.enabled = TRUE
  AND ac.is_active = TRUE
ORDER BY ac.name;
```

### Query 2: Get Agent's Tools with Priority
```sql
SELECT tc.tool_id, tc.name, tc.description, at.priority
FROM tool_configs tc
JOIN agent_tools at ON tc.tool_id = at.tool_id
WHERE at.agent_id = (SELECT agent_id FROM agent_configs WHERE name = 'AgentDebt')
ORDER BY at.priority ASC
LIMIT 5;
```

### Query 3: Get Tenant's Tool Permissions
```sql
SELECT tc.name, ttp.enabled
FROM tool_configs tc
LEFT JOIN tenant_tool_permissions ttp
  ON tc.tool_id = ttp.tool_id
  AND ttp.tenant_id = '550e8400-e29b-41d4-a716-446655440001'
WHERE tc.is_active = TRUE;
```

### Query 4: Get Session History with Messages
```sql
SELECT
  s.session_id,
  s.user_id,
  s.created_at,
  COUNT(m.message_id) as message_count,
  MAX(m.timestamp) as last_message
FROM sessions s
LEFT JOIN messages m ON s.session_id = m.session_id
WHERE s.tenant_id = '550e8400-e29b-41d4-a716-446655440001'
  AND s.user_id = 'user-123'
GROUP BY s.session_id, s.user_id, s.created_at
ORDER BY s.created_at DESC;
```

### Query 5: Get LLM Usage by Tenant
```sql
SELECT
  t.name,
  lm.model_name,
  COUNT(DISTINCT s.session_id) as sessions,
  COUNT(m.message_id) as messages,
  SUM((m.metadata->>'token_count')::int) as total_tokens
FROM tenants t
JOIN sessions s ON t.tenant_id = s.tenant_id
JOIN messages m ON s.session_id = m.session_id
JOIN tenant_llm_configs tlc ON t.tenant_id = tlc.tenant_id
JOIN llm_models lm ON tlc.llm_model_id = lm.llm_model_id
WHERE m.role = 'assistant'
  AND m.timestamp >= NOW() - INTERVAL '30 days'
GROUP BY t.name, lm.model_name;
```

---

## Data Flow Examples

### Example 1: New Tenant Onboarding

```sql
-- Step 1: Create tenant
INSERT INTO tenants (name, domain, status)
VALUES ('NewCorp', 'newcorp.io', 'active')
RETURNING tenant_id;
-- Returns: tenant_id = 'new-tenant-uuid'

-- Step 2: Configure LLM
INSERT INTO tenant_llm_configs (tenant_id, llm_model_id, encrypted_api_key)
VALUES (
  'new-tenant-uuid',
  (SELECT llm_model_id FROM llm_models WHERE model_name = 'gpt-4o-mini'),
  'gAAAAABf...'  -- Encrypted API key
);

-- Step 3: Grant agent permissions
INSERT INTO tenant_agent_permissions (tenant_id, agent_id, enabled)
SELECT
  'new-tenant-uuid',
  agent_id,
  TRUE
FROM agent_configs
WHERE name IN ('AgentDebt', 'AgentShipment');

-- Step 4: Grant tool permissions
INSERT INTO tenant_tool_permissions (tenant_id, tool_id, enabled)
SELECT DISTINCT
  'new-tenant-uuid',
  at.tool_id,
  TRUE
FROM tenant_agent_permissions tap
JOIN agent_tools at ON tap.agent_id = at.agent_id
WHERE tap.tenant_id = 'new-tenant-uuid';
```

### Example 2: Create New Agent

```sql
-- Step 1: Create agent
INSERT INTO agent_configs (name, prompt_template, llm_model_id, description)
VALUES (
  'AgentInventory',
  'You are an inventory management assistant...',
  (SELECT llm_model_id FROM llm_models WHERE model_name = 'gpt-4o-mini'),
  'Handles warehouse inventory queries'
)
RETURNING agent_id;
-- Returns: agent_id = 'new-agent-uuid'

-- Step 2: Assign tools
INSERT INTO agent_tools (agent_id, tool_id, priority)
VALUES
  ('new-agent-uuid', (SELECT tool_id FROM tool_configs WHERE name = 'get_warehouse_stock'), 1),
  ('new-agent-uuid', (SELECT tool_id FROM tool_configs WHERE name = 'check_reorder_levels'), 2);

-- Step 3: Grant to tenant
INSERT INTO tenant_agent_permissions (tenant_id, agent_id, enabled)
VALUES ('new-tenant-uuid', 'new-agent-uuid', TRUE);
```

---

## Performance Optimization

### Critical Indexes

```sql
-- Multi-tenant query optimization
CREATE INDEX idx_sessions_tenant_user ON sessions(tenant_id, user_id, created_at DESC);
CREATE INDEX idx_messages_session_time ON messages(session_id, timestamp ASC);

-- Permission lookups
CREATE INDEX idx_tenant_agent_perms_lookup
  ON tenant_agent_permissions(tenant_id, agent_id)
  WHERE enabled = TRUE;

CREATE INDEX idx_tenant_tool_perms_lookup
  ON tenant_tool_permissions(tenant_id, tool_id)
  WHERE enabled = TRUE;

-- Priority tool filtering
CREATE INDEX idx_agent_tools_priority
  ON agent_tools(agent_id, priority ASC);
```

### Query Performance Tips

1. **Use CTEs for Complex Queries**: Break down into readable steps
2. **Filter Early**: Apply WHERE clauses as early as possible
3. **Limit Results**: Always use LIMIT for list queries
4. **Use EXPLAIN ANALYZE**: Identify slow queries

```sql
-- Example: Optimized agent loading query
EXPLAIN ANALYZE
SELECT ac.*
FROM agent_configs ac
WHERE ac.agent_id IN (
    SELECT agent_id
    FROM tenant_agent_permissions
    WHERE tenant_id = '...' AND enabled = TRUE
)
AND ac.is_active = TRUE;
```

---

## Related Documents

- **[System Architecture](02_SYSTEM_ARCHITECTURE.md)** - How components interact
- **[Tenant Onboarding Guide](03_TENANT_ONBOARDING_GUIDE.md)** - Step-by-step tenant setup
- **[API Reference](05_API_REFERENCE.md)** - REST endpoints using this schema

---

**Document Status**: ✅ Complete
**Maintained By**: Database Team
**Schema Version**: 1.0
