"""Test dynamic agent loading in SupervisorAgent."""
# Import models first to ensure proper initialization
from src.models.tenant import Tenant
from src.models.agent import AgentConfig, AgentTools
from src.models.permissions import TenantAgentPermission
from src.models.session import ChatSession
from src.models.message import Message
from src.models.llm_model import LLMModel
from src.models.tenant_llm_config import TenantLLMConfig
from src.models.base_tool import BaseTool
from src.models.tool import ToolConfig
from src.models.output_format import OutputFormat

from src.config import SessionLocal
from src.services.supervisor_agent import SupervisorAgent

db = SessionLocal()
tenant_id = '2628802d-1dff-4a98-9325-704433c5d3ab'

try:
    supervisor = SupervisorAgent(db, tenant_id, '')

    print("✅ Available Agents for tenant:")
    for agent in supervisor.available_agents:
        print(f"   - {agent['name']}: {agent['description']}")

    print("\n✅ Generated Supervisor Prompt:")
    print("---")
    print(supervisor.supervisor_prompt)
    print("---")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
