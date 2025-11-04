"""Complete end-to-end flow test for the chatbot."""
import asyncio
import sys
sys.path.insert(0, "/path/to/backend")

from sqlalchemy.orm import Session
from src.config import get_db
from src.services.supervisor_agent import SupervisorAgent


async def test_full_flow():
    """Test the complete flow from message to response."""
    db = next(get_db())
    tenant_id = "2628802d-1dff-4a98-9325-704433c5d3ab"

    supervisor = SupervisorAgent(
        db=db,
        tenant_id=tenant_id,
        jwt_token=""
    )

    test_messages = [
        "Show me the debt for tax code 0123456789012",
        "What's the company policy on refunds?",
        "What's the weather?",
    ]

    for message in test_messages:
        print()
        print("="*100)
        print("FULL FLOW TEST")
        print("="*100)
        print(f"Input Message: {message}\n")

        try:
            # Step 1: Intent Detection
            print("[STEP 1] INTENT DETECTION (SupervisorAgent._detect_intent)")
            agent_name = await supervisor._detect_intent(message)
            print(f"→ Detected Agent: {agent_name}")
            print()

            # Step 2-5: Routing + Extraction + Tool Call + Response
            print("[STEP 2-5] ROUTING → EXTRACTION → TOOL CALL → RESPONSE")
            response = await supervisor.route_message(message)

            print(f"→ Agent: {response.get('agent')}")
            print(f"→ Intent: {response.get('intent')}")
            print(f"→ Status: {response.get('status')}")
            print()

            metadata = response.get('metadata', {})

            # Step 3: Entity Extraction
            print("[STEP 3] ENTITY EXTRACTION")
            entities = metadata.get('extracted_entities', {})
            print(f"→ Extracted Entities: {entities}")
            print()

            # Step 4: Tool Calls
            print("[STEP 4] TOOL CALL DECISION & EXECUTION")
            tool_calls = metadata.get('tool_calls', [])
            print(f"→ Number of Tools Called: {len(tool_calls)}")
            for i, call in enumerate(tool_calls, 1):
                print(f"  [{i}] Tool: {call.get('tool_name')}")
                print(f"      Args: {call.get('tool_args')}")
            if not tool_calls:
                print("  (No tools called)")
            print()

            # Step 5: Response with metadata
            print("[STEP 5] RESPONSE")
            llm_model = metadata.get('llm_model', {})
            print(f"→ LLM Model Used: {llm_model.get('model_name', 'unknown')}")
            print(f"→ Model Class: {llm_model.get('model_class', 'unknown')}")
            print(f"→ Duration: {metadata.get('duration_ms', 0):.2f}ms")
            print(f"→ Status: {metadata.get('status', 'unknown')}")
            print()

            print("[FINAL RESPONSE]")
            response_data = response.get('response', {})
            if isinstance(response_data, dict):
                for key, value in response_data.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"→ {key}: {value[:100]}...")
                    else:
                        print(f"→ {key}: {value}")
            else:
                print(f"→ {response_data}")
            print()

            # Flow visualization
            print("[FLOW SUMMARY]")
            print(f"User Input")
            print(f"    ↓")
            print(f"Intent: {response.get('intent')} | Agent: {response.get('agent')}")
            print(f"    ↓")
            print(f"Entities: {list(entities.keys()) if entities else 'None'}")
            print(f"    ↓")
            print(f"Tools Called: {[call.get('tool_name') for call in tool_calls] if tool_calls else 'None'}")
            print(f"    ↓")
            print(f"Response Status: {response.get('status')}")
            print()

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*100)
    print("FLOW TEST COMPLETE")
    print("="*100)


if __name__ == "__main__":
    asyncio.run(test_full_flow())
