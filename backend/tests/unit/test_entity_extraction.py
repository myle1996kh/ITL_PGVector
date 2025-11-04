"""Test script for entity extraction in DomainAgent."""
import asyncio
import sys
sys.path.insert(0, "/path/to/backend")

from sqlalchemy.orm import Session
from src.config import get_db
from src.services.domain_agents import AgentFactory


async def test_entity_extraction():
    """Test entity extraction from user messages."""
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
        print(f"Available agents: AgentDebt, AgentAnalysis")
        return

    test_cases = [
        {
            "message": "Show debt for tax code 0123456789012",
            "expected_entities": {"tax_code": "0123456789012"},
            "expected_intent": "query_debt"
        },
        {
            "message": "What's the balance for MST 456 sold by salesman John?",
            "expected_entities": {"mst": "456", "salesman": "John"},
            "expected_intent": "query_debt"
        },
        {
            "message": "Show payment history for tax code 9876543210123",
            "expected_entities": {"tax_code": "9876543210123"},
            "expected_intent": "query_debt"
        },
        {
            "message": "Customer John Doe with MST 789 owes money",
            "expected_entities": {"mst": "789"},
            "expected_intent": "query_debt"
        },
    ]

    print("="*100)
    print("ENTITY EXTRACTION TEST")
    print(f"Agent: {agent_name}")
    print("="*100)
    print()

    for i, test_case in enumerate(test_cases, 1):
        message = test_case["message"]
        expected_entities = test_case["expected_entities"]
        expected_intent = test_case["expected_intent"]

        print(f"Test Case {i}")
        print(f"Message: {message}")

        try:
            intent, entities = await agent._extract_intent_and_entities(message)

            print(f"Detected Intent: {intent} (Expected: {expected_intent})")
            print(f"Extracted Entities: {entities}")
            print(f"Expected Entities: {expected_entities}")

            # Check if all expected entities are present
            all_present = all(
                key in entities and entities[key] == value
                for key, value in expected_entities.items()
            )

            status = "✓" if all_present else "✗"
            print(f"{status} Entities Match")

        except Exception as e:
            print(f"✗ Error: {e}")

        print()

    print("="*100)


if __name__ == "__main__":
    asyncio.run(test_entity_extraction())
