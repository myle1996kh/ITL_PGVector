# System Architecture - AgentHub Multi-Agent Chatbot Framework

**Document Version**: 1.0
**Last Updated**: 2025-11-03
**Architecture Type**: Multi-Tier, Multi-Tenant SaaS

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Diagram](#component-diagram)
3. [Request Flow](#request-flow)
4. [Multi-Tenant Isolation](#multi-tenant-isolation)
5. [Agent System Architecture](#agent-system-architecture)
6. [Tool Loading System](#tool-loading-system)
7. [LLM Management](#llm-management)
8. [Caching Strategy](#caching-strategy)
9. [Database Design](#database-design)
10. [Security Architecture](#security-architecture)
11. [Technology Stack Details](#technology-stack-details)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │  Chat Widget  │  │  Admin Panel  │  │  Monitoring   │       │
│  │  (React/Vue)  │  │  (Admin UI)   │  │  Dashboard    │       │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘       │
└──────────┼──────────────────┼──────────────────┼────────────────┘
           │ HTTPS + JWT      │ HTTPS + JWT      │ HTTPS
           │                  │                  │
┌──────────▼──────────────────▼──────────────────▼────────────────┐
│                     API Gateway / Load Balancer                  │
│                      (NGINX / AWS ALB)                           │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                   FastAPI Application Layer                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Middleware Pipeline                                        ││
│  │  ├─ CORS Handler                                            ││
│  │  ├─ JWT Authentication (RS256 validation)                   ││
│  │  ├─ Tenant Extraction (from JWT payload)                    ││
│  │  ├─ Request Logging (structlog)                             ││
│  │  └─ Error Handler                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐   │
│  │  Chat API     │  │  Admin API    │  │  Session API     │   │
│  │  /chat        │  │  /admin/*     │  │  /sessions       │   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬──────────┘   │
└──────────┼──────────────────┼──────────────────┼────────────────┘
           │                  │                  │
┌──────────▼──────────────────▼──────────────────▼────────────────┐
│                      Service Layer                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ SupervisorAgent │  │ LLMManager   │  │ ToolLoader        │  │
│  │ (Intent Router) │  │ (Multi-LLM)  │  │ (Dynamic Tools)   │  │
│  └────────┬────────┘  └──────┬───────┘  └────────┬──────────┘  │
│           │                  │                   │              │
│  ┌────────▼──────────────────▼───────────────────▼──────────┐  │
│  │  Domain Agents: AgentDebt, AgentShipment, AgentAnalysis  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ RAG Service     │  │ Checkpoint   │  │ Output Formatter  │  │
│  │ (ChromaDB)      │  │ Service      │  │ (JSON/Table/etc)  │  │
│  └─────────────────┘  └──────────────┘  └───────────────────┘  │
└──────────┬───────────────────┬─────────────────┬────────────────┘
           │                   │                 │
┌──────────▼───────────────────▼─────────────────▼────────────────┐
│                      Data Layer                                  │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │  PostgreSQL   │  │    Redis     │  │    ChromaDB       │    │
│  │  (Main DB)    │  │  (Cache)     │  │  (Vectors)        │    │
│  │               │  │              │  │                   │    │
│  │  13 Tables:   │  │  Cache Keys: │  │  Collections:     │    │
│  │  - tenants    │  │  - agents    │  │  - knowledge_base │    │
│  │  - agents     │  │  - tools     │  │  - documents      │    │
│  │  - tools      │  │  - llm       │  │                   │    │
│  │  - sessions   │  │  - perms     │  │                   │    │
│  │  - messages   │  │              │  │                   │    │
│  │  - ...        │  │              │  │                   │    │
│  └───────────────┘  └──────────────┘  └───────────────────┘    │
└─────────┬──────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────────┐
│              External Systems                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐      │
│  │  LLM APIs    │  │  Business    │  │  Auth Provider    │      │
│  │  - OpenAI    │  │  APIs        │  │  (JWT Issuer)     │      │
│  │  - Gemini    │  │  - ERP       │  │                   │      │
│  │  - Claude    │  │  - CRM       │  │                   │      │
│  │  - OpenRouter│  │  - Logistics │  │                   │      │
│  └──────────────┘  └──────────────┘  └───────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Application (main.py)                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Routers (API Endpoints)                                ││
│  │  ├─ /api/{tenant_id}/chat → chat.py                     ││
│  │  ├─ /api/{tenant_id}/sessions → sessions.py             ││
│  │  ├─ /api/admin/agents → admin/agents.py                 ││
│  │  ├─ /api/admin/tools → admin/tools.py                   ││
│  │  ├─ /api/admin/tenants → admin/tenants.py               ││
│  │  └─ /api/admin/knowledge → admin/knowledge.py           ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Services (Business Logic)                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  supervisor_agent.py                                    ││
│  │  ├─ _detect_language() → "en" | "vi"                    ││
│  │  ├─ _load_available_agents() → [AgentDebt, ...]        ││
│  │  ├─ _build_supervisor_prompt() → Dynamic prompt         ││
│  │  ├─ _detect_intent() → "AgentDebt" | "UNCLEAR"         ││
│  │  └─ route_message() → Route to domain agent            ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  domain_agents.py                                       ││
│  │  ├─ DomainAgent (base class)                            ││
│  │  │  ├─ _extract_intent_and_entities()                   ││
│  │  │  ├─ invoke() → Execute with tools                    ││
│  │  │  └─ _format_response()                               ││
│  │  ├─ AgentDebt (customer debt queries)                   ││
│  │  ├─ AgentShipment (shipment tracking)                   ││
│  │  ├─ AgentAnalysis (RAG knowledge base)                  ││
│  │  └─ AgentOCR (document processing)                      ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  tool_loader.py                                         ││
│  │  ├─ load_agent_tools() → [StructuredTool, ...]         ││
│  │  ├─ create_tool_from_db() → Tool instance              ││
│  │  ├─ _check_tenant_permission() → bool                   ││
│  │  └─ _inject_jwt_context() → Tool with auth             ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  llm_manager.py                                         ││
│  │  ├─ get_llm_for_tenant() → ChatOpenAI | ChatGemini     ││
│  │  ├─ _load_llm_config() → TenantLLMConfig               ││
│  │  ├─ _decrypt_api_key() → Decrypted key                 ││
│  │  └─ _cache_llm_client() → Cache in Redis               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Tools (Execution Layer)                                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  tools/http.py                                          ││
│  │  ├─ HTTPGetTool                                         ││
│  │  │  └─ execute() → GET request with JWT                ││
│  │  └─ HTTPPostTool                                        ││
│  │     └─ execute() → POST request with JWT               ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  tools/rag.py                                           ││
│  │  └─ RAGTool                                             ││
│  │     └─ execute() → ChromaDB search + synthesis         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Request Flow

### End-to-End Chat Request Flow

```
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: User Sends Message                                  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                POST /api/{tenant_id}/chat
                {
                  "message": "What is debt for MST 0123456789?",
                  "user_id": "user-123",
                  "session_id": "session-abc" (optional)
                }
                Headers: Authorization: Bearer <JWT>
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 2: Authentication Middleware                           │
│  ├─ Extract JWT from Authorization header                    │
│  ├─ Validate RS256 signature with public key                 │
│  ├─ Decode payload: {tenant_id, user_id, exp, ...}          │
│  ├─ Verify tenant_id matches URL parameter                   │
│  ├─ Check token expiration                                   │
│  └─ Result: ✅ Request authenticated, tenant_id extracted    │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 3: Chat Endpoint Handler (api/chat.py)                 │
│  ├─ Validate request schema (Pydantic)                       │
│  ├─ Check if session_id provided, else create new session    │
│  ├─ Save user message to database:                           │
│  │  INSERT INTO messages (session_id, role='user', ...)     │
│  └─ Result: session_id, user message saved                   │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 4: SupervisorAgent Initialization                      │
│  ├─ Load LLM for tenant:                                     │
│  │  └─ LLMManager.get_llm_for_tenant(tenant_id)             │
│  │     ├─ Check Redis: agenthub:{tenant_id}:llm             │
│  │     ├─ If miss: Query tenant_llm_configs table           │
│  │     ├─ Decrypt API key (Fernet)                          │
│  │     ├─ Create ChatOpenAI/ChatGemini client               │
│  │     └─ Cache in Redis (1h TTL)                           │
│  ├─ Load available agents:                                   │
│  │  └─ _load_available_agents(tenant_id)                    │
│  │     ├─ Query: SELECT agent_configs                        │
│  │     │         JOIN tenant_agent_permissions               │
│  │     │         WHERE tenant_id = ? AND enabled = TRUE      │
│  │     └─ Result: [AgentDebt, AgentShipment, AgentGuidance] │
│  ├─ Build dynamic supervisor prompt:                         │
│  │  └─ _build_supervisor_prompt(available_agents)           │
│  │     └─ "You can route to: AgentDebt, AgentShipment, ..." │
│  └─ Result: SupervisorAgent ready with tenant context        │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 5: Intent Detection & Routing                          │
│  ├─ Detect language:                                         │
│  │  └─ _detect_language("What is debt...") → "en"           │
│  ├─ Detect intent:                                           │
│  │  └─ _detect_intent(message, available_agents)            │
│  │     ├─ Send to LLM: "Classify intent: [AgentDebt, ...]"  │
│  │     ├─ LLM response: {"agent": "AgentDebt"}              │
│  │     └─ Result: Route to "AgentDebt"                       │
│  └─ Result: target_agent = "AgentDebt", language = "en"      │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 6: Domain Agent Initialization (AgentDebt)             │
│  ├─ Load agent config from database:                         │
│  │  └─ SELECT * FROM agent_configs WHERE name='AgentDebt'   │
│  ├─ Load LLM (same as supervisor):                           │
│  │  └─ LLMManager.get_llm_for_tenant(tenant_id)             │
│  ├─ Load tools for agent:                                    │
│  │  └─ ToolLoader.load_agent_tools(agent_id, tenant_id)     │
│  │     ├─ Query: SELECT tool_configs                         │
│  │     │         FROM agent_tools                            │
│  │     │         WHERE agent_id = ? ORDER BY priority ASC    │
│  │     │         LIMIT 5                                     │
│  │     ├─ Check tenant_tool_permissions for each tool        │
│  │     ├─ Create StructuredTool instances                    │
│  │     │  └─ HTTPGetTool("get_customer_debt")               │
│  │     │     ├─ endpoint: "https://erp.com/api/debt/{mst}"  │
│  │     │     ├─ input_schema: {mst: string}                 │
│  │     │     └─ inject_jwt: True                            │
│  │     └─ Result: [get_customer_debt, ...]                  │
│  └─ Result: AgentDebt with tools ready                       │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 7: Entity Extraction & Agent Invocation                │
│  ├─ Extract entities from message:                           │
│  │  └─ _extract_intent_and_entities(message)                │
│  │     ├─ Analyze tool input_schema: {mst: string}          │
│  │     ├─ Send to LLM: "Extract MST from message"           │
│  │     └─ Result: {"mst": "0123456789"}                     │
│  ├─ Prepare agent invocation:                                │
│  │  └─ messages = [                                          │
│  │       SystemMessage(agent.prompt_template),               │
│  │       HumanMessage("What is debt for MST 0123456789?")    │
│  │     ]                                                     │
│  ├─ Bind tools to LLM:                                       │
│  │  └─ llm_with_tools = llm.bind_tools([get_customer_debt]) │
│  ├─ Invoke LLM:                                              │
│  │  └─ response = await llm_with_tools.ainvoke(messages)    │
│  │     ├─ LLM decides to call: get_customer_debt(mst="...")  │
│  │     └─ Result: AIMessage with tool_calls                  │
│  └─ Result: Tool call detected                               │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 8: Tool Execution                                      │
│  ├─ Execute get_customer_debt tool:                          │
│  │  └─ HTTPGetTool.execute(mst="0123456789")                │
│  │     ├─ Format endpoint: "https://erp.com/api/debt/0123.."│
│  │     ├─ Inject JWT: headers["Authorization"] = user_jwt   │
│  │     ├─ Make HTTP GET request                             │
│  │     ├─ Response: {"total_debt": 15432.50, ...}           │
│  │     └─ Validate against output schema                    │
│  └─ Result: Tool execution successful, data returned         │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 9: Response Synthesis                                  │
│  ├─ Send tool result back to LLM:                            │
│  │  └─ messages.append(ToolMessage(tool_result))            │
│  │  └─ final_response = await llm.ainvoke(messages)         │
│  │     └─ LLM synthesizes: "Customer MST 0123456789 has..." │
│  ├─ Apply output formatting:                                 │
│  │  └─ OutputFormatter.format(response, format="structured") │
│  ├─ Build metadata:                                          │
│  │  └─ metadata = {                                          │
│  │       "agent": "AgentDebt",                               │
│  │       "intent": "customer_debt_query",                    │
│  │       "tool_calls": ["get_customer_debt"],               │
│  │       "extracted_entities": {"mst": "0123456789"},       │
│  │       "llm_model": "gpt-4o-mini",                         │
│  │       "tokens": {"input": 120, "output": 80}             │
│  │     }                                                     │
│  └─ Result: Formatted response with metadata                 │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 10: Save to Database                                   │
│  ├─ Save assistant message:                                  │
│  │  └─ INSERT INTO messages (                                │
│  │       session_id, role='assistant',                       │
│  │       content=final_response,                             │
│  │       metadata=metadata                                   │
│  │     )                                                     │
│  ├─ Update session:                                          │
│  │  └─ UPDATE sessions                                       │
│  │       SET last_message_at=NOW(), agent_id=agent_id       │
│  │       WHERE session_id=?                                  │
│  ├─ Save checkpoint (LangGraph):                             │
│  │  └─ PostgresSaver.save(thread_id, state)                 │
│  └─ Result: Conversation persisted                           │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  STEP 11: Return Response to User                            │
│  └─ HTTP 200 OK                                              │
│     {                                                        │
│       "session_id": "session-abc",                           │
│       "message_id": "msg-xyz",                               │
│       "response": "Customer MST 0123456789 has...",          │
│       "agent": "AgentDebt",                                  │
│       "metadata": {...}                                      │
│     }                                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Multi-Tenant Isolation

### 3-Layer Permission Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Agent Permission Check (SupervisorAgent)           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  _load_available_agents(tenant_id)                     │  │
│  │  └─ Query:                                              │  │
│  │     SELECT agent_configs.*                              │  │
│  │     FROM agent_configs                                  │  │
│  │     JOIN tenant_agent_permissions                       │  │
│  │       ON agent_configs.agent_id = tenant_agent...       │  │
│  │     WHERE tenant_agent_permissions.tenant_id = ?        │  │
│  │       AND tenant_agent_permissions.enabled = TRUE       │  │
│  │       AND agent_configs.is_active = TRUE                │  │
│  │                                                          │  │
│  │  Result: Tenant A sees [AgentDebt, AgentShipment]       │  │
│  │          Tenant B sees [AgentDebt, AgentAnalysis]       │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 2: Tool Permission Check (ToolLoader)                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  load_agent_tools(agent_id, tenant_id)                 │  │
│  │  └─ Query:                                              │  │
│  │     SELECT tool_configs.*                               │  │
│  │     FROM agent_tools                                    │  │
│  │     JOIN tool_configs ON ...                            │  │
│  │     WHERE agent_tools.agent_id = ?                      │  │
│  │     ORDER BY agent_tools.priority ASC                   │  │
│  │     LIMIT 5                                             │  │
│  │                                                          │  │
│  │  For each tool:                                         │  │
│  │    └─ Check tenant_tool_permissions:                    │  │
│  │       SELECT * FROM tenant_tool_permissions             │  │
│  │       WHERE tenant_id = ? AND tool_id = ?               │  │
│  │         AND enabled = TRUE                              │  │
│  │                                                          │  │
│  │  Result: Only loads tools tenant is authorized for      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 3: LLM Access Control (LLMManager)                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  get_llm_for_tenant(tenant_id)                         │  │
│  │  └─ Query:                                              │  │
│  │     SELECT tenant_llm_configs.*                         │  │
│  │     FROM tenant_llm_configs                             │  │
│  │     WHERE tenant_id = ?                                 │  │
│  │                                                          │  │
│  │  └─ Decrypt API key:                                    │  │
│  │     api_key = fernet.decrypt(encrypted_api_key)         │  │
│  │                                                          │  │
│  │  └─ Create LLM client:                                  │  │
│  │     ChatOpenAI(api_key=tenant_A_key)                    │  │
│  │                                                          │  │
│  │  Result: Each tenant uses their own LLM API key         │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Tenant Isolation Table

| Isolation Layer | Mechanism | Example |
|----------------|-----------|---------|
| **Database** | `tenant_id` foreign key in all tables | `sessions` filtered by `tenant_id` |
| **Cache** | Redis key namespacing | `agenthub:tenant-A:cache:agents` |
| **Auth** | JWT payload includes `tenant_id` | Middleware validates tenant access |
| **API Keys** | Encrypted per-tenant in `tenant_llm_configs` | Tenant A ≠ Tenant B API keys |
| **Permissions** | Junction tables for agents/tools | `tenant_agent_permissions` |
| **Sessions** | LangGraph thread IDs include tenant | `tenant_{id}__user_{id}__session_{id}` |

---

## Agent System Architecture

### Agent Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│  SupervisorAgent (Singleton per Tenant)                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Responsibilities:                                     │  │
│  │  ├─ Language detection (EN/VI)                         │  │
│  │  ├─ Intent classification                              │  │
│  │  ├─ Route to domain agent                              │  │
│  │  └─ Handle UNCLEAR/MULTI_INTENT cases                  │  │
│  │                                                          │  │
│  │  Configuration:                                         │  │
│  │  ├─ LLM: Lightweight (GPT-4o-mini)                     │  │
│  │  ├─ Prompt: Dynamic (built from available agents)      │  │
│  │  ├─ Tools: None (routing only)                         │  │
│  │  └─ Source: Code (supervisor_agent.py)                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │ Routes to ↓
        ┌──────────────────┼──────────────────┬────────────────┐
        │                  │                  │                │
┌───────▼──────┐  ┌────────▼──────┐  ┌───────▼──────┐  ┌──────▼──────┐
│  AgentDebt   │  │ AgentShipment │  │ AgentAnalysis│  │  AgentOCR   │
├──────────────┤  ├───────────────┤  ├──────────────┤  ├─────────────┤
│ Purpose:     │  │ Purpose:      │  │ Purpose:     │  │ Purpose:    │
│ Customer debt│  │ Shipment      │  │ Knowledge    │  │ Document    │
│ queries      │  │ tracking      │  │ base RAG     │  │ processing  │
│              │  │               │  │              │  │             │
│ Tools:       │  │ Tools:        │  │ Tools:       │  │ Tools:      │
│ - get_debt   │  │ - track_ship  │  │ - rag_search │  │ - ocr_doc   │
│ - pay_history│  │ - eta_check   │  │              │  │             │
│              │  │               │  │              │  │             │
│ LLM:         │  │ LLM:          │  │ LLM:         │  │ LLM:        │
│ GPT-4o       │  │ GPT-4o        │  │ GPT-4o       │  │ GPT-4o      │
│              │  │               │  │              │  │             │
│ Source:      │  │ Source:       │  │ Source:      │  │ Source:     │
│ Database     │  │ Database      │  │ Database     │  │ Database    │
│ (agent_id=..)│  │ (agent_id=..) │  │ (agent_id=..)│  │ (agent_id=..)│
└──────────────┘  └───────────────┘  └──────────────┘  └─────────────┘
```

### Agent Configuration Flow

```
1. Admin creates agent via API:
   POST /api/admin/agents
   {
     "name": "AgentInventory",
     "prompt_template": "You are an inventory management assistant...",
     "llm_model_id": "uuid-gpt4o",
     "default_output_format_id": "uuid-json"
   }

2. Database insert:
   INSERT INTO agent_configs (...)
   → agent_id = "uuid-new-agent"

3. Assign tools:
   POST /api/admin/agents/uuid-new-agent/tools
   {
     "tools": [
       {"tool_id": "uuid-tool-1", "priority": 1},
       {"tool_id": "uuid-tool-2", "priority": 2}
     ]
   }

4. Grant tenant permission:
   POST /api/admin/tenants/tenant-A/permissions
   {
     "agent_id": "uuid-new-agent",
     "enabled": true
   }

5. Agent immediately available:
   User (Tenant A): "Check inventory for SKU-12345"
   → SupervisorAgent loads AgentInventory dynamically
   → Routes to new agent
   → Agent executes with assigned tools
```

---

## Tool Loading System

### Dynamic Tool Creation

```
┌──────────────────────────────────────────────────────────────┐
│  ToolLoader.load_agent_tools(agent_id, tenant_id)            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 1: Query Database                                │  │
│  │  └─ SELECT tool_configs.*, agent_tools.priority        │  │
│  │     FROM agent_tools                                    │  │
│  │     JOIN tool_configs ON ...                            │  │
│  │     WHERE agent_id = ? ORDER BY priority ASC LIMIT 5    │  │
│  │                                                          │  │
│  │  Result: [                                              │  │
│  │    {                                                    │  │
│  │      "tool_id": "uuid-1",                               │  │
│  │      "name": "get_customer_debt",                       │  │
│  │      "base_tool_type": "HTTP_GET",                      │  │
│  │      "config": {                                        │  │
│  │        "endpoint": "https://erp.com/api/debt/{mst}",    │  │
│  │        "method": "GET",                                 │  │
│  │        "headers": {"X-API-Version": "v1"}               │  │
│  │      },                                                 │  │
│  │      "input_schema": {                                  │  │
│  │        "type": "object",                                │  │
│  │        "properties": {                                  │  │
│  │          "mst": {"type": "string", "pattern": "^[0-9]"}│  │
│  │        }                                                │  │
│  │      },                                                 │  │
│  │      "priority": 1                                      │  │
│  │    },                                                   │  │
│  │    ...                                                  │  │
│  │  ]                                                      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 2: Check Tenant Permissions                      │  │
│  │  └─ For each tool:                                      │  │
│  │     SELECT * FROM tenant_tool_permissions               │  │
│  │     WHERE tenant_id = ? AND tool_id = ? AND enabled=TRUE│  │
│  │                                                          │  │
│  │  └─ If permission missing:                              │  │
│  │     logger.warning("Tenant not permitted for tool")     │  │
│  │     continue (skip tool)                                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 3: Create StructuredTool Instances               │  │
│  │  └─ tool_class = HTTPGetTool | HTTPPostTool | RAGTool  │  │
│  │  └─ input_schema_pydantic = create_model_from_schema() │  │
│  │  └─ tool = StructuredTool.from_function(               │  │
│  │       name="get_customer_debt",                         │  │
│  │       description="Retrieve customer debt by MST",      │  │
│  │       func=tool_class.execute,                          │  │
│  │       args_schema=input_schema_pydantic                 │  │
│  │     )                                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 4: Inject JWT Context                            │  │
│  │  └─ tool.metadata = {                                   │  │
│  │       "user_jwt": current_user_jwt,                     │  │
│  │       "tenant_id": tenant_id                            │  │
│  │     }                                                   │  │
│  │  └─ When tool executes, JWT auto-injected in headers   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Return: [StructuredTool, StructuredTool, ...]              │
└──────────────────────────────────────────────────────────────┘
```

### Tool Types & Handlers

| Tool Type | Handler Class | Config Fields | Use Case |
|-----------|--------------|---------------|----------|
| **HTTP_GET** | `tools.http.HTTPGetTool` | endpoint, headers, timeout | Retrieve data from REST APIs |
| **HTTP_POST** | `tools.http.HTTPPostTool` | endpoint, headers, body_template, timeout | Submit data to external systems |
| **RAG** | `tools.rag.RAGTool` | collection_name, top_k, similarity_threshold | Search knowledge base in ChromaDB |
| **DB_QUERY** | `tools.db.DBQueryTool` (future) | query_template, connection_string | Execute SQL queries |
| **OCR** | `tools.ocr.OCRTool` (future) | ocr_service_url, supported_formats | Process documents |

---

## LLM Management

### Multi-Provider Support Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  LLMManager.get_llm_for_tenant(tenant_id)                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 1: Check Redis Cache                             │  │
│  │  └─ redis_key = f"agenthub:{tenant_id}:llm"            │  │
│  │  └─ cached_client = redis.get(redis_key)               │  │
│  │  └─ if cached_client:                                  │  │
│  │       return pickle.loads(cached_client)               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 2: Load from Database (Cache Miss)               │  │
│  │  └─ tenant_config = db.query(TenantLLMConfig)          │  │
│  │                       .filter(tenant_id=tenant_id)      │  │
│  │                       .join(LLMModel)                   │  │
│  │                       .first()                          │  │
│  │                                                          │  │
│  │  └─ Result: {                                           │  │
│  │       "llm_model": {                                    │  │
│  │         "provider": "openai",                           │  │
│  │         "model_name": "gpt-4o-mini",                    │  │
│  │         "context_window": 128000                        │  │
│  │       },                                                │  │
│  │       "encrypted_api_key": "gAAAAABf...",              │  │
│  │       "rate_limit_rpm": 60                              │  │
│  │     }                                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 3: Decrypt API Key                               │  │
│  │  └─ fernet = Fernet(FERNET_KEY)                        │  │
│  │  └─ api_key = fernet.decrypt(encrypted_api_key)        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 4: Create Provider-Specific Client               │  │
│  │  └─ if provider == "openai":                           │  │
│  │       llm = ChatOpenAI(                                 │  │
│  │         api_key=api_key,                                │  │
│  │         model="gpt-4o-mini",                            │  │
│  │         temperature=0,                                  │  │
│  │         max_tokens=2000                                 │  │
│  │       )                                                 │  │
│  │  └─ elif provider == "gemini":                         │  │
│  │       llm = ChatGoogleGenerativeAI(...)                │  │
│  │  └─ elif provider == "anthropic":                      │  │
│  │       llm = ChatAnthropic(...)                         │  │
│  │  └─ elif provider == "openrouter":                     │  │
│  │       llm = ChatOpenAI(                                 │  │
│  │         base_url="https://openrouter.ai/api/v1",       │  │
│  │         api_key=api_key,                                │  │
│  │         model="..."                                     │  │
│  │       )                                                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Step 5: Cache Client                                  │  │
│  │  └─ redis.setex(                                        │  │
│  │       redis_key,                                        │  │
│  │       3600,  # 1 hour TTL                               │  │
│  │       pickle.dumps(llm)                                 │  │
│  │     )                                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Return: llm (ChatOpenAI | ChatGoogleGenerativeAI | ...)    │
└──────────────────────────────────────────────────────────────┘
```

### Provider Comparison

| Provider | Models Supported | Context Window | Cost (per 1M tokens) | Best For |
|----------|-----------------|----------------|---------------------|----------|
| **OpenAI** | GPT-4o, GPT-4o-mini | 128k | Input: $2.50, Output: $10 | Function calling, reasoning |
| **Google Gemini** | Gemini 1.5 Pro | 1M tokens | Input: $1.25, Output: $3.75 | Long context, multimodal |
| **Anthropic Claude** | Claude 3.5 Sonnet | 200k | Input: $3, Output: $15 | Complex reasoning, safety |
| **OpenRouter** | Multiple (unified API) | Varies | Varies | Cost optimization, fallback |

---

## Caching Strategy

### Redis Cache Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Redis Cache Namespacing                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Pattern: agenthub:{tenant_id}:cache:{resource}:{id}   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Cache Keys:                                                 │
│  ├─ agenthub:tenant-A:llm                                    │
│  │  └─ Value: Serialized ChatOpenAI client                  │
│  │  └─ TTL: 3600s (1 hour)                                  │
│  │                                                           │
│  ├─ agenthub:tenant-A:cache:agent:uuid-agent-debt           │
│  │  └─ Value: AgentConfig JSON                              │
│  │  └─ TTL: 3600s                                           │
│  │                                                           │
│  ├─ agenthub:tenant-A:cache:tool:uuid-tool-1                │
│  │  └─ Value: ToolConfig JSON                               │
│  │  └─ TTL: 3600s                                           │
│  │                                                           │
│  ├─ agenthub:tenant-A:cache:permissions:agents              │
│  │  └─ Value: List of enabled agent_ids for tenant         │
│  │  └─ TTL: 1800s (30 min)                                  │
│  │                                                           │
│  └─ agenthub:tenant-A:cache:permissions:tools               │
│     └─ Value: List of enabled tool_ids for tenant          │
│     └─ TTL: 1800s                                           │
└──────────────────────────────────────────────────────────────┘

Cache Invalidation Strategies:
┌────────────────────────────────────────────────────────────┐
│  1. TTL-Based (Passive)                                    │
│     └─ Keys expire after 1 hour automatically              │
│                                                             │
│  2. Manual Reload (Active)                                 │
│     └─ POST /api/admin/agents/reload                       │
│     └─ Deletes all agenthub:*:cache:agent:* keys          │
│                                                             │
│  3. Write-Through (On Update)                              │
│     └─ PATCH /api/admin/agents/{id}                        │
│     └─ Update database + invalidate specific cache key     │
└────────────────────────────────────────────────────────────┘

Performance Metrics:
┌────────────────────────────────────────────────────────────┐
│  Cache Hit Rate Target: >90%                               │
│                                                             │
│  Request 1 (Cold Cache):                                   │
│  ├─ Load LLM from DB: ~300ms                               │
│  ├─ Load Tools from DB: ~100ms                             │
│  └─ Total: ~400ms                                          │
│                                                             │
│  Request 2+ (Warm Cache):                                  │
│  ├─ Load LLM from Redis: ~5ms                              │
│  ├─ Load Tools from Redis: ~5ms                            │
│  └─ Total: ~10ms (40x faster!)                             │
└────────────────────────────────────────────────────────────┘
```

---

## Database Design

### Schema Overview (13 Tables)

```
Configuration Cluster:
┌─────────────┐       ┌──────────────────┐       ┌────────────┐
│   tenants   │◄──────┤ tenant_llm_config├──────►│ llm_models │
└─────┬───────┘       └──────────────────┘       └────────────┘
      │
      ├────► sessions (1:N)
      ├────► tenant_agent_permissions (1:N)
      └────► tenant_tool_permissions (1:N)

Agent/Tool Cluster:
┌──────────────┐       ┌─────────────┐       ┌──────────────┐
│  base_tools  ├──────►│ tool_configs│◄──────┤output_formats│
└──────────────┘       └──────┬──────┘       └──────────────┘
                              │
                              │ N:M
                              ▼
                      ┌───────────────┐
                      │  agent_tools  │
                      └───────┬───────┘
                              │
                              ▼
                      ┌───────────────┐
                      │ agent_configs │
                      └───────────────┘

Conversation Cluster:
┌──────────────┐
│   sessions   │
└──────┬───────┘
       │ 1:N
       ▼
┌──────────────┐
│   messages   │
└──────────────┘

State Management:
┌──────────────┐
│ checkpoints  │ (LangGraph PostgresSaver)
└──────────────┘
```

### Key Indexes for Performance

```sql
-- Multi-tenant isolation
CREATE INDEX idx_sessions_tenant_user
  ON sessions(tenant_id, user_id, created_at DESC);

-- Agent permission lookup
CREATE INDEX idx_tenant_agent_perms
  ON tenant_agent_permissions(tenant_id, agent_id)
  WHERE enabled = TRUE;

-- Tool permission lookup
CREATE INDEX idx_tenant_tool_perms
  ON tenant_tool_permissions(tenant_id, tool_id)
  WHERE enabled = TRUE;

-- Priority-based tool filtering
CREATE INDEX idx_agent_tools_priority
  ON agent_tools(agent_id, priority ASC);

-- Message chronological retrieval
CREATE INDEX idx_messages_session_time
  ON messages(session_id, timestamp ASC);
```

---

## Security Architecture

### Authentication Flow

```
┌──────────────────────────────────────────────────────────────┐
│  1. External Auth Provider (OAuth2/SSO)                      │
│     └─ User logs in → Issues JWT token (RS256)              │
│                                                              │
│     JWT Payload:                                             │
│     {                                                        │
│       "sub": "user-123",                                     │
│       "tenant_id": "tenant-A",                               │
│       "email": "user@example.com",                           │
│       "roles": ["user"],                                     │
│       "exp": 1699999999,                                     │
│       "iat": 1699900000                                      │
│     }                                                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│  2. User sends request with JWT                              │
│     POST /api/tenant-A/chat                                  │
│     Headers:                                                 │
│       Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI...   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│  3. JWT Authentication Middleware (middleware/auth.py)       │
│     ┌──────────────────────────────────────────────────────┐│
│     │  Step 1: Extract Token                               ││
│     │  └─ header = request.headers.get("Authorization")    ││
│     │  └─ token = header.split("Bearer ")[1]               ││
│     └──────────────────────────────────────────────────────┘│
│     ┌──────────────────────────────────────────────────────┐│
│     │  Step 2: Validate Signature                          ││
│     │  └─ jwt.decode(                                       ││
│     │       token,                                          ││
│     │       JWT_PUBLIC_KEY,  # RS256 public key            ││
│     │       algorithms=["RS256"]                            ││
│     │     )                                                 ││
│     │  └─ Raises InvalidSignatureError if tampered         ││
│     └──────────────────────────────────────────────────────┘│
│     ┌──────────────────────────────────────────────────────┐│
│     │  Step 3: Check Expiration                            ││
│     │  └─ if payload["exp"] < current_time:                ││
│     │       raise HTTPException(401, "Token expired")       ││
│     └──────────────────────────────────────────────────────┘│
│     ┌──────────────────────────────────────────────────────┐│
│     │  Step 4: Validate Tenant Access                      ││
│     │  └─ url_tenant_id = request.path_params["tenant_id"] ││
│     │  └─ jwt_tenant_id = payload["tenant_id"]             ││
│     │  └─ if url_tenant_id != jwt_tenant_id:               ││
│     │       raise HTTPException(403, "Forbidden")           ││
│     └──────────────────────────────────────────────────────┘│
│     ┌──────────────────────────────────────────────────────┐│
│     │  Step 5: Attach Context to Request                   ││
│     │  └─ request.state.user_id = payload["sub"]           ││
│     │  └─ request.state.tenant_id = payload["tenant_id"]   ││
│     │  └─ request.state.jwt_token = token                  ││
│     └──────────────────────────────────────────────────────┘│
└──────────────────────────┬───────────────────────────────────┘
                           │
                       ✅ Authenticated
                       Proceed to handler
```

### Encryption Strategy

```
API Key Encryption (Fernet Symmetric):
┌────────────────────────────────────────────────────────────┐
│  Encrypt (on tenant onboarding):                           │
│  └─ plaintext_key = "sk-abc123..."                        │
│  └─ fernet = Fernet(FERNET_KEY)                           │
│  └─ encrypted_key = fernet.encrypt(plaintext_key.encode())│
│  └─ INSERT INTO tenant_llm_configs (encrypted_api_key)    │
│                                                             │
│  Decrypt (at runtime):                                     │
│  └─ encrypted_key = db.tenant_llm_configs.encrypted_api_key│
│  └─ plaintext_key = fernet.decrypt(encrypted_key).decode()│
│  └─ ChatOpenAI(api_key=plaintext_key)                     │
└────────────────────────────────────────────────────────────┘

FERNET_KEY Management:
├─ Stored in environment variable (never in code/DB)
├─ Rotated quarterly (requires re-encrypting all API keys)
├─ Access restricted to backend application only
└─ Backed up securely (encrypted backup)
```

---

## Technology Stack Details

### Backend Stack

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| **Web Framework** | FastAPI | 0.104+ | Async REST API |
| **ASGI Server** | Uvicorn | 0.24+ | Production server |
| **Agent Framework** | LangChain | 0.3+ | LLM orchestration |
| **State Management** | LangGraph | 0.2+ | Checkpointing |
| **Database ORM** | SQLAlchemy | 2.0+ | Async ORM |
| **Migrations** | Alembic | 1.12+ | Schema versioning |
| **Cache** | Redis-py | 5.0+ | Redis client |
| **Validation** | Pydantic | 2.0+ | Data schemas |
| **Auth** | PyJWT | 2.8+ | JWT validation |
| **Encryption** | Cryptography | 41+ | Fernet encryption |
| **Logging** | Structlog | 23+ | Structured logs |
| **Testing** | Pytest | 7.4+ | Test framework |

### Infrastructure Stack

```
Production Deployment Architecture:

┌──────────────────────────────────────────────────────────┐
│  Load Balancer (NGINX / AWS ALB)                         │
│  ├─ SSL Termination (TLS 1.3)                            │
│  ├─ Rate Limiting (per tenant)                           │
│  └─ Health Check: /health                                │
└────────────────────┬─────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼────┐    ┌─────▼────┐    ┌────▼────┐
│ FastAPI │    │ FastAPI  │    │ FastAPI │
│ Worker 1│    │ Worker 2 │    │ Worker 3│
└────┬────┘    └─────┬────┘    └────┬────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼────────┐ ┌───▼──────┐ ┌──────▼────┐
│ PostgreSQL  │ │  Redis   │ │ ChromaDB  │
│ (Primary)   │ │ (Cache)  │ │ (Vectors) │
│             │ │          │ │           │
│ Replicas:   │ │ Sentinel │ │ Persistent│
│ - Read      │ │ HA       │ │ Volume    │
│ - Standby   │ │          │ │           │
└─────────────┘ └──────────┘ └───────────┘
```

---

## Performance Characteristics

### Latency Targets

| Operation | Target | Measured | Notes |
|-----------|--------|----------|-------|
| **Chat Query (Simple)** | <2.5s | P95: 1.8s | No RAG, single tool call |
| **Chat Query (RAG)** | <4s | P95: 3.2s | Includes vector search |
| **Agent Config Load** | <10ms | Avg: 5ms | From Redis cache |
| **Tool Load** | <10ms | Avg: 8ms | From Redis cache |
| **DB Write (Message)** | <50ms | Avg: 25ms | Single INSERT |
| **LLM Call (GPT-4o-mini)** | <1.5s | Avg: 800ms | Depends on OpenAI |

### Scalability Metrics

```
Horizontal Scaling:
├─ FastAPI Workers: Auto-scale based on CPU (target: 70%)
├─ PostgreSQL: Read replicas for query load distribution
├─ Redis: Redis Cluster for cache sharding
└─ ChromaDB: Sharded collections by tenant

Capacity Planning:
├─ 1 FastAPI worker: ~50 concurrent requests
├─ 3 workers: ~150 concurrent requests
├─ PostgreSQL connection pool: 20 connections per worker
├─ Redis: 256MB cache (LRU eviction)
└─ Expected throughput: 1000 req/min per worker
```

---

## Related Documents

- **[Chatbot Specification](01_CHATBOT_SPECIFICATION.md)** - Requirements and features
- **[Database Schema](04_DATABASE_SCHEMA_ERD.md)** - Complete data model
- **[Security Guide](08_SECURITY_GUIDE.md)** - Authentication and encryption details
- **[Operations Guide](11_OPERATIONS_GUIDE.md)** - Monitoring and maintenance

---

**Document Status**: ✅ Complete
**Review Date**: 2025-11-03
**Maintained By**: Platform Architecture Team
