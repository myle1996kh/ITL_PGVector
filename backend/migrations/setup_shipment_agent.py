"""
Setup script for AgentShipment and Shipment HTTP tool.
This script sets up:
1. HTTP_GET BaseTool (if not exists)
2. Shipment ToolConfig for shipment tracking
3. AgentShipment with database
4. Link tool to agent
5. TenantAgentPermission and TenantToolPermission for target tenant
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


def setup_http_get_base_tool(db: Session) -> str:
    """Setup HTTP_GET BaseTool if not exists. Returns base_tool_id."""
    http_base = db.query(BaseTool).filter(BaseTool.type == "HTTP_GET").first()

    if http_base:
        logger.info("HTTP_GET BaseTool already exists", base_tool_id=http_base.base_tool_id)
        return str(http_base.base_tool_id)

    base_tool_id = uuid.uuid4()
    http_base = BaseTool(
        base_tool_id=base_tool_id,
        type="HTTP_GET",
        handler_class="tools.http.HTTPGetTool",
        description="HTTP GET request tool for external API calls",
        default_config_schema={
            "base_url": {"type": "string", "description": "Base URL for API"},
            "endpoint": {"type": "string", "description": "API endpoint path"},
            "headers": {"type": "object", "default": {}, "description": "HTTP headers"},
            "timeout": {"type": "integer", "default": 30, "minimum": 1, "maximum": 300},
        }
    )
    db.add(http_base)
    db.commit()
    logger.info("HTTP_GET BaseTool created", base_tool_id=base_tool_id)
    return str(base_tool_id)


def setup_shipment_tool_config(db: Session, base_tool_id: str) -> str:
    """Setup Shipment ToolConfig. Returns tool_id."""
    shipment_tool = db.query(ToolConfig).filter(
        ToolConfig.name == "get_shipment_tracking"
    ).first()

    if shipment_tool:
        logger.info("Shipment ToolConfig already exists", tool_id=shipment_tool.tool_id)
        return str(shipment_tool.tool_id)

    tool_id = uuid.uuid4()
    shipment_tool = ToolConfig(
        tool_id=tool_id,
        name="get_shipment_tracking",
        base_tool_id=uuid.UUID(base_tool_id),
        config={
            "base_url": "https://api.shipment.example.com",  # Dummy URL
            "endpoint": "/v1/shipment/{shipment_id}",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            "timeout": 30
        },
        input_schema={
            "type": "object",
            "properties": {
                "shipment_id": {
                    "type": "string",
                    "description": "Shipment ID in format VSG + 10 digits + FM (e.g., VSG1234567890FM)"
                }
            },
            "required": ["shipment_id"]
        },
        description="Get shipment tracking information and status by shipment ID",
        is_active=True
    )
    db.add(shipment_tool)
    db.commit()
    logger.info("Shipment ToolConfig created", tool_id=tool_id)
    return str(tool_id)


def setup_agent_shipment(db: Session, llm_model_id: str) -> str:
    """Setup AgentShipment. Returns agent_id."""
    agent = db.query(AgentConfig).filter(
        AgentConfig.name == "AgentShipment"
    ).first()

    if agent:
        logger.info("AgentShipment already exists", agent_id=agent.agent_id)
        return str(agent.agent_id)

    agent_id = uuid.uuid4()
    agent = AgentConfig(
        agent_id=agent_id,
        name="AgentShipment",
        handler_class="services.domain_agents.DomainAgent",  # Use generic DomainAgent
        prompt_template="""You are a Shipment Tracking Assistant that helps customers track and get information about their shipments.

When users ask about shipments:
1. Extract the shipment ID from their message (format: VSG + 10 digits + FM)
2. Use the shipment tracking tool to get real-time status
3. Provide clear information about shipment status, location, and delivery details
4. Be helpful and professional
5. Respond in the user's language (English or Vietnamese)

Example shipment IDs: VSG1234567890FM, VSG9876543210FM""",
        llm_model_id=uuid.UUID(llm_model_id),
        description="Shipment tracking agent for delivery status and information",
        is_active=True
    )
    db.add(agent)
    db.commit()
    logger.info("AgentShipment created", agent_id=agent_id)
    return str(agent_id)


def link_tool_to_agent(db: Session, agent_id: str, tool_id: str, priority: int = 1):
    """Link shipment tool to AgentShipment."""
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


def grant_tenant_agent_permission(db: Session, tenant_id: str, agent_id: str):
    """Grant tenant permission to use AgentShipment."""
    perm = db.query(TenantAgentPermission).filter(
        TenantAgentPermission.tenant_id == uuid.UUID(tenant_id),
        TenantAgentPermission.agent_id == uuid.UUID(agent_id)
    ).first()

    if perm:
        if perm.enabled:
            logger.info("Tenant already has agent permission", tenant_id=tenant_id, agent_id=agent_id)
            return
        else:
            perm.enabled = True
            db.commit()
            logger.info("Tenant agent permission enabled", tenant_id=tenant_id, agent_id=agent_id)
            return

    perm = TenantAgentPermission(
        tenant_id=uuid.UUID(tenant_id),
        agent_id=uuid.UUID(agent_id),
        enabled=True
    )
    db.add(perm)
    db.commit()
    logger.info("Tenant agent permission granted", tenant_id=tenant_id, agent_id=agent_id)


def grant_tenant_tool_permission(db: Session, tenant_id: str, tool_id: str):
    """Grant tenant permission to use shipment tracking tool."""
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

        # Setup HTTP GET base tool
        base_tool_id = setup_http_get_base_tool(db)

        # Setup shipment tool config
        tool_id = setup_shipment_tool_config(db, base_tool_id)

        # Setup AgentShipment
        agent_id = setup_agent_shipment(db, str(llm_model.llm_model_id))

        # Link tool to agent
        link_tool_to_agent(db, agent_id, tool_id)

        # Grant permissions
        grant_tenant_agent_permission(db, TARGET_TENANT_ID, agent_id)
        grant_tenant_tool_permission(db, TARGET_TENANT_ID, tool_id)

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
        print(f"Base Tool ID: {base_tool_id}")
        print(f"Tenant ID: {TARGET_TENANT_ID}")
        print("\nYou can now:")
        print("1. Send message to /test/chat with shipment tracking request")
        print("2. Example: 'What is the status of shipment VSG1234567890FM?'")
        print("3. Shipment tracking tool will automatically be loaded and used")
        print("4. SupervisorAgent will auto-detect and route to AgentShipment")
        print("5. Responses will be in user's language (EN/VI)")

    except Exception as e:
        logger.error("Setup failed", error=str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
