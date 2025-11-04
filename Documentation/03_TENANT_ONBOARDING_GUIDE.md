# Tenant Onboarding Guide

**Document Version**: 1.0
**Last Updated**: 2025-11-03
**Audience**: System Administrators, DevOps Engineers

---

## Table of Contents

1. [Overview](#overview)
2. [4-Step Onboarding Process](#4-step-onboarding-process)
3. [Option A: Reuse Existing Resources](#option-a-reuse-existing-resources)
4. [Option B: Create New Resources](#option-b-create-new-resources)
5. [Testing Tenant Setup](#testing-tenant-setup)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide explains how to onboard a new tenant (organization) to the AgentHub Multi-Agent Chatbot Framework. The process is **100% database-driven** and requires **no code changes or system restart**.

### Onboarding Time
- **Option A** (Reuse existing resources): ~10 minutes
- **Option B** (Create new resources): ~20-30 minutes

### Prerequisites
- Access to PostgreSQL database
- Admin API credentials (for REST approach)
- Tenant LLM API key (OpenAI, Gemini, Claude, or OpenRouter)
- List of agents and tools needed for tenant

---

## 4-Step Onboarding Process

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: CREATE TENANT                                       │
│ └─ INSERT INTO tenants (tenant_id, name, domain, status)   │
└───────────────────────┬─────────────────────────────────────┘
                        │
      ┌─────────────────┴─────────────────┐
      │                                   │
      ▼                                   ▼
┌────────────────┐              ┌────────────────────┐
│   OPTION A     │              │    OPTION B        │
│ Reuse Existing │              │  Create New        │
│   Resources    │              │   Resources        │
└────────┬───────┘              └────────┬───────────┘
         │                               │
         │                               ├─ Create LLM models (if needed)
         │                               ├─ Create tools (if needed)
         │                               └─ Create agents (if needed)
         │                               │
         └───────────────┬───────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ STEP 2: SETUP PERMISSIONS                                    │
│ ├─ INSERT INTO tenant_llm_configs (tenant_id, api_key)      │
│ ├─ INSERT INTO tenant_agent_permissions (tenant_id, agent)  │
│ └─ INSERT INTO tenant_tool_permissions (tenant_id, tool)    │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ STEP 3: VERIFY SETUP                                         │
│ └─ Test chat query with tenant credentials                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                     ✅ Done!
```

---

## Option A: Reuse Existing Resources

Use this option when the new tenant needs the same agents and tools as existing tenants.

### Step 1: Create Tenant

**Via SQL**:
```sql
INSERT INTO tenants (tenant_id, name, domain, status, created_at)
VALUES (
  gen_random_uuid(),
  'Acme Corporation',
  'acme.com',
  'active',
  NOW()
);
```

**Via Admin API**:
```bash
POST /api/admin/tenants
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "name": "Acme Corporation",
  "domain": "acme.com",
  "status": "active"
}

# Response:
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corporation",
  ...
}
```

### Step 2: Configure LLM Access

**Get Available LLM Models**:
```bash
GET /api/admin/llm-models
Authorization: Bearer <admin_jwt>

# Response:
[
  {
    "llm_model_id": "uuid-gpt4o-mini",
    "provider": "openai",
    "model_name": "gpt-4o-mini",
    "context_window": 128000
  },
  {
    "llm_model_id": "uuid-gemini-pro",
    "provider": "gemini",
    "model_name": "gemini-1.5-pro",
    "context_window": 1048576
  }
]
```

**Configure Tenant LLM**:
```bash
POST /api/admin/tenants/{tenant_id}/llm-config
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "llm_model_id": "uuid-gpt4o-mini",
  "api_key": "sk-abc123...",  # Will be encrypted
  "rate_limit_rpm": 60,
  "rate_limit_tpm": 10000
}
```

**Via SQL**:
```sql
-- First, encrypt the API key
-- (Use Python script: python -c "from utils.encryption import encrypt_api_key; print(encrypt_api_key('sk-abc123...'))")

INSERT INTO tenant_llm_configs (
  config_id, tenant_id, llm_model_id, encrypted_api_key, rate_limit_rpm
)
VALUES (
  gen_random_uuid(),
  '550e8400-e29b-41d4-a716-446655440000',  -- tenant_id from step 1
  (SELECT llm_model_id FROM llm_models WHERE model_name = 'gpt-4o-mini'),
  'gAAAAABf...',  -- Encrypted API key
  60
);
```

### Step 3: Grant Agent Permissions

**List Available Agents**:
```bash
GET /api/admin/agents
Authorization: Bearer <admin_jwt>

# Response:
[
  {"agent_id": "uuid-agent-debt", "name": "AgentDebt", ...},
  {"agent_id": "uuid-agent-shipment", "name": "AgentShipment", ...},
  {"agent_id": "uuid-agent-analysis", "name": "AgentAnalysis", ...}
]
```

**Grant Permissions**:
```bash
POST /api/admin/tenants/{tenant_id}/permissions/agents
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "agent_permissions": [
    {"agent_id": "uuid-agent-debt", "enabled": true},
    {"agent_id": "uuid-agent-shipment", "enabled": true}
  ]
}
```

**Via SQL**:
```sql
INSERT INTO tenant_agent_permissions (tenant_id, agent_id, enabled)
VALUES
  ('550e8400-e29b-41d4-a716-446655440000', (SELECT agent_id FROM agent_configs WHERE name = 'AgentDebt'), TRUE),
  ('550e8400-e29b-41d4-a716-446655440000', (SELECT agent_id FROM agent_configs WHERE name = 'AgentShipment'), TRUE);
```

### Step 4: Grant Tool Permissions

**List Tools Used by Agents**:
```bash
GET /api/admin/agents/{agent_id}/tools
Authorization: Bearer <admin_jwt>

# Response:
[
  {"tool_id": "uuid-tool-debt", "name": "get_customer_debt", ...},
  {"tool_id": "uuid-tool-payment", "name": "get_payment_history", ...}
]
```

**Grant Permissions**:
```bash
POST /api/admin/tenants/{tenant_id}/permissions/tools
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "tool_permissions": [
    {"tool_id": "uuid-tool-debt", "enabled": true},
    {"tool_id": "uuid-tool-payment", "enabled": true}
  ]
}
```

**Via SQL**:
```sql
-- Grant permissions for all tools used by permitted agents
INSERT INTO tenant_tool_permissions (tenant_id, tool_id, enabled)
SELECT DISTINCT
  '550e8400-e29b-41d4-a716-446655440000' AS tenant_id,
  at.tool_id,
  TRUE AS enabled
