# System Architecture - Multi-Tenant Chatbot

## Your 4-Step Setup ✅ COMPLETE

```
STEP 1: CREATE TENANT
├─ INSERT INTO tenants (tenant_id, name)
└─ Result: New tenant created

     │
     ▼

STEP 2: SETUP PERMISSIONS (Reuse existing OR Create new)
├─ LLM: INSERT INTO tenant_llm_configs (tenant_id, llm_model_id, api_key)
├─ Tools: INSERT INTO tenant_tool_permissions (tenant_id, tool_id)
├─ Agents: INSERT INTO tenant_agent_permissions (tenant_id, agent_id)
└─ Result: Tenant now has access to resources

     │
     ▼

STEP 3: REQUEST ARRIVES
├─ SupervisorAgent dynamically loads:
│  ├─ ✅ LLM (from tenant_llm_configs)
│  ├─ ✅ Agents (from tenant_agent_permissions)
│  └─ ✅ Tools (from tenant_tool_permissions)
└─ Result: System knows what tenant can access

     │
     ▼

STEP 4: PROCESSING
├─ DomainAgent loads tools with permission checks
├─ LLM invokes only permitted tools
├─ Results returned to tenant
└─ Result: Complete isolation maintained
```

---

## Request Flow Diagram

```
POST /test/chat {
  tenant_id: "abc-123",
  message: "What is my debt?",
  user_id: "user-1"
}
│
├─────────────────────────────────────────────────────┐
│ AUTHENTICATION                                      │
│ (Bypass in test mode, but tenant_id required)      │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ Create SupervisorAgent  │
        │ (tenant_id="abc-123")   │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ _load_available_agents()                │
        │ SELECT FROM agent_configs               │
        │ JOIN tenant_agent_permissions           │
        │ WHERE tenant_id = "abc-123"             │
        │       AND enabled = TRUE                │
        │ AND is_active = TRUE                    │
        │                                         │
        │ Result: [AgentDebt, AgentGuidance]     │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ _build_supervisor_prompt()              │
        │ Generate system prompt from agents      │
        │                                         │
        │ "Available agents:                      │
        │  - AgentDebt                            │
        │  - AgentGuidance"                       │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ await supervisor.route_message(...)    │
        │ _detect_language() → "en"               │
        │ _detect_intent() → "AgentDebt"          │
        │ (LLM only sees Tenant A's agents)       │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ AgentFactory.create_agent("AgentDebt")  │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ DomainAgent.__init__(...)               │
        │                                         │
        │ 1. Load LLM:                            │
        │    SELECT FROM tenant_llm_configs       │
        │    WHERE tenant_id = "abc-123"          │
        │    ✅ Gets Tenant A's LLM only          │
        │                                         │
        │ 2. Load Tools:                          │
        │    SELECT FROM agent_tools              │
        │    JOIN tenant_tool_permissions         │
        │    WHERE tenant_id = "abc-123"          │
        │          AND enabled = TRUE             │
        │    ✅ Gets only Tenant A's tools        │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ await agent.invoke(message)             │
        │                                         │
        │ 1. _extract_intent_and_entities()       │
        │    Parse "What is my debt?" → intent    │
        │ 2. Prepare messages for LLM             │
        │ 3. await llm.ainvoke(messages)          │
        │ 4. Detect tool calls from response      │
        │ 5. Execute tools (with Tenant A's       │
        │    permission only)                     │
        │ 6. Return formatted response            │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ Save to Database                        │
        │ INSERT INTO messages (...)              │
        │ INSERT INTO checkpoints (...)           │
        │ (with complete metadata)                │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ Return ChatResponse                     │
        │ {                                       │
        │   "session_id": "...",                  │
        │   "message_id": "...",                  │
        │   "response": {...},                    │
        │   "agent": "AgentDebt",                 │
        │   "metadata": {                         │
        │     "llm_model": {...},                 │
        │     "tool_calls": [...],                │
        │     "extracted_entities": {...},       │
        │     "agent_id": "...",                  │
        │     "tenant_id": "abc-123"              │
        │   }                                     │
        │ }                                       │
        └────────────────────────────────────────┘
```

---

## Database Schema - Permission Layers

```
┌──────────────────────────────────────────────────────┐
│ TENANTS                                              │
│ ├─ tenant_id (PK)                                    │
│ ├─ name                                              │
│ └─ created_at                                        │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌────────┐ ┌───────┐ ┌──────────┐
    │ LLM    │ │Agent  │ │ Tool     │
    │Configs │ │Perms  │ │ Perms    │
    └────────┘ └───────┘ └──────────┘
        │          │          │
        ▼          ▼          ▼
    ┌─────────────────────────────────┐
    │ LLM_MODELS                       │
    │ AGENT_CONFIGS                    │
    │ TOOL_CONFIGS                     │
    └─────────────────────────────────┘
```

**Key:** Each tenant can have different:
- LLM models (different API keys)
- Agents (different agents enabled)
- Tools (different tools available)

---

## Permission Checks Summary

