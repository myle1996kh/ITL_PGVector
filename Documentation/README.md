# AgentHub Multi-Agent Chatbot Framework - Documentation

**Version**: 1.0
**Last Updated**: 2025-11-03
**Project**: ITL_Base_28.10

---

## Welcome

This documentation provides comprehensive guidance for the **AgentHub Multi-Agent Chatbot Framework**, a production-ready, multi-tenant chatbot system built with FastAPI, LangChain 0.3+, and intelligent agent orchestration.

---

## Quick Navigation

### Getting Started
- **[Quick Start Guide](13_QUICKSTART.md)** - Get up and running in 10 minutes
- **[Developer Setup](06_DEVELOPER_SETUP.md)** - Complete development environment setup
- **[Deployment Guide](07_DEPLOYMENT_GUIDE.md)** - Production deployment instructions

### Understanding the System
- **[Chatbot Specification](01_CHATBOT_SPECIFICATION.md)** - Features, requirements, and scope
- **[System Architecture](02_SYSTEM_ARCHITECTURE.md)** - Architecture diagrams and design patterns
- **[Database Schema & ERD](04_DATABASE_SCHEMA_ERD.md)** - Complete data model with 13 tables

### Configuration & Management
- **[Tenant Onboarding Guide](03_TENANT_ONBOARDING_GUIDE.md)** - Multi-tenant setup and configuration
- **[Security Guide](08_SECURITY_GUIDE.md)** - Authentication, encryption, and permissions
- **[Operations Guide](11_OPERATIONS_GUIDE.md)** - Monitoring, logging, and maintenance

### Development
- **[API Reference](05_API_REFERENCE.md)** - Complete REST API documentation
- **[Tool Development](09_TOOL_DEVELOPMENT.md)** - Creating and configuring custom tools
- **[Agent Development](10_AGENT_DEVELOPMENT.md)** - Building domain-specific agents
- **[Testing Guide](12_TESTING_GUIDE.md)** - Testing strategies and examples

### Reference
- **[Troubleshooting & FAQ](14_TROUBLESHOOTING_FAQ.md)** - Common issues and solutions
- **[Glossary](15_GLOSSARY.md)** - Terms, concepts, and acronyms

---

## Documentation Structure

### 01. Chatbot Specification
**Purpose**: Define what the system does and why
**Audience**: Product managers, stakeholders, developers
**Contents**: Features, user stories, success criteria, scope

### 02. System Architecture
**Purpose**: Explain how the system works
**Audience**: Developers, architects, DevOps
**Contents**: Components, data flow, multi-tenant isolation, caching

### 03. Tenant Onboarding Guide
**Purpose**: Step-by-step guide to onboard new tenants
**Audience**: System administrators, integrators
**Contents**: 4-step process, database setup, permissions, testing

### 04. Database Schema & ERD
**Purpose**: Complete data model documentation
**Audience**: Database administrators, developers
**Contents**: 13 tables, relationships, indexes, seed data

### 05. API Reference
**Purpose**: REST API endpoint documentation
**Audience**: Frontend developers, API consumers
**Contents**: Endpoints, schemas, authentication, examples

### 06. Developer Setup
**Purpose**: Local development environment setup
**Audience**: New developers joining the project
**Contents**: Installation, configuration, running services, testing

### 07. Deployment Guide
**Purpose**: Production deployment procedures
**Audience**: DevOps engineers, system administrators
**Contents**: Docker, environment variables, SSL, monitoring

### 08. Security Guide
**Purpose**: Security mechanisms and best practices
**Audience**: Security engineers, compliance teams
**Contents**: JWT auth, encryption, permissions, audit logging

### 09. Tool Development
**Purpose**: Create and integrate custom tools
**Audience**: Integration developers, backend engineers
**Contents**: Tool types, schemas, dynamic loading, JWT injection

### 10. Agent Development
**Purpose**: Build domain-specific conversational agents
**Audience**: AI/ML engineers, backend developers
**Contents**: Agent patterns, prompt engineering, tool assignment

### 11. Operations Guide
**Purpose**: Day-to-day system operations
**Audience**: Operations teams, SREs
**Contents**: Monitoring, metrics, logging, maintenance, troubleshooting

