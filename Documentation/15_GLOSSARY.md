# Glossary - AgentHub Multi-Agent Chatbot Framework

**Document Version**: 1.0
**Last Updated**: 2025-11-03

---

## A

**Agent**
A specialized AI assistant that handles specific business domains (e.g., AgentDebt for customer debt queries). Each agent has its own prompt, tools, and LLM configuration.

**Agent Config**
Database record in `agent_configs` table defining an agent's behavior, including system prompt, LLM model, and output format.

**Agent Permission**
Entry in `tenant_agent_permissions` table controlling which agents a tenant can access.

**Alembic**
Database migration tool for SQLAlchemy. Used to version and manage database schema changes.

**API Key Encryption**
Process of encrypting LLM provider API keys using Fernet symmetric encryption before storing in the database.

---

## B

**Base Tool**
Template defining a tool type (HTTP_GET, HTTP_POST, RAG, etc.) in the `base_tools` table. Tool instances are created from these templates.

---

## C

**Cache Hit Rate**
Percentage of requests served from Redis cache instead of database. Target: >90%.

**Cache Stampede**
Situation where multiple requests simultaneously try to regenerate an expired cache entry, overloading the database.

**Checkpoint**
Serialized conversation state saved by LangGraph PostgresSaver, allowing conversation continuity across requests.

**ChromaDB**
Vector database used for storing and searching document embeddings in RAG (Retrieval-Augmented Generation) operations.

**Context Window**
Maximum number of tokens (words/characters) an LLM can process in a single request. Varies by model (e.g., 128k for GPT-4o, 1M for Gemini 1.5 Pro).

**Cross-Tenant Data Leakage**
Security vulnerability where one tenant can access another tenant's data. Prevented through multi-layer isolation.

---

## D

**Domain Agent**
Specialized agent handling specific business domains (debt, shipment, inventory, etc.). Extends base `DomainAgent` class.

**Dynamic Tool Loading**
Process of creating tool instances from database configurations at runtime, without code changes.

---

## E

**Entity Extraction**
Process of identifying and extracting specific data fields (MST, SKU, dates, etc.) from user messages using LLM analysis.

**Encrypted API Key**
LLM provider API key encrypted with Fernet before storage in `tenant_llm_configs.encrypted_api_key` column.

---

## F

**FastAPI**
Modern Python web framework used for building the REST API. Provides async support and auto-generated API documentation.

**Fernet**
Symmetric encryption algorithm (part of Cryptography library) used to encrypt tenant API keys.

---

## G

**GPT-4o / GPT-4o-mini**
OpenAI's language models. GPT-4o-mini is lightweight and cost-effective, used for SupervisorAgent routing.

---

## H

**Handler Class**
Python class path (e.g., `tools.http.HTTPGetTool`) that implements tool execution logic.

**HTTP GET Tool**
Tool type that makes GET requests to external APIs, automatically injecting user JWT tokens.

**HTTP POST Tool**
Tool type that makes POST requests to external APIs with configurable body templates.

---

## I

**Input Schema**
JSON Schema defining required and optional parameters for a tool. Used for validation and LLM parameter extraction.

**Intent Detection**
Process by which SupervisorAgent analyzes user messages to determine which domain agent should handle the request.

---

## J

**JSON Schema**
Standard format for defining the structure of JSON data. Used for tool input/output validation.

**JWT (JSON Web Token)**
Authentication token format using RS256 signature. Contains user_id, tenant_id, and expiration claims.

---

## L

**LangChain**
Framework for building LLM-powered applications. Provides abstractions for agents, tools, prompts, and chains.

**LangGraph**
Extension of LangChain for building stateful, graph-based agent workflows with checkpointing support.

**LLM (Large Language Model)**
AI model (GPT-4o, Gemini, Claude) that generates text responses. Used for intent detection, entity extraction, and response synthesis.

**LLM Manager**
Service (`llm_manager.py`) that loads tenant-specific LLM configurations and creates authenticated LLM clients.

---

## M

**Message**
Individual chat message in a conversation, stored in `messages` table with role (user/assistant), content, and metadata.

**Metadata**
JSON object attached to messages containing intent, tool_calls, extracted_entities, token counts, and duration.

**Multi-Intent Query**
User message containing multiple questions or intents. MVP rejects these; future versions will support sequential execution.

**Multi-Tenant**
Architecture supporting multiple isolated organizations (tenants) on shared infrastructure with complete data separation.

**MST**
Mã Số Thuế (Vietnamese tax code). 10-digit identifier for Vietnamese businesses. Example: 0123456789.

---

## N

**Namespace**
Prefix pattern used in Redis cache keys to isolate tenant data. Format: `agenthub:{tenant_id}:cache:{resource}`.

---

## O

**OCR (Optical Character Recognition)**
Tool type for extracting text from documents (PDFs, images). Planned future enhancement.

**OpenRouter**
Service providing unified API access to multiple LLM providers (OpenAI, Anthropic, Google, etc.).

**Output Format**
Response format definition (structured_json, markdown_table, chart_data, summary_text) stored in `output_formats` table.

---

## P

**Permission Layer**
One of three security layers: L1 (Agent permissions), L2 (Tool permissions), L3 (LLM access control).

**PostgreSQL**
Relational database storing 13 core tables (tenants, agents, tools, sessions, messages, etc.).

**PostgresSaver**
LangGraph component that saves conversation checkpoints to PostgreSQL for state persistence.

**Priority**
Integer field in `agent_tools` table controlling tool visibility. Lower number = higher priority (1 is highest).

**Prompt Template**
System prompt defining an agent's role, capabilities, and behavior. Stored in `agent_configs.prompt_template`.