FROM tenant_agent_permissions tap
JOIN agent_tools at ON tap.agent_id = at.agent_id
WHERE tap.tenant_id = '550e8400-e29b-41d4-a716-446655440000'
  AND tap.enabled = TRUE;
```

### Step 5: Verify Setup

```bash
# Test chat endpoint
POST /api/550e8400-e29b-41d4-a716-446655440000/test/chat
Content-Type: application/json

{
  "message": "What is the debt for customer MST 0123456789?",
  "user_id": "test-user"
}

# Expected response:
{
  "session_id": "...",
  "message_id": "...",
  "response": "Customer MST 0123456789 has total debt of $15,432.50...",
  "agent": "AgentDebt",
  "metadata": {
    "llm_model": "gpt-4o-mini",
    "tool_calls": ["get_customer_debt"],
    "extracted_entities": {"mst": "0123456789"}
  }
}
```

---

## Option B: Create New Resources

Use this option when the tenant needs custom agents or tools.

### Step 1-2: Same as Option A
Follow Step 1 (Create Tenant) and Step 2 (Configure LLM) from Option A.

### Step 3: Create Custom Tools

**Example: Create Inventory Tool**:
```bash
POST /api/admin/tools
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "name": "get_warehouse_inventory",
  "base_tool_id": "uuid-http-get",  # HTTP_GET base tool
  "config": {
    "endpoint": "https://erp.acme.com/api/inventory/{sku}",
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
        "description": "Product SKU code",
        "pattern": "^SKU-[0-9]{5}$"
      }
    },
    "required": ["sku"]
  },
  "output_format_id": "uuid-format-json",
  "description": "Get current warehouse inventory for product SKU"
}