### 12. Testing Guide
**Purpose**: Comprehensive testing strategies
**Audience**: QA engineers, developers
**Contents**: Unit, integration, E2E, performance, security testing

### 13. Quick Start
**Purpose**: Get running in 10 minutes
**Audience**: Developers wanting quick overview
**Contents**: Minimal setup, first chatbot query, example flows

### 14. Troubleshooting & FAQ
**Purpose**: Solve common problems quickly
**Audience**: All users
**Contents**: Error messages, solutions, debugging tips

### 15. Glossary
**Purpose**: Define terms and concepts
**Audience**: All users
**Contents**: Terminology, acronyms, technical definitions

---

## Key Features

### Multi-Agent Architecture
- **SupervisorAgent**: Intelligent intent detection and routing
- **Domain Agents**: Specialized agents (Debt, Shipment, Analysis, OCR)
- **Dynamic Loading**: Agents configured via database, no code changes

### Dynamic Tool System
- **5 Tool Types**: HTTP GET/POST, RAG, Database Query, OCR
- **JSON Schema**: Define tools with input/output schemas
- **Auto JWT Injection**: Seamless authentication to external APIs
- **Priority Filtering**: Top-N tool selection for optimal performance

### Multi-Tenant Isolation
- **Complete Data Isolation**: Separate configurations per tenant
- **3-Layer Permissions**: Agent, Tool, LLM access control
- **Encrypted API Keys**: Fernet encryption at rest
- **Namespaced Caching**: Redis keys scoped to tenant_id

### LLM Provider Support
- **OpenAI**: GPT-4o, GPT-4o-mini
- **Google Gemini**: Gemini 1.5 Pro
- **Anthropic Claude**: Claude 3.5 Sonnet
- **OpenRouter**: Unified API for multiple providers