**Pydantic**
Python library for data validation and settings management using type annotations.

---

## R

**RAG (Retrieval-Augmented Generation)**
Technique combining vector search (ChromaDB) with LLM generation to answer questions from knowledge base documents.

**RAG Tool**
Tool type that performs semantic search over ChromaDB collections and synthesizes answers.

**Rate Limit**
Restrictions on API usage per tenant (requests per minute, tokens per minute) stored in `tenant_llm_configs`.

**Redis**
In-memory cache used for storing LLM clients, agent configs, and tool configs with 1-hour TTL.

**Renderer Hint**
JSON object in output formats providing UI guidance (table, chart, json display) for frontend rendering.

**Request Coalescing**
Technique to combine multiple simultaneous identical requests into single backend operation.

**RS256**
RSA signature algorithm using public/private key pair. Used for JWT token validation.

---

## S

**Session**
Conversation thread between user and chatbot, stored in `sessions` table with unique `session_id`.

**Sliding Window**
Context management strategy keeping last N messages (default: 10) + system prompt, discarding older messages.

**SQLAlchemy**
Python ORM (Object-Relational Mapping) library providing database abstraction layer.

**Structured Tool**
LangChain tool instance created from database configuration with typed input schema and execution function.

**Structlog**
Structured logging library outputting JSON-formatted logs with context (tenant_id, user_id, timestamps).

**SupervisorAgent**
Central routing agent that detects intent and language, then routes messages to appropriate domain agents.

---

## T

**Tenant**
Organization/company using the chatbot system. Stored in `tenants` table with unique `tenant_id` (UUID).

**Tenant Isolation**
Architecture ensuring complete data separation between tenants at database, cache, and application layers.

**Thread ID**
Unique identifier for conversation state in LangGraph. Format: `tenant_{id}__user_{id}__session_{id}`.

**Token**
Unit of text processed by LLMs. Approximately 4 characters or 0.75 words. Used for cost calculation.

**Tool**
Executable function that agents can call (HTTP API, database query, RAG search, etc.). Defined in `tool_configs` table.

**Tool Execution**
Process of running a tool with extracted parameters and returning results to the agent.

**Tool Loader**
Service (`tool_loader.py`) that creates LangChain tool instances from database configurations.

**Tool Permission**
Entry in `tenant_tool_permissions` table controlling which tools a tenant's agents can use.

**TTL (Time To Live)**
Duration before Redis cache entry expires. Default: 3600 seconds (1 hour) for configs.

---

## U

**Uvicorn**
ASGI server for running FastAPI applications in production.

**UUID (Universally Unique Identifier)**
128-bit identifier format (e.g., `550e8400-e29b-41d4-a716-446655440000`) used for database primary keys.

---

## V

**Vector Database**
Database optimized for similarity search over embeddings. ChromaDB used for RAG knowledge base queries.

**Vector Embedding**
Numerical representation of text enabling semantic similarity comparisons.

---

## W

**Webhook**
HTTP callback triggered by events (tool execution, agent routing). Planned future enhancement.

---

## Acronyms

| Acronym | Full Term | Meaning |
|---------|-----------|---------|
| **API** | Application Programming Interface | Interface for software communication |
| **ASGI** | Asynchronous Server Gateway Interface | Python async web server standard |
| **CRUD** | Create, Read, Update, Delete | Basic database operations |
| **CRM** | Customer Relationship Management | Business software for customer data |
| **DB** | Database | Structured data storage |
| **ERP** | Enterprise Resource Planning | Business management software |
| **FK** | Foreign Key | Database relationship reference |
| **HTTP** | Hypertext Transfer Protocol | Web communication protocol |
| **JSON** | JavaScript Object Notation | Data interchange format |
| **JSONB** | JSON Binary | PostgreSQL binary JSON storage |
| **JWT** | JSON Web Token | Authentication token format |
| **LLM** | Large Language Model | AI text generation model |
| **LRU** | Least Recently Used | Cache eviction algorithm |
| **MST** | Mã Số Thuế | Vietnamese tax code |
| **OCR** | Optical Character Recognition | Text extraction from images |
| **ORM** | Object-Relational Mapping | Database abstraction layer |
| **PII** | Personally Identifiable Information | Sensitive personal data |
| **PK** | Primary Key | Unique database row identifier |
| **RAG** | Retrieval-Augmented Generation | Vector search + LLM synthesis |
| **RBAC** | Role-Based Access Control | Permission system |
| **REST** | Representational State Transfer | API architectural style |
| **RPM** | Requests Per Minute | Rate limit metric |
| **RS256** | RSA Signature with SHA-256 | JWT signing algorithm |
| **SaaS** | Software as a Service | Cloud-hosted software model |
| **SKU** | Stock Keeping Unit | Product identifier |
| **SQL** | Structured Query Language | Database query language |
| **SSO** | Single Sign-On | Centralized authentication |
| **TLS** | Transport Layer Security | Encryption protocol |
| **TPM** | Tokens Per Minute | LLM rate limit metric |
| **TTL** | Time To Live | Cache expiration time |
| **UI** | User Interface | Visual interaction layer |
| **URL** | Uniform Resource Locator | Web address |
| **UUID** | Universally Unique Identifier | 128-bit unique ID |

---

## Related Documents

- **[Chatbot Specification](01_CHATBOT_SPECIFICATION.md)** - Features and requirements
- **[System Architecture](02_SYSTEM_ARCHITECTURE.md)** - Technical design
- **[Quick Start](13_QUICKSTART.md)** - Getting started guide
- **[API Reference](05_API_REFERENCE_AND_GUIDES.md)** - Endpoint documentation

---

**Document Status**: ✅ Complete
**Maintained By**: Documentation Team
