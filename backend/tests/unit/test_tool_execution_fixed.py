"""Debug script to test tool execution step by step - FIXED VERSION."""
import asyncio
import sys
sys.path.insert(0, ".")

# Import all models FIRST to register relationships
from src.models.base import Base
from src.models.tenant import Tenant
from src.models.session import ChatSession
from src.models.message import Message
from src.models.llm_model import LLMModel
from src.models.tenant_llm_config import TenantLLMConfig
from src.models.base_tool import BaseTool
from src.models.tool import ToolConfig
from src.models.agent import AgentConfig, AgentTools
from src.models.permissions import TenantAgentPermission, TenantToolPermission
from src.models.output_format import OutputFormat

from src.config import get_db
from src.services.domain_agents import AgentFactory
from src.config import settings
import json


async def test_tool_execution():
    """Test tool execution with detailed logging."""
    db = next(get_db())
    tenant_id = "2628802d-1dff-4a98-9325-704433c5d3ab"
    agent_name = "AgentDebt"

    print("="*100)
    print("TOOL EXECUTION DIAGNOSTIC TEST")
    print("="*100)
    print()

    # Check settings
    print("[1] CHECK ENVIRONMENT SETTINGS")
    print(f"    DISABLE_AUTH: {settings.DISABLE_AUTH}")
    print(f"    TEST_BEARER_TOKEN: {'Set' if settings.TEST_BEARER_TOKEN else 'NOT SET'}")
    print(f"    Token length: {len(settings.TEST_BEARER_TOKEN) if settings.TEST_BEARER_TOKEN else 0}")
    if settings.TEST_BEARER_TOKEN:
        # Try to check token expiration
        try:
            import base64
            parts = settings.TEST_BEARER_TOKEN.split('.')
            if len(parts) == 3:
                payload = parts[1]
                # Add padding if needed
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                decoded = base64.urlsafe_b64decode(payload)
                import json
                token_data = json.loads(decoded)
                from datetime import datetime
                exp_timestamp = token_data.get('exp')
                if exp_timestamp:
                    exp_date = datetime.fromtimestamp(exp_timestamp)
                    now = datetime.now()
                    if exp_date < now:
                        print(f"    ⚠️  TOKEN EXPIRED on {exp_date}")
                    else:
                        days_left = (exp_date - now).days
                        print(f"    ✓ Token valid until {exp_date} ({days_left} days)")
        except Exception as e:
            print(f"    (Could not decode token: {e})")
    print()

    # Create agent
    print("[2] CREATE AGENT")
    try:
        agent = await AgentFactory.create_agent(
            db=db,
            agent_name=agent_name,
            tenant_id=tenant_id,
            jwt_token=""
        )
        print(f"    ✓ Agent created: {agent_name}")
    except Exception as e:
        print(f"    ✗ Error creating agent: {e}")
        import traceback
        traceback.print_exc()
        return

    # Check tools
    print()
    print("[3] CHECK AVAILABLE TOOLS")
    print(f"    Total tools: {len(agent.tools)}")
    for i, tool in enumerate(agent.tools, 1):
        print(f"    Tool {i}: {tool.name}")
        print(f"      Description: {tool.description[:80]}...")
        print(f"      Args: {tool.args}")
        print()

    # Test message that should call tool
    test_message = "Show debt for tax code 0104985841"

    print("[4] TEST ENTITY EXTRACTION")
    print(f"    Message: {test_message}")
    intent, entities = await agent._extract_intent_and_entities(test_message)
    print(f"    Detected Intent: {intent}")
    print(f"    Extracted Entities: {entities}")
    print()

    # Test full invoke
    print("[5] TEST FULL AGENT INVOCATION")
    print(f"    Message: {test_message}")
    print()

    try:
        response = await agent.invoke(test_message)

        print(f"    Status: {response.get('status')}")
        print(f"    Agent: {response.get('agent')}")
        print(f"    Intent: {response.get('intent')}")
        print()

        # Check metadata
        metadata = response.get('metadata', {})

        print("[6] CHECK TOOL CALLS IN METADATA")
        tool_calls = metadata.get('tool_calls', [])
        print(f"    Tool calls count: {len(tool_calls)}")

        if tool_calls:
            print("    ✓ Tools were called!")
            for i, call in enumerate(tool_calls, 1):
                print(f"    Tool {i}:")
                print(f"      Name: {call.get('tool_name')}")
                print(f"      Args: {call.get('tool_args')}")
                print(f"      ID: {call.get('tool_id')}")
        else:
            print("    ✗ NO TOOLS CALLED - Debug points:")
            print("      1. Is agent prompt instructing to use tools?")
            print("      2. Are tools properly bound to LLM?")
            print("      3. Did LLM understand the query?")
        print()

        print("[7] CHECK RESPONSE DATA")
        response_data = response.get('response', {})
        if isinstance(response_data, dict):
            print(f"    Response keys: {list(response_data.keys())}")
            print(f"    Response data (first 500 chars):")
            print(f"    {json.dumps(response_data, indent=6)[:500]}...")
        else:
            print(f"    Response type: {type(response_data)}")
            print(f"    Response: {str(response_data)[:200]}...")
        print()

        print("[8] TOOL EXECUTION RESULT CHECK")
        if tool_calls:
            tool_result = response.get('data', {})
            if tool_result:
                print(f"    ✓ Tool returned data")
                print(f"    Data keys: {list(tool_result.keys()) if isinstance(tool_result, dict) else 'N/A'}")
            else:
                print(f"    ⚠️  Tool called but no response data")
                print(f"    Possible reasons:")
                print(f"      - API returned empty response")
                print(f"      - Tax code not found in database")
                print(f"      - Bearer token expired or invalid")
                print(f"      - API endpoint returned error")
        print()

        print("[9] DEBUGGING TIPS")
        print("    If tool not called:")
        print("      → Check agent prompt template in database")
        print("      → Ensure prompt mentions available tools")
        print("      → Verify LLM is instructed to USE TOOLS")
        print()
        print("    If tool called but no response:")
        print("      → Check API endpoint is reachable")
        print("      → Check bearer token is valid/not expired")
        print("      → Check tax_code exists in API database")
        print("      → Monitor logs for 'http_get_error' or API response")
        print()
        print("    Next steps:")
        print("      1. Check FastAPI server logs for HTTP errors")
        print("      2. Test API endpoint manually with curl:")
        print("      3. Verify TEST_BEARER_TOKEN in .env is not expired")
        print("      4. Try different tax_code if available")
        print()
        print("    Manual API test command:")
        print("      curl -X GET \\")
        print('        "https://uat-accounting-api-efms.logtechub.com/api/v1/vi/AccountReceivable/GetReceivableByTaxCode/0104985841" \\')
        print(f'        -H "Authorization: Bearer YOUR_TOKEN" \\')
        print('        -H "Content-Type: application/json"')
        print()

    except Exception as e:
        print(f"    ✗ Error during invocation: {e}")
        import traceback
        traceback.print_exc()

    print("="*100)


if __name__ == "__main__":
    asyncio.run(test_tool_execution())
