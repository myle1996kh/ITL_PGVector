"""Seed tenant_agent_permissions for test tenant."""
import asyncio
import uuid
from sqlalchemy.orm import Session
from src.config import SessionLocal

# Import ALL models to ensure SQLAlchemy relationships are properly registered
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

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Test tenant ID from seed_test_data.py
TENANT_ID = "2628802d-1dff-4a98-9325-704433c5d3ab"


def seed_tenant_agent_permissions():
    """Seed tenant_agent_permissions to enable AgentDebt for test tenant."""
    db = SessionLocal()

    try:
        # Find AgentDebt by name
        agent_debt = db.query(AgentConfig).filter(
            AgentConfig.name == "AgentDebt"
        ).first()

        if not agent_debt:
            logger.error("agent_not_found", agent_name="AgentDebt")
            print("❌ AgentDebt not found. Please run seed_test_data.py first.")
            return

        logger.info(
            "agent_found",
            agent_id=str(agent_debt.agent_id),
            agent_name=agent_debt.name
        )
        print(f"✅ Found AgentDebt: {agent_debt.agent_id}")

        # Check if permission already exists
        existing_permission = db.query(TenantAgentPermission).filter(
            TenantAgentPermission.tenant_id == uuid.UUID(TENANT_ID),
            TenantAgentPermission.agent_id == agent_debt.agent_id
        ).first()

        if existing_permission:
            logger.warning(
                "permission_already_exists",
                tenant_id=TENANT_ID,
                agent_id=str(agent_debt.agent_id)
            )
            print(f"⚠️  Permission already exists for tenant {TENANT_ID}")
            print(f"   Status: {'enabled' if existing_permission.enabled else 'disabled'}")

            # Update to enabled if it's disabled
            if not existing_permission.enabled:
                existing_permission.enabled = True
                db.commit()
                logger.info("permission_enabled", permission_id=str(existing_permission.permission_id))
                print("✅ Permission updated to enabled")
            return

        # Create new tenant_agent_permission
        permission_id = uuid.uuid4()
        tenant_agent_permission = TenantAgentPermission(
            permission_id=permission_id,
            tenant_id=uuid.UUID(TENANT_ID),
            agent_id=agent_debt.agent_id,
            enabled=True
        )

        db.add(tenant_agent_permission)
        db.commit()

        logger.info(
            "permission_created",
            permission_id=str(permission_id),
            tenant_id=TENANT_ID,
            agent_id=str(agent_debt.agent_id)
        )

        print("\n" + "="*60)
        print("✅ Tenant Agent Permission Created Successfully!")
        print("="*60)
        print(f"Permission ID: {permission_id}")
        print(f"Tenant ID:     {TENANT_ID}")
        print(f"Agent ID:      {agent_debt.agent_id}")
        print(f"Agent Name:    {agent_debt.name}")
        print(f"Enabled:       True")
        print("="*60)
        print("\n🚀 Test tenant can now use AgentDebt for chat sessions!")
        print("\nNext steps:")
        print("1. Ensure server is running: uvicorn src.main:app --reload")
        print("2. Set DISABLE_AUTH=true in .env for testing")
        print("3. Add your UAT bearer token to TEST_BEARER_TOKEN in .env")
        print("4. Test with: python test_chat_api.py")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("seed_failed", error=str(e))
        print(f"❌ Failed to seed tenant_agent_permissions: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_tenant_agent_permissions()