# Response:
{
  "tool_id": "uuid-new-tool-inventory",
  ...
}
```

**Via SQL**:
```sql
INSERT INTO tool_configs (
  tool_id, name, base_tool_id, config, input_schema,
  output_format_id, description, is_active
)
VALUES (
  gen_random_uuid(),
  'get_warehouse_inventory',
  (SELECT base_tool_id FROM base_tools WHERE type = 'HTTP_GET'),
  '{
    "endpoint": "https://erp.acme.com/api/inventory/{sku}",
    "method": "GET",
    "headers": {"X-API-Version": "v2"},
    "timeout": 30
  }'::jsonb,
  '{
    "type": "object",
    "properties": {
      "sku": {"type": "string", "pattern": "^SKU-[0-9]{5}$"}
    },
    "required": ["sku"]
  }'::jsonb,
  (SELECT format_id FROM output_formats WHERE name = 'structured_json'),
  'Get warehouse inventory for product SKU',
  TRUE
);
```

### Step 4: Create Custom Agent

**Example: Create InventoryAgent**:
```bash
POST /api/admin/agents
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "name": "AgentInventory",
  "prompt_template": "You are AgentInventory, a specialized assistant for warehouse inventory queries.\n\nYour capabilities:\n- Check stock levels by SKU\n- Identify low inventory items\n- Provide reorder recommendations\n\nAlways:\n- Extract SKU from user query\n- Validate SKU format (SKU-XXXXX)\n- Use get_warehouse_inventory tool\n- Return structured inventory data",
  "llm_model_id": "uuid-gpt4o-mini",
  "default_output_format_id": "uuid-format-json",
  "description": "Handles warehouse inventory queries"
}

# Response:
{
  "agent_id": "uuid-new-agent-inventory",
  ...
}
```

### Step 5: Assign Tools to Agent

```bash
POST /api/admin/agents/{agent_id}/tools
Content-Type: application/json
Authorization: Bearer <admin_jwt>

{
  "tools": [
    {"tool_id": "uuid-new-tool-inventory", "priority": 1}
  ]
}
```

**Via SQL**:
```sql
INSERT INTO agent_tools (agent_id, tool_id, priority)
VALUES (
  'uuid-new-agent-inventory',
  'uuid-new-tool-inventory',
  1
);
```

### Step 6: Grant Permissions (Same as Option A Step 3-4)

```sql
-- Grant agent permission
INSERT INTO tenant_agent_permissions (tenant_id, agent_id, enabled)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'uuid-new-agent-inventory', TRUE);

-- Grant tool permission
INSERT INTO tenant_tool_permissions (tenant_id, tool_id, enabled)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'uuid-new-tool-inventory', TRUE);
```

---

## Testing Tenant Setup

### Test Checklist

```bash
# 1. Verify tenant exists
SELECT * FROM tenants WHERE domain = 'acme.com';

# 2. Verify LLM config
SELECT t.name, tlc.encrypted_api_key, lm.model_name
FROM tenants t
JOIN tenant_llm_configs tlc ON t.tenant_id = tlc.tenant_id
JOIN llm_models lm ON tlc.llm_model_id = lm.llm_model_id
WHERE t.domain = 'acme.com';

# 3. Verify agent permissions
SELECT t.name, ac.name AS agent_name, tap.enabled
FROM tenants t
JOIN tenant_agent_permissions tap ON t.tenant_id = tap.tenant_id
JOIN agent_configs ac ON tap.agent_id = ac.agent_id
WHERE t.domain = 'acme.com';

# 4. Verify tool permissions
SELECT t.name, tc.name AS tool_name, ttp.enabled
FROM tenants t
JOIN tenant_tool_permissions ttp ON t.tenant_id = ttp.tenant_id
JOIN tool_configs tc ON ttp.tool_id = tc.tool_id
WHERE t.domain = 'acme.com';
```

### Integration Test

**Test Script** (`test_tenant_setup.py`):
```python
import requests

TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
BASE_URL = "http://localhost:8000"

# Test 1: Health check
response = requests.get(f"{BASE_URL}/health")
assert response.status_code == 200, "API not healthy"

# Test 2: Chat with AgentDebt
response = requests.post(
    f"{BASE_URL}/api/{TENANT_ID}/test/chat",
    json={
        "message": "What is debt for MST 0123456789?",
        "user_id": "test-user"
    }
)
assert response.status_code == 200, f"Chat failed: {response.text}"
data = response.json()
assert data["agent"] == "AgentDebt", "Wrong agent selected"
assert "tool_calls" in data["metadata"], "Tools not executed"