### Production-Ready
- **FastAPI**: Async, high-performance API
- **PostgreSQL**: 13-table relational schema
- **Redis**: Configuration caching, session state
- **ChromaDB**: Vector database for RAG
- **Structured Logging**: JSON logs with context
- **Health Checks**: Monitoring and observability

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI | Async REST API |
| **Agent Orchestration** | LangChain 0.3+ | LLM workflows |
| **State Management** | LangGraph 0.2+ | Conversation checkpointing |
| **Database** | PostgreSQL 15+ | Relational data |
| **Cache** | Redis 7.x | Configuration caching |
| **Vector DB** | ChromaDB | RAG embeddings |
| **ORM** | SQLAlchemy 2.0+ | Database abstraction |
| **Validation** | Pydantic 2.0+ | Schema validation |
| **Authentication** | JWT (RS256) | Token-based auth |
| **Encryption** | Fernet | API key encryption |
| **Logging** | Structlog | Structured logging |
| **Migrations** | Alembic | Database versioning |
| **Testing** | Pytest | Unit/integration tests |
| **Containerization** | Docker Compose | Service orchestration |

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User / Frontend                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP + JWT
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Middleware: Auth (JWT) + Logging                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Routes: /chat, /sessions, /admin/*               │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Supervisor   │  │ LLM Manager  │  │ Tool Loader  │      │
│  │ Agent        │  │              │  │              │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Domain Agents: AgentDebt, AgentShipment, ...        │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌───────────────┐ ┌──────────┐ ┌─────────────┐
│  PostgreSQL   │ │  Redis   │ │  ChromaDB   │
│  (Data)       │ │  (Cache) │ │  (Vectors)  │
└───────────────┘ └──────────┘ └─────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              External APIs (ERP, CRM, Services)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Overview

### 13 Core Tables

**Configuration Tables**:
1. `tenants` - Organizations using the system
2. `llm_models` - Available LLM providers/models
3. `tenant_llm_configs` - Tenant-specific LLM settings
4. `base_tools` - Tool type templates
5. `output_formats` - Response format definitions

**Agent & Tool System**:
6. `tool_configs` - Specific tool instances
7. `agent_configs` - Domain agent configurations
8. `agent_tools` - Many-to-many: agents ↔ tools

**Permissions**:
9. `tenant_agent_permissions` - Agent access per tenant
10. `tenant_tool_permissions` - Tool access per tenant

**Conversations**:
11. `sessions` - Conversation sessions
12. `messages` - Chat messages
13. `checkpoints` - LangGraph state persistence

---

## Common Use Cases

### 1. Query Customer Debt
**User**: "What is the debt for customer MST 0123456789?"
**Flow**: SupervisorAgent → AgentDebt → get_customer_debt tool → External API
**Result**: Structured debt information with formatting

### 2. Add New Agent (No Code)
**Admin**: Create AgentInventory via admin API
**Flow**: POST /api/admin/agents → Database insert → Cache reload
**Result**: New agent immediately available to authorized tenants

### 3. Multi-Tenant Isolation
**Scenario**: TenantA and TenantB use different LLM models
**Flow**: Each tenant's requests use their own API keys and configs
**Result**: Complete data and cost isolation

### 4. RAG Knowledge Query
**User**: "What is our return policy?"
**Flow**: SupervisorAgent → AgentAnalysis → RAGTool → ChromaDB
**Result**: AI-synthesized answer with source citations

---

## Quick Links

### External Resources
- [LangChain 0.3+ Documentation](https://python.langchain.com/docs/introduction/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/docs/)

### Project Files
- [Backend README](../backend/README.md)
- [Project Specification](../specs/001-agenthub-chatbot-framework/spec.md)
- [Implementation Plan](../specs/001-agenthub-chatbot-framework/plan.md)
- [Data Model](../specs/001-agenthub-chatbot-framework/data-model.md)

---

## Getting Help

### For Developers
1. Start with [Quick Start Guide](13_QUICKSTART.md)
2. Read [System Architecture](02_SYSTEM_ARCHITECTURE.md)
3. Check [Troubleshooting & FAQ](14_TROUBLESHOOTING_FAQ.md)
4. Review code examples in relevant guides

### For Administrators
1. Review [Tenant Onboarding Guide](03_TENANT_ONBOARDING_GUIDE.md)
2. Understand [Security Guide](08_SECURITY_GUIDE.md)
3. Follow [Deployment Guide](07_DEPLOYMENT_GUIDE.md)
4. Use [Operations Guide](11_OPERATIONS_GUIDE.md) for maintenance

### For API Consumers
1. Study [API Reference](05_API_REFERENCE.md)
2. Review authentication in [Security Guide](08_SECURITY_GUIDE.md)
3. Check [Troubleshooting & FAQ](14_TROUBLESHOOTING_FAQ.md) for errors

---

## Document Conventions

### Code Examples
All code examples use syntax highlighting:
```python
# Python example
from fastapi import FastAPI
app = FastAPI()
```

```bash
# Bash example
cd backend && source venv/Scripts/activate
```

### File Paths
- Absolute Windows paths: `c:\Users\gensh\Downloads\ITL_Base_28.10\backend\`
- Relative paths from project root: `backend/src/main.py`

### Links
- Internal links: `[System Architecture](02_SYSTEM_ARCHITECTURE.md)`
- External links: `[FastAPI](https://fastapi.tiangolo.com/)`
- Code references: `backend/src/services/supervisor_agent.py:123`

### Status Indicators
- ✅ Complete / Working
- ⏳ In Progress
- ❌ Missing / Needs Attention
- ⚠️ Warning / Important Note

---

## Contributing to Documentation

### Standards
- Use Markdown with GitHub-flavored extensions
- Include practical code examples
- Add diagrams where helpful (ASCII art or Mermaid)
- Cross-reference related documents
- Keep tone professional and clear

### Structure
- Start with purpose and audience
- Provide table of contents for long documents
- Use consistent heading hierarchy (H1 → H6)
- Include examples after concepts
- End with troubleshooting or next steps

---

## License

MIT License - See project LICENSE file

---

## Contact

For questions or issues related to this documentation:
- Review [Troubleshooting & FAQ](14_TROUBLESHOOTING_FAQ.md)
- Check existing project documentation
- Contact the development team

---

**Happy Building!** 🚀
