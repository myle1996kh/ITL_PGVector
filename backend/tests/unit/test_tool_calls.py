"""Test script for tool call execution in DomainAgent."""
import asyncio
import sys
sys.path.insert(0, "/path/to/backend")

from sqlalchemy.orm import Session
from src.config import get_db
from src.services.domain_agents import AgentFactory


async def test_tool_calls():
    """Test whether domain agent calls tools with extracted entities."""
    db = next(get_db())
    tenant_id = "2628802d-1dff-4a98-9325-704433c5d3ab"
    agent_name = "AgentDebt"

    try:
        agent = await AgentFactory.create_agent(
            db=db,
            agent_name=agent_name,
            tenant_id=tenant_id,
            jwt_token=""
        )
    except ValueError as e:
        print(f"Error creating agent: {e}")
        return

    print("="*100)
    print("TOOL CALL TEST")
    print(f"Agent: {agent_name}")
    print("="*100)
    print()

    # Check available tools
    print("[INFO] AVAILABLE TOOLS")
    print(f"Total tools: {len(agent.tools)}")
    for tool in agent.tools:
        print(f"  - {tool.name}")
        print(f"    Description: {tool.description}")
        print(f"    Input Schema: {tool.args}")
        print()

    test_messages = [
        {
            "message": "Show debt for tax code 0123456789012",
            "should_call_tool": True,
            "expected_tool": None  # Any tool that extracts debt info
        },
        {
            "message": "What's customer debt?",
            "should_call_tool": False,  # Too vague
            "expected_tool": None
        },
        {
            "message": "Get balance for account 0123456789012",
            "should_call_tool": True,
            "expected_tool": None
        },
    ]

    print("[TEST] TOOL CALL EXECUTION")
    print()

    for i, test_case in enumerate(test_messages, 1):
        message = test_case["message"]
        should_call = test_case["should_call_tool"]

        print(f"Test Case {i}")
        print(f"Message: {message}")
        print(f"Should Call Tool: {should_call}")

        try:
            response = await agent.invoke(message)

            metadata = response.get('metadata', {})
            tool_calls = metadata.get('tool_calls', [])
            extracted_entities = metadata.get('extracted_entities', {})
            intent = metadata.get('intent', 'unknown')

            print(f"Detected Intent: {intent}")
            print(f"Extracted Entities: {extracted_entities}")
            print(f"Tools Called: {len(tool_calls)}")

            if tool_calls:
                for j, tool_call in enumerate(tool_calls, 1):
                    print(f"  Tool {j}: {tool_call.get('tool_name')}")
                    print(f"    Args: {tool_call.get('tool_args')}")
            else:
                print("  (No tools called)")

            # Verify expectation
            has_tool_call = len(tool_calls) > 0
            if should_call == has_tool_call:
                print("✓ PASS - Tool call matches expectation")
            else:
                print(f"✗ FAIL - Expected tool call: {should_call}, Got: {has_tool_call}")

        except Exception as e:
            print(f"✗ Error during invocation: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("="*100)
    print("\n[DEBUGGING TIPS]")
    print("1. Check if tools are loaded:")
    print(f"   Tools available: {len(agent.tools)}")
    print()
    print("2. Check agent prompt to ensure it's instructed to use tools:")
    print(f"   Agent Config: {agent.agent_config.name}")
    print(f"   Prompt Template starts with: {agent.agent_config.prompt_template[:100]}...")
    print()
    print("3. Check tool configuration in database:")
    print("""
    SELECT at.agent_id, at.tool_id, tc.name, tc.description, at.priority
    FROM agent_tools at
    JOIN tool_configs tc ON at.tool_id = tc.tool_id
    WHERE at.agent_id = '{agent_id}'
    ORDER BY at.priority ASC;
    """)
    print()


if __name__ == "__main__":
    asyncio.run(test_tool_calls())
