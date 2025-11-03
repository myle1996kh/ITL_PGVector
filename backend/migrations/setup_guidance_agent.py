"""
Setup script for AgentGuidance and RAG tool configuration.
This script sets up:
1. RAG BaseTool (if not exists)
2. RAG ToolConfig for Guidance
3. AgentGuidance with database
4. TenantAgentPermission for target tenant
"""
import sys
import uuid
from sqlalchemy.orm import Session
from src.config import SessionLocal
# Import all models to ensure proper initialization
from src.models.tenant import Tenant
from src.models.base_tool import BaseTool
from src.models.tool import ToolConfig
from src.models.agent import AgentConfig, AgentTools
from src.models.llm_model import LLMModel
from src.models.tenant_llm_config import TenantLLMConfig
from src.models.permissions import TenantAgentPermission, TenantToolPermission
from src.models.output_format import OutputFormat
from src.models.session import ChatSession
from src.models.message import Message
from src.utils.logging import get_logger

logger = get_logger(__name__)

TARGET_TENANT_ID = "2628802d-1dff-4a98-9325-704433c5d3ab"


def setup_rag_base_tool(db: Session) -> str:
    """Setup RAG BaseTool if not exists. Returns base_tool_id."""
    rag_base = db.query(BaseTool).filter(BaseTool.type == "RAG").first()

    if rag_base:
        logger.info("RAG BaseTool already exists", base_tool_id=rag_base.base_tool_id)
        return str(rag_base.base_tool_id)

    base_tool_id = uuid.uuid4()
    rag_base = BaseTool(
        base_tool_id=base_tool_id,
        type="RAG",
        handler_class="tools.rag.RAGTool",
        description="Retrieval-Augmented Generation tool for knowledge base queries",
        default_config_schema={
            "collection_name": {"type": "string", "description": "ChromaDB collection name"},
            "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
            "chromadb_host": {"type": "string", "default": "localhost"},
            "chromadb_port": {"type": "integer", "default": 8001},
        }
    )
    db.add(rag_base)
    db.commit()
    logger.info("RAG BaseTool created", base_tool_id=base_tool_id)
    return str(base_tool_id)


def setup_rag_tool_config(db: Session, base_tool_id: str) -> str:
    """Setup RAG ToolConfig for Guidance. Returns tool_id."""
    rag_tool = db.query(ToolConfig).filter(
        ToolConfig.name == "guidance_rag_retrieval"
    ).first()

    if rag_tool:
        logger.info("RAG ToolConfig already exists", tool_id=rag_tool.tool_id)
        return str(rag_tool.tool_id)

    tool_id = uuid.uuid4()
    rag_tool = ToolConfig(
        tool_id=tool_id,
        name="guidance_rag_retrieval",
        base_tool_id=uuid.UUID(base_tool_id),
        config={
            "collection_name": "guidance_knowledge_base",
            "top_k": 5,
            "chromadb_host": "localhost",
            "chromadb_port": 8001,
        },
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for the knowledge base"
                }
            },
            "required": ["query"]
        },
        description="Retrieve guidance documents from knowledge base",
        is_active=True
    )
    db.add(rag_tool)
    db.commit()
    logger.info("RAG ToolConfig created", tool_id=tool_id)
    return str(tool_id)


def setup_agent_guidance(db: Session, llm_model_id: str) -> str:
    """Setup AgentGuidance. Returns agent_id."""
    agent = db.query(AgentConfig).filter(
        AgentConfig.name == "AgentGuidance"
    ).first()

    if agent:
        logger.info("AgentGuidance already exists", agent_id=agent.agent_id)
        return str(agent.agent_id)

    agent_id = uuid.uuid4()
    agent = AgentConfig(
        agent_id=agent_id,
        name="AgentGuidance",
        prompt_template="""You are a Guidance Assistant that helps users with company policies, procedures, and guidelines.

You have access to a comprehensive knowledge base of company guidance documents.
When answering questions:
1. Search the knowledge base using the RAG retrieval tool
2. Provide clear, accurate answers based on retrieved documents
3. Always cite the source document in your response
4. If no relevant guidance is found, clearly state this and offer to escalate
5. Be helpful and professional in your tone
6. Respond in the user's language""",
        llm_model_id=uuid.UUID(llm_model_id),
        description="Guidance assistant for company policies and procedures",
        is_active=True
    )
    db.add(agent)
    db.commit()
    logger.info("AgentGuidance created", agent_id=agent_id)
    return str(agent_id)


