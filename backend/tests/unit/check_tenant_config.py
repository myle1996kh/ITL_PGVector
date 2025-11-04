"""Check tenant configuration - LLM, agents, and tools."""
import uuid
from src.config import SessionLocal

# Import ALL models
from src.models.tenant import Tenant
from src.models.session import ChatSession
from src.models.message import Message
from src.models.llm_model import LLMModel
from src.models.tenant_llm_config import TenantLLMConfig
from src.models.base_tool import BaseTool
from src.models.output_format import OutputFormat
from src.models.tool import ToolConfig
from src.models.agent import AgentConfig, AgentTools
from src.models.permissions import TenantAgentPermission, TenantToolPermission

TENANT_ID = "2628802d-1dff-4a98-9325-704433c5d3ab"

def check_tenant_config():
    """Check if tenant has complete configuration."""
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print(f"CHECKING TENANT CONFIGURATION: {TENANT_ID}")
        print("="*80)

        # 1. Check tenant exists
        tenant = db.query(Tenant).filter(Tenant.tenant_id == uuid.UUID(TENANT_ID)).first()
        if not tenant:
            print("❌ Tenant not found!")
            return
        print(f"\n✅ Tenant found: {tenant.name}")
        print(f"   Domain: {tenant.domain}")
        print(f"   Status: {tenant.status}")

        # 2. Check LLM configuration
        tenant_llm_config = db.query(TenantLLMConfig).filter(
            TenantLLMConfig.tenant_id == uuid.UUID(TENANT_ID)
        ).first()

        if not tenant_llm_config:
            print("\n❌ NO LLM CONFIGURATION FOUND!")
            print("   Tenant needs LLM config to process chat messages")
            print("\n💡 Fix: Run seed script to create LLM config")
            return

        print(f"\n✅ LLM Configuration found")
        print(f"   LLM Model ID: {tenant_llm_config.llm_model_id}")
        print(f"   Has encrypted API key: {bool(tenant_llm_config.encrypted_api_key)}")

        # Get LLM model details
        llm_model = db.query(LLMModel).filter(
            LLMModel.llm_model_id == tenant_llm_config.llm_model_id
        ).first()

        if llm_model:
            print(f"   Provider: {llm_model.provider}")
            print(f"   Model: {llm_model.model_name}")
            print(f"   Active: {llm_model.is_active}")

        # 3. Check agent permissions
        agent_permissions = db.query(TenantAgentPermission).filter(
            TenantAgentPermission.tenant_id == uuid.UUID(TENANT_ID),
            TenantAgentPermission.enabled == True
        ).all()

        if not agent_permissions:
            print("\n❌ NO AGENT PERMISSIONS FOUND!")
            print("   Tenant has no agents enabled")
            return

        print(f"\n✅ Agent Permissions: {len(agent_permissions)} enabled")

        for perm in agent_permissions:
            agent = db.query(AgentConfig).filter(
                AgentConfig.agent_id == perm.agent_id
            ).first()

            if agent:
                print(f"\n   Agent: {agent.name}")
                print(f"   - ID: {agent.agent_id}")
                print(f"   - Active: {agent.is_active}")
                print(f"   - Description: {agent.description[:80]}...")

                # Get tools for this agent
                tools = db.query(ToolConfig).join(
                    AgentTools, ToolConfig.tool_id == AgentTools.tool_id
                ).filter(
                    AgentTools.agent_id == agent.agent_id
                ).all()

                print(f"   - Tools: {len(tools)}")
                for tool in tools:
                    print(f"      • {tool.name}: {tool.description}")

        # 4. Check tool permissions
        tool_permissions = db.query(TenantToolPermission).filter(
            TenantToolPermission.tenant_id == uuid.UUID(TENANT_ID),
            TenantToolPermission.enabled == True
        ).all()

        print(f"\n✅ Tool Permissions: {len(tool_permissions)} enabled")

        print("\n" + "="*80)
        print("✅ TENANT CONFIGURATION IS COMPLETE!")
        print("="*80)
        print("\nTenant is ready to process chat messages.\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_tenant_config()
