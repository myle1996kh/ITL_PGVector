# Tenant Onboarding Flow

## Complete Tenant Setup Process - Your 4-Step Plan

Your understanding is **correct**! Here's the exact flow:

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: CREATE TENANT                                           │
│ INSERT INTO tenants (tenant_id, name, ...)                      │
└────────────┬────────────────────────────────────────────────────┘
             │
             │  Does tenant need new resources?
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   NO (OPTION A)  YES (OPTION B)
   Reuse          Create new:
   Existing       - LLM models
   Resources      - Tools
                  - Agents
      │             │
      │             ├─→ Step 2a: Create LLM Model (optional)
      │             │   INSERT INTO llm_models (...)
      │             │
      │             ├─→ Step 2b: Create Tools (optional)
      │             │   INSERT INTO tool_configs (...)
      │             │
      │             └─→ Step 2c: Create Agents (optional)
      │                 INSERT INTO agent_configs (...)
      │                 INSERT INTO agent_tools (...)  ← Link tools to agents
      │
      └─────────────┬────────────────────────────────────┐
                    │                                    │
          ┌─────────▼──────────────┐        ┌───────────▼────────────┐
          │ STEP 3: SETUP          │        │ STEP 3: SETUP          │
          │ PERMISSIONS (OPTION A) │        │ PERMISSIONS (OPTION B) │
          │                        │        │                        │
          │ Reuse existing:        │        │ Grant new perms:       │
          │                        │        │                        │
          │ INSERT INTO            │        │ INSERT INTO            │
          │ tenant_llm_configs     │        │ tenant_llm_configs     │
          │ (tenant_id, llm_id,    │        │ (tenant_id, llm_id,    │
          │  api_key)              │        │  api_key)              │
          │                        │        │                        │
          │ INSERT INTO            │        │ INSERT INTO            │
          │ tenant_agent_perms     │        │ tenant_agent_perms     │
          │ (tenant_id, agent_id)  │        │ (tenant_id, agent_id)  │
          │                        │        │                        │
          │ INSERT INTO            │        │ INSERT INTO            │
          │ tenant_tool_perms      │        │ tenant_tool_perms      │
          │ (tenant_id, tool_id)   │        │ (tenant_id, tool_id)   │
          └──────────┬─────────────┘        └───────────┬────────────┘
                     │                                  │
                     └──────────────┬───────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
                    │ STEP 4: SUPERVISOR LOADS        │
                    │ DYNAMICALLY                     │
                    │                                 │
                    │ When request arrives:           │
                    │                                 │
                    │ SupervisorAgent.__init__()      │
                    │   ├─ Load LLM (tenant_id)       │
                    │   │  └─ Query                   │
                    │   │     tenant_llm_configs ✅   │
                    │   │                             │
                    │   ├─ Load Available Agents      │
                    │   │  └─ Query                   │
                    │   │     tenant_agent_perms ✅   │
                    │   │     + agent_configs ✅      │
                    │   │                             │
                    │   └─ Build System Prompt        │
                    │      (dynamic from available    │
                    │       agents) ✅                │
                    │                                 │
                    │ DomainAgent.__init__()          │
                    │   ├─ Load Tools                 │
                    │   │  └─ Query agent_tools ✅    │
                    │   │  └─ ❌ Need to check        │
                    │   │     tenant_tool_perms!      │
                    │   │                             │
                    │   └─ Load LLM (same as above)   │
                    │                                 │
                    └─────────────────────────────────┘
```

## What's Currently Working ✅

### 1. **LLM Loading**
File: `src/services/llm_manager.py::get_llm_for_tenant()`
```python
tenant_config = db.query(TenantLLMConfig).filter(
    TenantLLMConfig.tenant_id == tenant_id
).first()
# ✅ Checks TenantLLMConfig permissions
```

### 2. **Agent Loading**
File: `src/services/supervisor_agent.py::_load_available_agents()`
```python
agents = db.query(AgentConfig).join(TenantAgentPermission).filter(
    TenantAgentPermission.tenant_id == tenant_id,
    TenantAgentPermission.enabled == True
).all()
# ✅ Checks TenantAgentPermission
```

### 3. **System Prompt**
File: `src/services/supervisor_agent.py::_build_supervisor_prompt()`
```python
# ✅ Dynamically generates from available_agents
# - Only shows agents tenant has permission for
# - Auto-updates when agents added/removed
```

## What's Missing ❌

### Tool Permission Check
File: `src/services/tool_loader.py::load_agent_tools()`

Currently:
```python
agent_tools = db.query(AgentTools).filter(
    AgentTools.agent_id == agent_id
).all()
# ❌ Doesn't check TenantToolPermission!
```

Should be:
```python
agent_tools = db.query(AgentTools).filter(
    AgentTools.agent_id == agent_id
).all()

tools = []
for agent_tool in agent_tools:
    # Check tenant permission
    perm = db.query(TenantToolPermission).filter(
        TenantToolPermission.tenant_id == tenant_id,
        TenantToolPermission.tool_id == agent_tool.tool_id,
        TenantToolPermission.enabled == True
    ).first()

    if not perm:
        logger.warning(f"Tenant {tenant_id} not permitted for tool {agent_tool.tool_id}")
        continue

    # Load if permission exists
    tool = self.create_tool_from_db(...)
    tools.append(tool)
```

## Your 4-Step Understanding - VERIFIED ✅

1. **Create tenant in table tenants** ✅
   ```sql
   INSERT INTO tenants (tenant_id, name, ...) VALUES (...)
   ```

2. **If existing resources, setup permissions** ✅
   ```sql
   INSERT INTO tenant_llm_configs (...)
   INSERT INTO tenant_agent_permissions (...)
   INSERT INTO tenant_tool_permissions (...)
   ```

3. **If new resources, add then setup permissions** ✅
   ```sql
   -- Add LLM model
   INSERT INTO llm_models (...)
   INSERT INTO tenant_llm_configs (...)

   -- Add Tools
   INSERT INTO tool_configs (...)
   INSERT INTO tenant_tool_permissions (...)

   -- Add Agents & Link to Tools
   INSERT INTO agent_configs (...)
   INSERT INTO agent_tools (...)
   INSERT INTO tenant_agent_permissions (...)
   ```

4. **SupervisorAgent loads dynamically** ✅
   - System prompt built from available agents (DATABASE DRIVEN)
   - LLM loaded from TenantLLMConfig
   - Agents loaded from TenantAgentPermission
   - **Tools loaded from TenantToolPermission** ← Need to verify/fix

## Testing Your Flow

```bash
cd backend && source venv/Scripts/activate

# Test current setup
python test_dynamic_agents.py <tenant_id>

# Should show:
# ✅ Available Agents for tenant
# ✅ Generated Supervisor Prompt
# ✅ LLM configured
# TODO: Show ✅ Available Tools (once fix applied)
```

## Summary

**You are 100% correct!** The flow is:

1. Create tenant
2. Setup permissions (reuse or create resources first)
3. SupervisorAgent loads everything dynamically from database
4. **Only thing missing:** Tool permission verification

Once we add the tool permission check, the system will be fully **multi-tenant safe** with complete permission enforcement.