def link_tool_to_agent(db: Session, agent_id: str, tool_id: str, priority: int = 1):
    """Link RAG tool to AgentGuidance."""
    link = db.query(AgentTools).filter(
        AgentTools.agent_id == uuid.UUID(agent_id),
        AgentTools.tool_id == uuid.UUID(tool_id)
    ).first()

    if link:
        logger.info("Tool already linked to agent", agent_id=agent_id, tool_id=tool_id)
        return

    link = AgentTools(
        agent_id=uuid.UUID(agent_id),
        tool_id=uuid.UUID(tool_id),
        priority=priority
    )
    db.add(link)
    db.commit()
    logger.info("Tool linked to agent", agent_id=agent_id, tool_id=tool_id)


def grant_tenant_permission(db: Session, tenant_id: str, agent_id: str):
    """Grant tenant permission to use AgentGuidance."""
    perm = db.query(TenantAgentPermission).filter(
        TenantAgentPermission.tenant_id == uuid.UUID(tenant_id),
        TenantAgentPermission.agent_id == uuid.UUID(agent_id)
    ).first()

    if perm:
        if perm.enabled:
            logger.info("Tenant already has permission", tenant_id=tenant_id, agent_id=agent_id)
            return
        else:
            perm.enabled = True
            db.commit()
            logger.info("Tenant permission enabled", tenant_id=tenant_id, agent_id=agent_id)
            return

    perm = TenantAgentPermission(
        tenant_id=uuid.UUID(tenant_id),
        agent_id=uuid.UUID(agent_id),
        enabled=True
    )
    db.add(perm)
    db.commit()
    logger.info("Tenant permission granted", tenant_id=tenant_id, agent_id=agent_id)


def grant_tool_permission(db: Session, tenant_id: str, tool_id: str):
    """Grant tenant permission to use RAG tool."""
    perm = db.query(TenantToolPermission).filter(
        TenantToolPermission.tenant_id == uuid.UUID(tenant_id),
        TenantToolPermission.tool_id == uuid.UUID(tool_id)
    ).first()

    if perm:
        if perm.enabled:
            logger.info("Tenant already has tool permission", tenant_id=tenant_id, tool_id=tool_id)
            return
        else:
            perm.enabled = True
            db.commit()
            logger.info("Tool permission enabled", tenant_id=tenant_id, tool_id=tool_id)
            return

    perm = TenantToolPermission(
        tenant_id=uuid.UUID(tenant_id),
        tool_id=uuid.UUID(tool_id),
        enabled=True
    )
    db.add(perm)
    db.commit()
    logger.info("Tool permission granted", tenant_id=tenant_id, tool_id=tool_id)


def main():
    """Run setup."""
    db = SessionLocal()

    try:
        # Get first available LLM model
        llm_model = db.query(LLMModel).filter(LLMModel.is_active == True).first()
        if not llm_model:
            logger.error("No active LLM model found")
            sys.exit(1)

        logger.info("Using LLM model", llm_model_id=llm_model.llm_model_id)

        # Setup RAG
        base_tool_id = setup_rag_base_tool(db)
        tool_id = setup_rag_tool_config(db, base_tool_id)

        # Setup Agent
        agent_id = setup_agent_guidance(db, str(llm_model.llm_model_id))

        # Link tool to agent
        link_tool_to_agent(db, agent_id, tool_id)

        # Grant permissions
        grant_tenant_permission(db, TARGET_TENANT_ID, agent_id)
        grant_tool_permission(db, TARGET_TENANT_ID, tool_id)

        logger.info(
            "Setup complete!",
            agent_id=agent_id,
            tool_id=tool_id,
            base_tool_id=base_tool_id,
            tenant_id=TARGET_TENANT_ID
        )

        print("\n✅ Setup Complete!")
        print(f"Agent ID: {agent_id}")
        print(f"Tool ID: {tool_id}")
        print(f"Tenant ID: {TARGET_TENANT_ID}")
        print("\nYou can now:")
        print("1. Send message to /test/chat with intent for 'AgentGuidance'")
        print("2. RAG tool will automatically be loaded and used")
        print("3. SupervisorAgent will auto-detect and route to AgentGuidance")
        print("4. Responses will be in user's language (EN/VI)")

    except Exception as e:
        logger.error("Setup failed", error=str(e))
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