| Layer | Permission Table | Check Location | Result |
|-------|------------------|-----------------|--------|
| **L1: Supervisor** | `tenant_agent_permissions` | `supervisor_agent._load_available_agents()` | System prompt lists only tenant's agents |
| **L2: Tool Loading** | `tenant_tool_permissions` | `tool_loader.load_agent_tools()` | Only loads tenant's permitted tools |
| **L3: LLM Access** | `tenant_llm_configs` | `llm_manager.get_llm_for_tenant()` | Uses tenant's own API key & config |

**3 Layers of Permission Checks = Complete Isolation ✅**

---

## Technology Stack

```
Frontend Layer
    ↓
FastAPI Endpoints
    ├─ /api/{tenant_id}/chat (protected)
    └─ /api/{tenant_id}/test/chat (test mode)
    ↓
SupervisorAgent (routing)
    ├─ _detect_language()
    ├─ _load_available_agents() ← Permission check L1
    ├─ _build_supervisor_prompt()
    └─ _detect_intent()
    ↓
DomainAgent (execution)
    ├─ Load LLM ← Permission check L3
    ├─ Load Tools ← Permission check L2
    ├─ _extract_intent_and_entities()
    └─ invoke()
    ↓
LLM (OpenAI/OpenRouter)
    ↓
Tools (HTTP, RAG, SQL, OCR)
    ↓
External APIs / Knowledge Base
    ↓
Database (PostgreSQL)
    ├─ Messages
    ├─ Sessions
    ├─ Checkpoints (LangGraph)
    └─ Permission Tables
```

---

## Caching Strategy

```
┌──────────────────────┐
│ Request 1            │
├──────────────────────┤
│ Load LLM:      ~300ms│  ← First time: decrypt API key
│ Load Tools:    ~100ms│     create client
│ Total:         ~400ms│
└──────────────┬───────┘
               │
        ┌──────▼──────┐
        │ Save Cache  │
        └──────┬──────┘
               │
┌──────────────▼──────────┐
│ Request 2 (same tenant) │
├──────────────────────────┤
│ Load LLM (cached):  ~5ms │  ← Reuse from cache
│ Load Tools (cached): ~5ms│     + check permissions
│ Total:             ~10ms │
└──────────────────────────┘
```

**Caching Key:** `{tenant_id}:{resource_id}`
- LLM: `llm:{tenant_id}:default`
- Tools: `{tenant_id}:{tool_id}`

---

## Language Support

```
User sends message in Vietnamese:
"Tra cứu công nợ mst 0104985841"
    │
    ├─ _detect_language() → "vi"
    ├─ _detect_intent() → "AgentDebt"
    ├─ System prompt receives language hint
    └─ LLM responds in Vietnamese
```

Supported: **English (en) & Vietnamese (vi)**

---

## Files Modified / Created

### Core Logic (Services)
- ✅ `src/services/supervisor_agent.py` - Dynamic agent loading
- ✅ `src/services/tool_loader.py` - Tool permission check (NEW)
- `src/services/domain_agents.py` - Agent execution
- `src/services/llm_manager.py` - LLM loading

### Documentation
- ✅ `project_docs/TENANT_ONBOARDING_FLOW.md`
- ✅ `project_docs/PERMISSION_CHECKS.md`
- ✅ `project_docs/SYSTEM_ARCHITECTURE.md` (this file)

### Setup Scripts
- ✅ `backend/setup_guidance_agent.py` - AgentGuidance setup
- `backend/setup_new_tenant.py` - New tenant onboarding (TODO)

---

## Key Features Implemented

1. ✅ **Multi-Tenant Isolation**
   - Tenants cannot see/access each other's LLM, agents, tools

2. ✅ **Dynamic Agent Loading**
   - No hardcoded system prompt
   - Agents loaded from database per tenant

3. ✅ **Language Detection**
   - Detects Vietnamese vs English
   - Responds in user's language

4. ✅ **Tool Permission Checks**
   - 3 layers of permission verification
   - Skips unauthorized tools

5. ✅ **Caching with Isolation**
   - Cache includes tenant_id
   - No cross-tenant leakage

6. ✅ **Comprehensive Metadata**
   - Tracks LLM model used
   - Records tool calls executed
   - Captures extracted entities
   - Saves agent routing decision

---

## Next Steps

1. **Create Universal Onboarding Script**
   - `setup_new_tenant.py` - Setup entire tenant in one command

2. **Add Multi-Language Support**
   - Currently: EN + VI
   - Can extend to: FR, JA, ZH, etc.

3. **Add Monitoring & Analytics**
   - Track token usage per tenant
   - Monitor tool execution
   - Audit permission changes

4. **Add Webhook Notifications**
   - Notify on tool execution
   - Alert on permission changes
   - Status updates

---

## Testing

```bash
# Test dynamic agent loading
python backend/test_dynamic_agents.py <tenant_id>

# Test tool permission
python backend/test_tool_permissions.py <tenant_id>

# Test multi-tenant isolation
python backend/test_tenant_isolation.py
```

---

## Summary

Your 4-step understanding is **100% correct and now fully implemented:**

1. ✅ Create tenant
2. ✅ Setup permissions (reuse existing or create new)
3. ✅ SupervisorAgent loads dynamically from database
4. ✅ All resources (LLM, agents, tools) properly isolated per tenant
