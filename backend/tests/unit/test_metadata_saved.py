"""Test script to verify metadata is saved to database."""
import sys
sys.path.insert(0, ".")

# Import all models first
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
from sqlalchemy import desc
import json


def check_message_metadata():
    """Check if metadata is saved in database."""
    db = next(get_db())

    print("="*100)
    print("CHECK MESSAGE METADATA IN DATABASE")
    print("="*100)
    print()

    # Query the most recent assistant messages
    messages = db.query(Message).filter(
        Message.role == "assistant"
    ).order_by(desc(Message.created_at)).limit(5).all()

    if not messages:
        print("❌ No assistant messages found in database")
        return

    print(f"Found {len(messages)} recent assistant messages")
    print()

    for i, msg in enumerate(messages, 1):
        print(f"[Message {i}]")
        print(f"  Message ID: {msg.message_id}")
        print(f"  Session ID: {msg.session_id}")
        print(f"  Role: {msg.role}")
        print(f"  Created at: {msg.created_at}")
        print()

        # Check metadata
        if msg.message_metadata:
            print(f"  ✓ Metadata found:")
            metadata = msg.message_metadata

            # Print each metadata field
            print(f"    - agent: {metadata.get('agent')}")
            print(f"    - intent: {metadata.get('intent')}")
            print(f"    - format: {metadata.get('format')}")
            print(f"    - status: {metadata.get('status')}")
            print()

            # Check for full metadata
            llm_model = metadata.get('llm_model')
            tool_calls = metadata.get('tool_calls')
            entities = metadata.get('extracted_entities')

            print(f"    LLM Model Info:")
            if llm_model:
                print(f"      ✓ Present: {json.dumps(llm_model, indent=6)}")
            else:
                print(f"      ❌ Missing")
            print()

            print(f"    Tool Calls:")
            if tool_calls:
                print(f"      ✓ Present ({len(tool_calls)} calls)")
                for j, call in enumerate(tool_calls, 1):
                    print(f"        {j}. {call.get('tool_name')} with args: {call.get('tool_args')}")
            else:
                print(f"      ❌ Missing or empty")
            print()

            print(f"    Extracted Entities:")
            if entities:
                print(f"      ✓ Present: {entities}")
            else:
                print(f"      ❌ Missing or empty")
            print()
        else:
            print(f"  ❌ No metadata found")

        print("-"*100)
        print()

    print("="*100)
    print("SUMMARY")
    print("="*100)
    print()

    # Count messages with full metadata
    count_with_metadata = 0
    count_with_tools = 0
    count_with_entities = 0
    count_with_llm = 0

    for msg in messages:
        if msg.message_metadata:
            count_with_metadata += 1
            if msg.message_metadata.get('tool_calls'):
                count_with_tools += 1
            if msg.message_metadata.get('extracted_entities'):
                count_with_entities += 1
            if msg.message_metadata.get('llm_model'):
                count_with_llm += 1

    print(f"Messages with metadata: {count_with_metadata}/{len(messages)}")
    print(f"Messages with tool_calls: {count_with_tools}/{len(messages)}")
    print(f"Messages with extracted_entities: {count_with_entities}/{len(messages)}")
    print(f"Messages with llm_model: {count_with_llm}/{len(messages)}")
    print()

    if count_with_metadata == len(messages):
        print("✓ All messages have metadata saved to database")
    else:
        print("⚠️ Some messages missing metadata - check code fixes were applied")
    print()


if __name__ == "__main__":
    check_message_metadata()
