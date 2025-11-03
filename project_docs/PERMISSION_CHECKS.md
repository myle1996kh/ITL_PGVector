# Permission Checks - Complete Tenant Isolation

## Your 4-Step Flow - All Permission Checks ✅

### Step 1: Create Tenant
```sql
INSERT INTO tenants (tenant_id, name, ...) VALUES (...)
```

---

### Step 2: Setup Permissions

#### 2a. LLM Permission
```sql
INSERT INTO tenant_llm_configs (
  tenant_id,
  llm_model_id,
  encrypted_api_key,
  rate_limit_rpm,
  rate_limit_tpm
) VALUES (...)
```
**Permission Check:** ✅ `src/services/llm_manager.py`
```python
tenant_config = db.query(TenantLLMConfig).filter(
    TenantLLMConfig.tenant_id == tenant_id
).first()
# Only loads LLM if tenant_id matches in TenantLLMConfig
```

---

#### 2b. Tool Permission
```sql
INSERT INTO tenant_tool_permissions (
  tenant_id,
  tool_id,
  enabled
) VALUES (...)
```
**Permission Check:** ✅ `src/services/tool_loader.py::load_agent_tools()`
```python
tool_permission = db.query(TenantToolPermission).filter(
    TenantToolPermission.tenant_id == tenant_id,
    TenantToolPermission.tool_id == tool_id,
    TenantToolPermission.enabled == True
).first()

if not tool_permission:
    logger.warning("tool_access_denied", ...)
    continue  # Skip this tool
```

---

#### 2c. Agent Permission
```sql
INSERT INTO tenant_agent_permissions (
  tenant_id,
  agent_id,
  enabled
) VALUES (...)
```
**Permission Check:** ✅ `src/services/supervisor_agent.py::_load_available_agents()`
```python
agents = db.query(AgentConfig).join(TenantAgentPermission).filter(
    TenantAgentPermission.tenant_id == tenant_id,
    TenantAgentPermission.enabled == True,
    AgentConfig.is_active == True
).all()
# Only loads agents tenant has permission for
```

---

### Step 3: Dynamic Loading by SupervisorAgent

```
┌─────────────────────────────────────────────────────┐
│ SupervisorAgent.__init__()                          │
│                                                     │
│ ✅ Check 1: Load LLM                               │
│    Query: TenantLLMConfig                          │
│    Filter: tenant_id = request.tenant_id           │
│    Result: Only 1 LLM per tenant                   │
│                                                     │
│ ✅ Check 2: Load Available Agents                  │
│    Query: AgentConfig JOIN                         │
│           TenantAgentPermission                    │
│    Filter: tenant_id + enabled=True                │
│    Result: Only agents tenant permitted to use     │
│                                                     │
│ ✅ Check 3: Build System Prompt                    │
│    From available agents (only tenant's agents)    │
│                                                     │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ DomainAgent.__init__()                              │
│                                                     │
│ ✅ Check 4: Load Tools                             │
│    Query: AgentTools + TenantToolPermission        │
│    Filter: tenant_id + enabled=True                │
│    Result: Only tools tenant permitted to use      │
│                                                     │
│ ✅ Check 5: Load LLM (again)                       │
│    Same as Check 1 - cached                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Isolation Verification

### Scenario: Tenant A tries to access Tenant B's resources

**Attempt 1: Direct LLM Access**
```python
# Tenant A makes request
db.query(TenantLLMConfig).filter(
    TenantLLMConfig.tenant_id == "tenant-a-id"
).first()
# Result: Gets only Tenant A's LLM config
# ✅ Tenant B's LLM is never loaded
```

**Attempt 2: Direct Agent Access**
```python
# Supervisor loads agents
db.query(AgentConfig).join(TenantAgentPermission).filter(
    TenantAgentPermission.tenant_id == "tenant-a-id"
).all()
# Result: Gets only Tenant A's agents
# ✅ Tenant B's agents are never shown in system prompt
```

**Attempt 3: Direct Tool Access**
```python
# Tool loader checks permission
db.query(TenantToolPermission).filter(
    TenantToolPermission.tenant_id == "tenant-a-id",
    TenantToolPermission.tool_id == "tenant-b-tool-id"
).first()
# Result: None (permission not found)
# ✅ Tool is skipped, not loaded
```

---

## Complete Permission Matrix

| Resource | Permission Table | Check Location | Status |
|----------|------------------|-----------------|--------|
| **LLM Model** | `tenant_llm_configs` | `llm_manager.get_llm_for_tenant()` | ✅ |
| **Agent** | `tenant_agent_permissions` | `supervisor_agent._load_available_agents()` | ✅ |
| **Tool** | `tenant_tool_permissions` | `tool_loader.load_agent_tools()` | ✅ |

---

## Testing Multi-Tenant Isolation

### Setup 2 Tenants
```bash
# Tenant A
python setup_guidance_agent.py --tenant-id "tenant-a"
# Gets: AgentDebt, AgentGuidance, RAG Tool

# Tenant B
python setup_guidance_agent.py --tenant-id "tenant-b" --agents "AgentAnalysis"
# Gets: AgentAnalysis only (no RAG Tool)
```

### Verify Isolation
```python
# Test Tenant A
supervisor_a = SupervisorAgent(db, "tenant-a-id", jwt_token)
print(supervisor_a.available_agents)  # Shows: AgentDebt, AgentGuidance
# System prompt includes AgentDebt, AgentGuidance

# Test Tenant B
supervisor_b = SupervisorAgent(db, "tenant-b-id", jwt_token)
print(supervisor_b.available_agents)  # Shows: AgentAnalysis only
# System prompt includes AgentAnalysis ONLY

# ✅ Tenants cannot see each other's agents!
```

---

## Data Flow With Permissions

```
HTTP Request: POST /test/chat
  tenant_id: "tenant-a-id"
  message: "..."
    │
    ├─ SupervisorAgent(db, "tenant-a-id")
    │   │
    │   ├─ _load_available_agents()
    │   │   Query: WHERE tenant_id = "tenant-a-id"
    │   │   Result: [AgentDebt, AgentGuidance]
    │   │
    │   └─ _build_supervisor_prompt()
    │       System prompt lists only:
    │       - AgentDebt
    │       - AgentGuidance
    │
    ├─ await supervisor.route_message(message)
    │   └─ _detect_intent(message)
    │       LLM sees only Tenant A's agents
    │       → Responds with agent name
    │
    └─ AgentFactory.create_agent("AgentDebt")
        └─ DomainAgent.__init__()
            │
            ├─ Load LLM
            │   Query: WHERE tenant_id = "tenant-a-id"
            │   ✅ Gets Tenant A's LLM only
            │
            └─ Load Tools
                Query: agent_tools + WHERE tenant_id = "tenant-a-id"
                ✅ Loads only Tenant A's permitted tools
```

---

## Summary: Complete Isolation ✅

1. **LLM Isolation** ✅ - Each tenant has their own encrypted API key
2. **Agent Isolation** ✅ - SupervisorAgent only shows permitted agents
3. **Tool Isolation** ✅ - Tools only loaded if tenant has permission
4. **System Prompt** ✅ - Built from tenant's agents only
5. **Caching** ✅ - Cache key includes tenant_id
6. **Tenant ID** ✅ - Always passed through request context

**Result:** Tenants cannot see, access, or use each other's resources!
