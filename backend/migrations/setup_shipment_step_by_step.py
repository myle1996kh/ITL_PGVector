"""
Step-by-step setup for AgentShipment.
Assumes HTTP_GET BaseTool already exists.

Steps:
1. Seed shipment tool config
2. Add AgentShipment agent
3. Link tool to agent
4. Grant tenant permissions
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
from src.models.output_format import OutputFormat
from src.models.permissions import TenantAgentPermission, TenantToolPermission
from src.models.session import ChatSession
from src.models.message import Message
from src.utils.logging import get_logger

logger = get_logger(__name__)

TARGET_TENANT_ID = "2628802d-1dff-4a98-9325-704433c5d3ab"


def step1_get_http_base_tool(db: Session) -> str:
    """STEP 1: Get existing HTTP_GET BaseTool. Returns base_tool_id."""
    print("\n" + "="*80)
    print("STEP 1: Get HTTP_GET BaseTool")
    print("="*80)

    http_base = db.query(BaseTool).filter(BaseTool.type == "HTTP_GET").first()

    if not http_base:
        print("❌ ERROR: HTTP_GET BaseTool not found!")
        print("Please create HTTP_GET BaseTool first")
        sys.exit(1)

    base_tool_id = str(http_base.base_tool_id)
    print(f"✅ Found HTTP_GET BaseTool: {base_tool_id}")
    return base_tool_id


def step2_seed_shipment_tool(db: Session, base_tool_id: str) -> str:
    """STEP 2: Seed shipment tool config. Returns tool_id."""
    print("\n" + "="*80)
    print("STEP 2: Seed Shipment Tool Config")
    print("="*80)

    # Check if already exists
    existing = db.query(ToolConfig).filter(
        ToolConfig.name == "get_shipment_tracking"
    ).first()

    if existing:
        print(f"⚠️  Shipment tool already exists: {existing.tool_id}")
        print(f"   Skipping creation...")
        return str(existing.tool_id)

    tool_id = uuid.uuid4()
    shipment_tool = ToolConfig(
        tool_id=tool_id,
        name="get_shipment_tracking",
        base_tool_id=uuid.UUID(base_tool_id),
        config={
            "base_url": "https://api.shipment.example.com",
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

    print(f"✅ Created Shipment ToolConfig:")
    print(f"   Tool ID: {tool_id}")
    print(f"   Name: get_shipment_tracking")
    print(f"   Base URL: https://api.shipment.example.com")
    print(f"   Endpoint: /v1/shipment/{{shipment_id}}")

    return str(tool_id)


def step3_add_agent_shipment(db: Session, llm_model_id: str) -> str:
    """STEP 3: Add AgentShipment. Returns agent_id."""
    print("\n" + "="*80)
    print("STEP 3: Add AgentShipment Agent")
    print("="*80)

    # Check if already exists
    existing = db.query(AgentConfig).filter(
        AgentConfig.name == "AgentShipment"
    ).first()

    if existing:
        print(f"⚠️  AgentShipment already exists: {existing.agent_id}")
        print(f"   Skipping creation...")
        return str(existing.agent_id)

    agent_id = uuid.uuid4()
    agent = AgentConfig(
        agent_id=agent_id,
        name="AgentShipment",
        handler_class="services.domain_agents.DomainAgent",
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

    print(f"✅ Created AgentShipment:")
    print(f"   Agent ID: {agent_id}")
    print(f"   Name: AgentShipment")
    print(f"   Handler Class: services.domain_agents.DomainAgent")
    print(f"   LLM Model: {llm_model_id}")

    return str(agent_id)


def step4_link_tool_to_agent(db: Session, agent_id: str, tool_id: str) -> None:
    """STEP 4: Link tool to agent."""
    print("\n" + "="*80)
    print("STEP 4: Link Shipment Tool to AgentShipment")
    print("="*80)

    # Check if already linked
    existing = db.query(AgentTools).filter(
        AgentTools.agent_id == uuid.UUID(agent_id),
        AgentTools.tool_id == uuid.UUID(tool_id)
    ).first()

    if existing:
        print(f"⚠️  Tool already linked to agent")
        print(f"   Skipping link...")
        return

    link = AgentTools(
        agent_id=uuid.UUID(agent_id),
        tool_id=uuid.UUID(tool_id),
        priority=1
    )
    db.add(link)
    db.commit()

    print(f"✅ Linked tool to agent:")
    print(f"   Agent ID: {agent_id}")
    print(f"   Tool ID: {tool_id}")
    print(f"   Priority: 1")


def step5_grant_agent_permission(db: Session, tenant_id: str, agent_id: str) -> None:
    """STEP 5: Grant tenant permission for agent."""
    print("\n" + "="*80)
    print("STEP 5: Grant Tenant Permission for AgentShipment")
    print("="*80)

    # Check if already exists
    existing = db.query(TenantAgentPermission).filter(
        TenantAgentPermission.tenant_id == uuid.UUID(tenant_id),
        TenantAgentPermission.agent_id == uuid.UUID(agent_id)
    ).first()

    if existing:
        if existing.enabled:
            print(f"✅ Tenant already has permission for agent (enabled)")
            print(f"   Tenant: {tenant_id}")
            return
        else:
            print(f"⚠️  Permission exists but disabled. Enabling...")
            existing.enabled = True
            db.commit()
            print(f"✅ Permission enabled!")
            return

    perm = TenantAgentPermission(
        tenant_id=uuid.UUID(tenant_id),
        agent_id=uuid.UUID(agent_id),
        enabled=True
    )
    db.add(perm)
    db.commit()

    print(f"✅ Granted tenant permission for agent:")
    print(f"   Tenant: {tenant_id}")
    print(f"   Agent: {agent_id}")
    print(f"   Enabled: True")


def step6_grant_tool_permission(db: Session, tenant_id: str, tool_id: str) -> None:
    """STEP 6: Grant tenant permission for tool."""
    print("\n" + "="*80)
    print("STEP 6: Grant Tenant Permission for Shipment Tool")
    print("="*80)

    # Check if already exists
    existing = db.query(TenantToolPermission).filter(
        TenantToolPermission.tenant_id == uuid.UUID(tenant_id),
        TenantToolPermission.tool_id == uuid.UUID(tool_id)
    ).first()

    if existing:
        if existing.enabled:
            print(f"✅ Tenant already has permission for tool (enabled)")
            print(f"   Tenant: {tenant_id}")
            return
        else:
            print(f"⚠️  Permission exists but disabled. Enabling...")
            existing.enabled = True
            db.commit()
            print(f"✅ Permission enabled!")
            return

    perm = TenantToolPermission(
        tenant_id=uuid.UUID(tenant_id),
        tool_id=uuid.UUID(tool_id),
        enabled=True
    )
    db.add(perm)
    db.commit()

    print(f"✅ Granted tenant permission for tool:")
    print(f"   Tenant: {tenant_id}")
    print(f"   Tool: {tool_id}")
    print(f"   Enabled: True")


def main():
    """Run all steps."""
    db = SessionLocal()

    try:
        # Get LLM model
        llm_model = db.query(LLMModel).filter(LLMModel.is_active == True).first()
        if not llm_model:
            print("❌ ERROR: No active LLM model found")
            sys.exit(1)

        print("\n" + "="*80)
        print("AGENTSHIPMENT STEP-BY-STEP SETUP")
        print("="*80)
        print(f"Target Tenant: {TARGET_TENANT_ID}")
        print(f"Active LLM: {llm_model.llm_model_id}")

        # Step 1: Get HTTP base tool
        base_tool_id = step1_get_http_base_tool(db)

        # Step 2: Seed tool
        tool_id = step2_seed_shipment_tool(db, base_tool_id)

        # Step 3: Add agent
        agent_id = step3_add_agent_shipment(db, str(llm_model.llm_model_id))

        # Step 4: Link tool to agent
        step4_link_tool_to_agent(db, agent_id, tool_id)

        # Step 5: Grant agent permission
        step5_grant_agent_permission(db, TARGET_TENANT_ID, agent_id)

        # Step 6: Grant tool permission
        step6_grant_tool_permission(db, TARGET_TENANT_ID, tool_id)

        # Summary
        print("\n" + "="*80)
        print("✅ ALL STEPS COMPLETE!")
        print("="*80)
        print(f"\nConfiguration Summary:")
        print(f"  Base Tool ID:  {base_tool_id}")
        print(f"  Tool ID:       {tool_id}")
        print(f"  Agent ID:      {agent_id}")
        print(f"  Tenant ID:     {TARGET_TENANT_ID}")
        print(f"\nYou can now:")
        print(f"  1. Send message to /test/chat with shipment tracking request")
        print(f"  2. Example: 'What is the status of shipment VSG1234567890FM?'")
        print(f"  3. SupervisorAgent will auto-route to AgentShipment")
        print(f"  4. AgentShipment will use shipment tracking tool")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
