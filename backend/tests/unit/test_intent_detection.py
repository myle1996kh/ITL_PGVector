"""Test script for intent detection in SupervisorAgent."""
import asyncio
import sys
sys.path.insert(0, "/path/to/backend")

from sqlalchemy.orm import Session
from src.config import get_db
from src.services.supervisor_agent import SupervisorAgent


async def test_intent_detection():
    """Test intent detection with various messages."""
    db = next(get_db())
    tenant_id = "2628802d-1dff-4a98-9325-704433c5d3ab"

    supervisor = SupervisorAgent(
        db=db,
        tenant_id=tenant_id,
        jwt_token=""
    )

    test_messages = [
        # Should route to AgentDebt
        ("Show me the debt for tax code 0123456789012", "AgentDebt"),
        ("What is my account balance?", "AgentDebt"),
        ("Show recent payments", "AgentDebt"),
        ("Get the customer debt by MST 123", "AgentDebt"),

        # Should route to AgentAnalysis
        ("What's the company policy on refunds?", "AgentAnalysis"),
        ("Search knowledge base for return policies", "AgentAnalysis"),
        ("Tell me about shipping costs", "AgentAnalysis"),

        # Should be MULTI_INTENT
        ("Show my debt AND tell me the refund policy", "MULTI_INTENT"),
        ("What's my balance and what's the return policy?", "MULTI_INTENT"),

        # Should be UNCLEAR
        ("What's the weather today?", "UNCLEAR"),
        ("Tell me a joke", "UNCLEAR"),
        ("Thời tiết hôm nay thế nào?", "UNCLEAR"),
    ]

    print("="*100)
    print("INTENT DETECTION TEST")
    print("="*100)

    correct = 0
    total = len(test_messages)

    for message, expected_agent in test_messages:
        agent_name = await supervisor._detect_intent(message)
        is_correct = agent_name == expected_agent
        status = "✓" if is_correct else "✗"

        if is_correct:
            correct += 1

        print(f"{status} Message: {message}")
        print(f"  Expected: {expected_agent}, Got: {agent_name}")
        print()

    print("="*100)
    print(f"ACCURACY: {correct}/{total} ({100*correct//total}%)")
    print("="*100)


if __name__ == "__main__":
    asyncio.run(test_intent_detection())
