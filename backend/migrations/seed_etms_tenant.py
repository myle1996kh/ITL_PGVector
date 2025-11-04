"""Seed data for eTMS tenant with specific LLM configurations.

This script creates:
- eTMS tenant
- LLM models (OpenRouter and OpenAI providers)
- Base tools (HTTP, RAG, DB, OCR)
- Tool configurations
- AgentGuidance for RAG
- Tenant permissions and LLM configs

Usage:
    python migrations/seed_etms_tenant.py
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/chatbot_db")
FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    print("❌ Error: FERNET_KEY not found in .env file")
    print("   Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
    sys.exit(1)

# Initialize encryption
fernet = Fernet(FERNET_KEY.encode())

# API Keys from user requirements - set these to your actual keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your-openrouter-api-key-here")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")


def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key using Fernet."""
    return fernet.encrypt(api_key.encode()).decode()


def main():
    """Seed eTMS tenant data."""
    print("\n" + "="*70)
    print("SEEDING eTMS TENANT DATA")
    print("="*70 + "\n")

    # Create database connection
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Generate UUIDs for all entities
        etms_tenant_id = str(uuid.uuid4())

        # Base tools
        http_get_id = str(uuid.uuid4())
        http_post_id = str(uuid.uuid4())
        rag_id = str(uuid.uuid4())
        db_query_id = str(uuid.uuid4())
        ocr_id = str(uuid.uuid4())

        # Output formats
        structured_json_id = str(uuid.uuid4())
        markdown_table_id = str(uuid.uuid4())
        chart_data_id = str(uuid.uuid4())
        summary_text_id = str(uuid.uuid4())

        # LLM models
        openrouter_gpt4o_mini_id = str(uuid.uuid4())
        openrouter_gemini_id = str(uuid.uuid4())
        openai_gpt4o_mini_id = str(uuid.uuid4())

        # Tools
        tool_rag_search_id = str(uuid.uuid4())

        # Agents
        agent_guidance_id = str(uuid.uuid4())

        print("✓ Generated UUIDs for all entities\n")

        # ========================================================================
        # 1. CREATE BASE TOOLS
        # ========================================================================
        print("📦 Creating base tools...")

        session.execute(text(f"""
            INSERT INTO base_tools (base_tool_id, type, handler_class, description)
            VALUES
            ('{http_get_id}', 'HTTP_GET', 'tools.http.HTTPGetTool', 'HTTP GET request tool'),
            ('{http_post_id}', 'HTTP_POST', 'tools.http.HTTPPostTool', 'HTTP POST request tool'),
            ('{rag_id}', 'RAG', 'tools.rag.RAGTool', 'RAG vector search tool using PgVector'),
            ('{db_query_id}', 'DB_QUERY', 'tools.db.DBQueryTool', 'Database query tool'),
            ('{ocr_id}', 'OCR', 'tools.ocr.OCRTool', 'OCR document processing tool')
            ON CONFLICT (type) DO NOTHING
        """))
        session.commit()
        print("✓ Base tools created\n")

        # ========================================================================
        # 2. CREATE OUTPUT FORMATS
        # ========================================================================
        print("📄 Creating output formats...")

        session.execute(text(f"""
            INSERT INTO output_formats (format_id, name, schema, renderer_hint, description)
            VALUES
            ('{structured_json_id}', 'structured_json', '{{"type": "object"}}'::jsonb, '{{"type": "json"}}'::jsonb, 'Structured JSON output format'),
            ('{markdown_table_id}', 'markdown_table', '{{"type": "string"}}'::jsonb, '{{"type": "table"}}'::jsonb, 'Markdown table output format'),
            ('{chart_data_id}', 'chart_data', '{{"type": "object"}}'::jsonb, '{{"type": "chart", "chartType": "bar"}}'::jsonb, 'Chart data output format'),
            ('{summary_text_id}', 'summary_text', '{{"type": "string"}}'::jsonb, '{{"type": "text"}}'::jsonb, 'Summary text output format')
            ON CONFLICT (name) DO NOTHING
        """))
        session.commit()
        print("✓ Output formats created\n")

        # ========================================================================
        # 3. CREATE LLM MODELS
        # ========================================================================
        print("🤖 Creating LLM models...")

        session.execute(text(f"""
            INSERT INTO llm_models (llm_model_id, provider, model_name, context_window, cost_per_1k_input_tokens, cost_per_1k_output_tokens, is_active)
            VALUES
            ('{openrouter_gpt4o_mini_id}', 'openrouter', 'openai/gpt-4o-mini', 128000, 0.00015, 0.0006, true),
            ('{openrouter_gemini_id}', 'openrouter', 'google/gemini-2.5-flash-lite', 1048576, 0.000075, 0.0003, true),
            ('{openai_gpt4o_mini_id}', 'openai', 'gpt-4o-mini', 128000, 0.00015, 0.0006, true)
        """))
        session.commit()
        print("✓ LLM models created")
        print(f"  - OpenRouter: openai/gpt-4o-mini")
        print(f"  - OpenRouter: google/gemini-2.5-flash-lite")
        print(f"  - OpenAI: gpt-4o-mini\n")

        # ========================================================================
        # 4. CREATE eTMS TENANT
        # ========================================================================
        print("🏢 Creating eTMS tenant...")

        session.execute(text(f"""
            INSERT INTO tenants (tenant_id, name, domain, status)
            VALUES ('{etms_tenant_id}', 'eTMS', 'etms.example.com', 'active')
        """))
        session.commit()
        print(f"✓ eTMS tenant created (ID: {etms_tenant_id})\n")

        # ========================================================================
        # 5. CREATE TENANT LLM CONFIGS (Multiple providers)
        # ========================================================================
        print("🔑 Creating tenant LLM configs with encrypted API keys...")

        # Encrypt API keys
        encrypted_openrouter_key = encrypt_api_key(OPENROUTER_API_KEY)
        encrypted_openai_key = encrypt_api_key(OPENAI_API_KEY)

        # Primary config: OpenRouter GPT-4o-mini
        openrouter_config_id = str(uuid.uuid4())
        session.execute(text(f"""
            INSERT INTO tenant_llm_configs (config_id, tenant_id, llm_model_id, encrypted_api_key, rate_limit_rpm, rate_limit_tpm)
            VALUES ('{openrouter_config_id}', '{etms_tenant_id}', '{openrouter_gpt4o_mini_id}', '{encrypted_openrouter_key}', 60, 10000)
        """))

        print(f"✓ OpenRouter config created")
        print(f"  - Provider: openrouter")
        print(f"  - Model: openai/gpt-4o-mini")
        print(f"  - API Key: {OPENROUTER_API_KEY[:20]}...\n")

        session.commit()

        # ========================================================================
        # 6. CREATE RAG TOOL CONFIG
        # ========================================================================
        print("🔍 Creating RAG tool configuration...")

        session.execute(text(f"""
            INSERT INTO tool_configs (tool_id, name, base_tool_id, config, input_schema, output_format_id, description, is_active)
            VALUES (
                '{tool_rag_search_id}',
                'search_knowledge_base',
                (SELECT base_tool_id FROM base_tools WHERE type = 'RAG'),
                '{{"top_k": 5}}'::jsonb,
                '{{"type": "object", "properties": {{"query": {{"type": "string"}}}}, "required": ["query"]}}'::jsonb,
                '{summary_text_id}',
                'Search eTMS knowledge base using PgVector RAG',
                true
            )
        """))
        session.commit()
        print("✓ RAG tool configured (top_k: 5)\n")

        # ========================================================================
        # 7. CREATE AgentGuidance
        # ========================================================================
        print("🤖 Creating AgentGuidance agent...")

        guidance_prompt = """You are AgentGuidance, an expert assistant for the eTMS (Enterprise Transport Management System).

Your role:
- Help users understand eTMS features and workflows
- Answer questions about eTMS operation procedures
- Provide guidance on creating orders, tracking shipments, and managing logistics
- Use the search_knowledge_base tool to retrieve relevant information from the eTMS User Guide

When answering:
1. Always search the knowledge base first using the tool
2. Provide clear, step-by-step instructions in Vietnamese (if query is in Vietnamese) or English
3. Cite specific pages from the user guide when available
4. If information is not found, clearly state that

Always be helpful, accurate, and cite your sources from the eTMS User Guide."""

        session.execute(text(f"""
            INSERT INTO agent_configs (agent_id, name, prompt_template, llm_model_id, default_output_format_id, description, handler_class, is_active)
            VALUES (
                '{agent_guidance_id}',
                'AgentGuidance',
                '{guidance_prompt}',
                '{openrouter_gpt4o_mini_id}',
                '{summary_text_id}',
                'eTMS guidance agent with RAG capabilities',
                'services.domain_agents.DomainAgent',
                true
            )
        """))
        session.commit()
        print(f"✓ AgentGuidance created (ID: {agent_guidance_id})\n")

        # ========================================================================
        # 8. LINK AGENT TO RAG TOOL
        # ========================================================================
        print("🔗 Linking AgentGuidance to RAG tool...")

        session.execute(text(f"""
            INSERT INTO agent_tools (agent_id, tool_id, priority)
            VALUES ('{agent_guidance_id}', '{tool_rag_search_id}', 1)
        """))
        session.commit()
        print("✓ Agent-tool link created\n")

        # ========================================================================
        # 9. GRANT TENANT PERMISSIONS
        # ========================================================================
        print("✅ Granting tenant permissions...")

        # Agent permission
        session.execute(text(f"""
            INSERT INTO tenant_agent_permissions (tenant_id, agent_id, enabled)
            VALUES ('{etms_tenant_id}', '{agent_guidance_id}', true)
        """))

        # Tool permission
        session.execute(text(f"""
            INSERT INTO tenant_tool_permissions (tenant_id, tool_id, enabled)
            VALUES ('{etms_tenant_id}', '{tool_rag_search_id}', true)
        """))

        session.commit()
        print("✓ Permissions granted\n")

        # ========================================================================
        # SUMMARY
        # ========================================================================
        print("="*70)
        print("✅ eTMS TENANT SEEDING COMPLETE!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  Tenant ID: {etms_tenant_id}")
        print(f"  Tenant Name: eTMS")
        print(f"  Domain: etms.example.com")
        print(f"\n🤖 LLM Models:")
        print(f"  - OpenRouter: openai/gpt-4o-mini (ID: {openrouter_gpt4o_mini_id})")
        print(f"  - OpenRouter: google/gemini-2.5-flash-lite (ID: {openrouter_gemini_id})")
        print(f"  - OpenAI: gpt-4o-mini (ID: {openai_gpt4o_mini_id})")
        print(f"\n🔧 Tools:")
        print(f"  - search_knowledge_base (RAG) (ID: {tool_rag_search_id})")
        print(f"\n👤 Agents:")
        print(f"  - AgentGuidance (ID: {agent_guidance_id})")
        print(f"\n🔑 API Keys:")
        print(f"  - OpenRouter: {OPENROUTER_API_KEY[:25]}... (encrypted)")
        print(f"  - OpenAI: {OPENAI_API_KEY[:25]}... (encrypted)")
        print(f"\n📚 Next Steps:")
        print(f"  1. Run: python migrations/seed_etms_rag_data.py")
        print(f"     (This will process the eTMS PDF and create RAG embeddings)")
        print(f"  2. Test the agent:")
        print(f"     curl -X POST http://localhost:8000/api/{etms_tenant_id}/chat \\")
        print(f"       -H 'Content-Type: application/json' \\")
        print(f"       -d '{{'\"message\": \"Hướng dẫn tạo đơn hàng\", \"user_id\": \"test\"}}'")
        print("="*70 + "\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
