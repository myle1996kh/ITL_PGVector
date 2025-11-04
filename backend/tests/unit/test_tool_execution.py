"""Debug script to test tool execution step by step."""
import asyncio
import sys
sys.path.insert(0, ".")

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
            print(f"    Response data:")
            print(f"    {json.dumps(response_data, indent=6)[:500]}...")
        else:
            print(f"    Response: {str(response_data)[:200]}...")
        print()

        print("[8] COMMON ISSUES CHECKLIST")
        issues = []

        if not tool_calls:
            issues.append("- No tools were called by the LLM")

        if not metadata.get('extracted_entities'):
            issues.append("- No entities were extracted")

        if not response_data or (isinstance(response_data, dict) and not response_data.get('response')):
            issues.append("- Response is empty or missing data")

        if issues:
            print("    Found issues:")
            for issue in issues:
                print(f"    {issue}")
        else:
            print("    ✓ All checks passed")
        print()

        print("[9] DEBUGGING TIPS")
        print("    If tool not called:")
        print("      → Check agent prompt template in database")
        print("      → Ensure prompt mentions available tools")
        print("      → Verify LLM is instructed to USE TOOLS")
        print()
        print("    If tool called but no response:")
        print("      → Check API endpoint URL is correct")
        print("      → Check bearer token is valid/not expired")
        print("      → Check query parameter (tax_code) is valid")
        print("      → Monitor logs for HTTP errors")
        print()
        print("    Next steps:")
        print("      1. Restart FastAPI server to reload settings")
        print("      2. Check server logs for 'http_get_error' or 'http_using_test_token'")
        print("      3. Test API endpoint manually with bearer token")
        print("      4. Verify TEST_BEARER_TOKEN in .env is not expired")
        print()

    except Exception as e:
        print(f"    ✗ Error during invocation: {e}")
        import traceback
        traceback.print_exc()

    print("="*100)


if __name__ == "__main__":
    asyncio.run(test_tool_execution())