print("✅ All tests passed!")
```

Run test:
```bash
python test_tenant_setup.py
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Tenant not found" Error
**Symptom**: 404 error when calling `/api/{tenant_id}/chat`

**Solution**:
```sql
-- Verify tenant exists and is active
SELECT tenant_id, name, status FROM tenants WHERE tenant_id = '...';

-- If status is not 'active', update it
UPDATE tenants SET status = 'active' WHERE tenant_id = '...';
```

#### Issue 2: "No LLM configured for tenant"
**Symptom**: 500 error with message about missing LLM config

**Solution**:
```sql
-- Check if tenant_llm_configs entry exists
SELECT * FROM tenant_llm_configs WHERE tenant_id = '...';

-- If missing, create one (see Step 2 above)
```

#### Issue 3: "No agents available"
**Symptom**: SupervisorAgent cannot route (no agents permitted)

**Solution**:
```sql
-- Check tenant_agent_permissions
SELECT tap.*, ac.name
FROM tenant_agent_permissions tap
JOIN agent_configs ac ON tap.agent_id = ac.agent_id
WHERE tap.tenant_id = '...' AND tap.enabled = TRUE;

-- If empty, grant permissions (see Step 3 above)
```

#### Issue 4: "Tool execution failed: Unauthorized"
**Symptom**: Tool calls return 403/401 errors

**Causes**:
- User JWT not being injected correctly
- External API credentials invalid
- Tool not permitted for tenant

**Solution**:
```sql
-- Verify tool permission
SELECT * FROM tenant_tool_permissions
WHERE tenant_id = '...' AND tool_id = '...' AND enabled = TRUE;

-- Check tool config
SELECT config FROM tool_configs WHERE tool_id = '...';
-- Ensure endpoint and headers are correct
```

#### Issue 5: "Intent detection fails"
**Symptom**: SupervisorAgent returns "UNCLEAR" for valid queries

**Solution**:
- Check agent descriptions are clear and distinct
- Verify LLM model is appropriate (use GPT-4o-mini minimum)
- Test with more explicit queries
- Review SupervisorAgent logs for LLM response

```bash
# Check logs
docker-compose logs backend | grep "SupervisorAgent"
```

---

## Cache Management

### Clear Tenant Cache

After modifying tenant configuration, clear the cache:

```bash
# Via API
POST /api/admin/agents/reload
Authorization: Bearer <admin_jwt>

# Via Redis CLI
redis-cli DEL agenthub:{tenant_id}:*
```

### Cache Keys to Clear

| Change | Redis Key Pattern |
|--------|------------------|
| **Agent config updated** | `agenthub:{tenant_id}:cache:agent:{agent_id}` |
| **Tool config updated** | `agenthub:{tenant_id}:cache:tool:{tool_id}` |
| **LLM config updated** | `agenthub:{tenant_id}:llm` |
| **Permissions updated** | `agenthub:{tenant_id}:cache:permissions:*` |
| **All tenant data** | `agenthub:{tenant_id}:*` |

---

## Next Steps

After successful onboarding:

1. **Provide Tenant Credentials**:
   - tenant_id
   - API endpoint: `https://agenthub.example.com/api/{tenant_id}/chat`
   - JWT issuer details (for authentication)

2. **Train Users**:
   - Share chat widget integration docs
   - Provide example queries for each agent
   - Explain conversation history access

3. **Monitor Usage**:
   - Track token usage and costs
   - Monitor agent/tool performance
   - Review error logs

4. **Optimize**:
   - Adjust rate limits based on usage
   - Add more agents/tools as needed
   - Refine agent prompts based on feedback

---

## Related Documents

- **[System Architecture](02_SYSTEM_ARCHITECTURE.md)** - Understanding multi-tenancy
- **[Security Guide](08_SECURITY_GUIDE.md)** - JWT and API key management
- **[API Reference](05_API_REFERENCE.md)** - Complete API documentation
- **[Operations Guide](11_OPERATIONS_GUIDE.md)** - Monitoring and maintenance

---

**Document Status**: ✅ Complete
**Last Reviewed**: 2025-11-03
**Maintained By**: Platform Operations Team
