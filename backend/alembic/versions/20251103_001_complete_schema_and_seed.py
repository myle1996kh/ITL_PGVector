"""Complete schema with all 14 tables and comprehensive seed data

Revision ID: 001
Revises:
Create Date: 2025-11-03

This migration creates all database tables and seeds initial data:
- 14 tables (including tenant_widget_configs)
- 5 base tools
- 4 output formats
- 4 LLM models
- 4 tool configs
- 4 agents
- 1 demo tenant with full configuration

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
import secrets

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables and insert seed data in ONE migration."""

    # ========================================================================
    # PART 1: CREATE ALL TABLES
    # ========================================================================

    # 1. tenants table
    op.create_table(
        'tenants',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), unique=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('ix_tenants_status', 'tenants', ['status'])

    # 2. llm_models table
    op.create_table(
        'llm_models',
        sa.Column('llm_model_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('context_window', sa.Integer, nullable=False),
        sa.Column('cost_per_1k_input_tokens', sa.DECIMAL(10, 6), nullable=False),
        sa.Column('cost_per_1k_output_tokens', sa.DECIMAL(10, 6), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('capabilities', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now())
    )
    op.create_index('ix_llm_models_provider_model', 'llm_models', ['provider', 'model_name'])
    op.create_index('ix_llm_models_is_active', 'llm_models', ['is_active'])

    # 3. tenant_llm_configs table
    op.create_table(
        'tenant_llm_configs',
        sa.Column('config_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('llm_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encrypted_api_key', sa.Text, nullable=False),
        sa.Column('rate_limit_rpm', sa.Integer, server_default='60'),
        sa.Column('rate_limit_tpm', sa.Integer, server_default='10000'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id']),
        sa.ForeignKeyConstraint(['llm_model_id'], ['llm_models.llm_model_id'])
    )
    op.create_index('ix_tenant_llm_configs_llm_model', 'tenant_llm_configs', ['llm_model_id'])

    # 4. base_tools table
    op.create_table(
        'base_tools',
        sa.Column('base_tool_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('type', sa.String(50), nullable=False, unique=True),
        sa.Column('handler_class', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('default_config_schema', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now())
    )

    # 5. output_formats table
    op.create_table(
        'output_formats',
        sa.Column('format_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('schema', postgresql.JSONB),
        sa.Column('renderer_hint', postgresql.JSONB),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now())
    )

    # 6. tool_configs table
    op.create_table(
        'tool_configs',
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('base_tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('config', postgresql.JSONB, nullable=False),
        sa.Column('input_schema', postgresql.JSONB, nullable=False),
        sa.Column('output_format_id', postgresql.UUID(as_uuid=True)),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['base_tool_id'], ['base_tools.base_tool_id']),
        sa.ForeignKeyConstraint(['output_format_id'], ['output_formats.format_id'])
    )
    op.create_index('ix_tool_configs_base_tool', 'tool_configs', ['base_tool_id'])
    op.create_index('ix_tool_configs_is_active', 'tool_configs', ['is_active'])

    # 7. agent_configs table
    op.create_table(
        'agent_configs',
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('prompt_template', sa.Text, nullable=False),
        sa.Column('llm_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('default_output_format_id', postgresql.UUID(as_uuid=True)),
        sa.Column('description', sa.Text),
        sa.Column('handler_class', sa.String(255), server_default='services.domain_agents.DomainAgent'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['llm_model_id'], ['llm_models.llm_model_id']),
        sa.ForeignKeyConstraint(['default_output_format_id'], ['output_formats.format_id'])
    )
    op.create_index('ix_agent_configs_is_active', 'agent_configs', ['is_active'])

    # 8. agent_tools junction table
    op.create_table(
        'agent_tools',
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('priority', sa.Integer, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('agent_id', 'tool_id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_configs.agent_id']),
        sa.ForeignKeyConstraint(['tool_id'], ['tool_configs.tool_id'])
    )
    op.create_index('ix_agent_tools_agent_priority', 'agent_tools', ['agent_id', 'priority'])

    # 9. tenant_agent_permissions table
    op.create_table(
        'tenant_agent_permissions',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('output_override_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('tenant_id', 'agent_id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id']),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_configs.agent_id']),
        sa.ForeignKeyConstraint(['output_override_id'], ['output_formats.format_id'])
    )
    op.create_index('ix_tenant_agent_permissions_enabled', 'tenant_agent_permissions', ['enabled'])

    # 10. tenant_tool_permissions table
    op.create_table(
        'tenant_tool_permissions',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('tenant_id', 'tool_id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id']),
        sa.ForeignKeyConstraint(['tool_id'], ['tool_configs.tool_id'])
    )
    op.create_index('ix_tenant_tool_permissions_enabled', 'tenant_tool_permissions', ['enabled'])

    # 11. sessions table
    op.create_table(
        'sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True)),
        sa.Column('thread_id', sa.String(500)),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id']),
        sa.ForeignKeyConstraint(['agent_id'], ['agent_configs.agent_id'])
    )
    op.create_index('ix_sessions_tenant_user', 'sessions', ['tenant_id', 'user_id', 'created_at'])
    op.create_index('ix_sessions_last_message', 'sessions', ['last_message_at'])

    # 12. messages table
    op.create_table(
        'messages',
        sa.Column('message_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.session_id'])
    )
    op.create_index('ix_messages_session_timestamp', 'messages', ['session_id', 'timestamp'])

    # 13. checkpoints table (for LangGraph PostgresSaver)
    op.create_table(
        'checkpoints',
        sa.Column('thread_id', sa.Text, primary_key=True),
        sa.Column('checkpoint_id', sa.Text, primary_key=True),
        sa.Column('parent_id', sa.Text),
        sa.Column('checkpoint', sa.LargeBinary, nullable=False),
        sa.Column('metadata', postgresql.JSONB)
    )

    # 14. tenant_widget_configs table
    op.create_table(
        'tenant_widget_configs',
        sa.Column('config_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('widget_key', sa.String(64), nullable=False, unique=True),
        sa.Column('widget_secret', sa.String(255), nullable=False),
        sa.Column('theme', sa.String(20), server_default='light'),
        sa.Column('primary_color', sa.String(7), server_default='#3B82F6'),
        sa.Column('position', sa.String(20), server_default='bottom-right'),
        sa.Column('custom_css', sa.Text),
        sa.Column('auto_open', sa.Boolean, server_default='false'),
        sa.Column('welcome_message', sa.Text),
        sa.Column('placeholder_text', sa.String(255), server_default='Type your message...'),
        sa.Column('allowed_domains', postgresql.JSONB, server_default='[]'),
        sa.Column('max_session_duration', sa.Integer, server_default='3600'),
        sa.Column('rate_limit_per_minute', sa.Integer, server_default='20'),
        sa.Column('enable_file_upload', sa.Boolean, server_default='false'),
        sa.Column('enable_voice_input', sa.Boolean, server_default='false'),
        sa.Column('enable_conversation_history', sa.Boolean, server_default='true'),
        sa.Column('embed_script_url', sa.String(500)),
        sa.Column('embed_code_snippet', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_regenerated_at', sa.TIMESTAMP),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'])
    )
    op.create_index('ix_widget_configs_widget_key', 'tenant_widget_configs', ['widget_key'])

    # ========================================================================
    # PART 2: SEED DATA
    # ========================================================================

    # Generate UUIDs for seed data
    http_get_id = str(uuid.uuid4())
    http_post_id = str(uuid.uuid4())
    rag_id = str(uuid.uuid4())
    db_query_id = str(uuid.uuid4())
    ocr_id = str(uuid.uuid4())

    structured_json_id = str(uuid.uuid4())
    markdown_table_id = str(uuid.uuid4())
    chart_data_id = str(uuid.uuid4())
    summary_text_id = str(uuid.uuid4())

    gpt4o_mini_id = str(uuid.uuid4())
    gpt4o_id = str(uuid.uuid4())
    gemini_id = str(uuid.uuid4())
    claude_id = str(uuid.uuid4())

    # Seed base_tools
    op.execute(
        f"""
        INSERT INTO base_tools (base_tool_id, type, handler_class, description) VALUES
        ('{http_get_id}', 'HTTP_GET', 'tools.http.HTTPGetTool', 'HTTP GET request tool'),
        ('{http_post_id}', 'HTTP_POST', 'tools.http.HTTPPostTool', 'HTTP POST request tool'),
        ('{rag_id}', 'RAG', 'tools.rag.RAGTool', 'RAG vector search tool'),
        ('{db_query_id}', 'DB_QUERY', 'tools.db.DBQueryTool', 'Database query tool'),
        ('{ocr_id}', 'OCR', 'tools.ocr.OCRTool', 'OCR document processing tool')
        """
    )

    # Seed output_formats
    op.execute(
        f"""
        INSERT INTO output_formats (format_id, name, schema, renderer_hint, description) VALUES
        ('{structured_json_id}', 'structured_json', '{{"type": "object"}}'::jsonb, '{{"type": "json"}}'::jsonb, 'Structured JSON output format'),
        ('{markdown_table_id}', 'markdown_table', '{{"type": "string"}}'::jsonb, '{{"type": "table"}}'::jsonb, 'Markdown table output format'),
        ('{chart_data_id}', 'chart_data', '{{"type": "object"}}'::jsonb, '{{"type": "chart", "chartType": "bar"}}'::jsonb, 'Chart data output format'),
        ('{summary_text_id}', 'summary_text', '{{"type": "string"}}'::jsonb, '{{"type": "text"}}'::jsonb, 'Summary text output format')
        """
    )

    # Seed llm_models
    op.execute(
        f"""
        INSERT INTO llm_models (llm_model_id, provider, model_name, context_window, cost_per_1k_input_tokens, cost_per_1k_output_tokens, is_active) VALUES
        ('{gpt4o_mini_id}', 'openrouter', 'openai/gpt-4o-mini', 128000, 0.00015, 0.0006, true),
        ('{gpt4o_id}', 'openrouter', 'openai/gpt-4o', 128000, 0.0025, 0.01, true),
        ('{gemini_id}', 'openrouter', 'google/gemini-1.5-pro', 1048576, 0.00125, 0.00375, true),
        ('{claude_id}', 'openrouter', 'anthropic/claude-3.5-sonnet', 200000, 0.003, 0.015, true)
        """
    )

    # Seed tool_configs
    tool_get_customer_debt_id = str(uuid.uuid4())
    tool_track_shipment_id = str(uuid.uuid4())
    tool_rag_search_id = str(uuid.uuid4())
    tool_sales_analytics_id = str(uuid.uuid4())

    op.execute(
        f"""
        INSERT INTO tool_configs (tool_id, name, base_tool_id, config, input_schema, output_format_id, description, is_active) VALUES
        ('{tool_get_customer_debt_id}', 'get_customer_debt', '{http_get_id}',
         '{{"endpoint": "https://api.example.com/customers/{{mst}}/debt", "method": "GET"}}'::jsonb,
         '{{"type": "object", "properties": {{"mst": {{"type": "string", "pattern": "^[0-9]{{10}}$"}}}}, "required": ["mst"]}}'::jsonb,
         '{structured_json_id}', 'Retrieve customer debt by MST', true),

        ('{tool_track_shipment_id}', 'track_shipment', '{http_get_id}',
         '{{"endpoint": "https://api.example.com/shipments/{{shipment_id}}/track", "method": "GET"}}'::jsonb,
         '{{"type": "object", "properties": {{"shipment_id": {{"type": "string"}}}}, "required": ["shipment_id"]}}'::jsonb,
         '{structured_json_id}', 'Track shipment status', true),

        ('{tool_rag_search_id}', 'search_knowledge_base', '{rag_id}',
         '{{"collection_name": "company_policies", "top_k": 5}}'::jsonb,
         '{{"type": "object", "properties": {{"query": {{"type": "string"}}}}, "required": ["query"]}}'::jsonb,
         '{summary_text_id}', 'Search knowledge base', true),

        ('{tool_sales_analytics_id}', 'get_sales_analytics', '{http_get_id}',
         '{{"endpoint": "https://api.example.com/analytics/sales", "method": "GET"}}'::jsonb,
         '{{"type": "object", "properties": {{"period": {{"type": "string", "enum": ["daily", "weekly", "monthly"]}}}}, "required": ["period"]}}'::jsonb,
         '{chart_data_id}', 'Get sales analytics', true)
        """
    )

    # Seed agent_configs
    agent_supervisor_id = str(uuid.uuid4())
    agent_debt_id = str(uuid.uuid4())
    agent_shipment_id = str(uuid.uuid4())
    agent_analysis_id = str(uuid.uuid4())

    supervisor_prompt = "You are SupervisorAgent. Route queries to: AgentDebt (debt/payment), AgentShipment (tracking), AgentAnalysis (knowledge/analytics). Respond with ONLY the agent name."
    debt_prompt = "You are AgentDebt. Help with customer debt inquiries. Use get_customer_debt tool when user provides MST (10-digit tax ID)."
    shipment_prompt = "You are AgentShipment. Help with shipment tracking. Use track_shipment tool when user provides shipment ID."
    analysis_prompt = "You are AgentAnalysis. Help with knowledge base queries and analytics. Use search_knowledge_base and get_sales_analytics tools."

    op.execute(
        f"""
        INSERT INTO agent_configs (agent_id, name, prompt_template, llm_model_id, default_output_format_id, description, is_active) VALUES
        ('{agent_supervisor_id}', 'SupervisorAgent', '{supervisor_prompt}', '{gpt4o_mini_id}', '{summary_text_id}', 'Intent router', true),
        ('{agent_debt_id}', 'AgentDebt', '{debt_prompt}', '{gpt4o_mini_id}', '{structured_json_id}', 'Customer debt specialist', true),
        ('{agent_shipment_id}', 'AgentShipment', '{shipment_prompt}', '{gpt4o_mini_id}', '{structured_json_id}', 'Shipment tracking specialist', true),
        ('{agent_analysis_id}', 'AgentAnalysis', '{analysis_prompt}', '{gpt4o_id}', '{summary_text_id}', 'Knowledge & analytics specialist', true)
        """
    )

    # Link agents to tools
    op.execute(
        f"""
        INSERT INTO agent_tools (agent_id, tool_id, priority) VALUES
        ('{agent_debt_id}', '{tool_get_customer_debt_id}', 1),
        ('{agent_shipment_id}', '{tool_track_shipment_id}', 1),
        ('{agent_analysis_id}', '{tool_rag_search_id}', 1),
        ('{agent_analysis_id}', '{tool_sales_analytics_id}', 2)
        """
    )

    # Create demo tenant
    demo_tenant_id = str(uuid.uuid4())
    op.execute(
        f"""
        INSERT INTO tenants (tenant_id, name, domain, status) VALUES
        ('{demo_tenant_id}', 'Demo Company', 'demo.agenthub.com', 'active')
        """
    )

    # Create demo tenant LLM config
    demo_llm_config_id = str(uuid.uuid4())
    op.execute(
        f"""
        INSERT INTO tenant_llm_configs (config_id, tenant_id, llm_model_id, encrypted_api_key, rate_limit_rpm, rate_limit_tpm) VALUES
        ('{demo_llm_config_id}', '{demo_tenant_id}', '{gpt4o_mini_id}', 'ENCRYPTED_KEY_PLACEHOLDER', 60, 10000)
        """
    )

    # Grant agent permissions
    op.execute(
        f"""
        INSERT INTO tenant_agent_permissions (tenant_id, agent_id, enabled) VALUES
        ('{demo_tenant_id}', '{agent_supervisor_id}', true),
        ('{demo_tenant_id}', '{agent_debt_id}', true),
        ('{demo_tenant_id}', '{agent_shipment_id}', true),
        ('{demo_tenant_id}', '{agent_analysis_id}', true)
        """
    )

    # Grant tool permissions
    op.execute(
        f"""
        INSERT INTO tenant_tool_permissions (tenant_id, tool_id, enabled) VALUES
        ('{demo_tenant_id}', '{tool_get_customer_debt_id}', true),
        ('{demo_tenant_id}', '{tool_track_shipment_id}', true),
        ('{demo_tenant_id}', '{tool_rag_search_id}', true),
        ('{demo_tenant_id}', '{tool_sales_analytics_id}', true)
        """
    )

    # Create widget config
    widget_key = f"wk_demo_{secrets.token_urlsafe(16)}"
    widget_config_id = str(uuid.uuid4())
    embed_snippet = f'<div id="agenthub-chat" data-widget-key="{widget_key}"></div><script src="https://widget.agenthub.com/embed.js" async></script>'

    op.execute(
        f"""
        INSERT INTO tenant_widget_configs (
            config_id, tenant_id, widget_key, widget_secret,
            theme, primary_color, position, welcome_message,
            allowed_domains, embed_script_url, embed_code_snippet
        ) VALUES (
            '{widget_config_id}', '{demo_tenant_id}', '{widget_key}', 'ENCRYPTED_SECRET_PLACEHOLDER',
            'light', '#3B82F6', 'bottom-right', 'Hello! How can I help you today?',
            '{{"domains": ["http://localhost:3000", "https://demo.agenthub.com"]}}'::jsonb,
            'https://widget.agenthub.com/embed.js',
            '{embed_snippet}'
        )
        """
    )

    # Print summary
    print("\n" + "="*70)
    print("DATABASE SETUP COMPLETE!")
    print("="*70)
    print(f"\n✓ 14 tables created")
    print(f"✓ 5 base tools seeded")
    print(f"✓ 4 output formats seeded")
    print(f"✓ 4 LLM models seeded")
    print(f"✓ 4 tool configs seeded")
    print(f"✓ 4 agents seeded")
    print(f"✓ 1 demo tenant created")
    print(f"\nDemo Tenant ID: {demo_tenant_id}")
    print(f"Widget Key: {widget_key}")
    print(f"\n⚠️  UPDATE API KEY:")
    print(f"UPDATE tenant_llm_configs")
    print(f"SET encrypted_api_key = '<your_encrypted_key>'")
    print(f"WHERE tenant_id = '{demo_tenant_id}';")
    print("="*70 + "\n")


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table('tenant_widget_configs')
    op.drop_table('checkpoints')
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('tenant_tool_permissions')
    op.drop_table('tenant_agent_permissions')
    op.drop_table('agent_tools')
    op.drop_table('agent_configs')
    op.drop_table('tool_configs')
    op.drop_table('output_formats')
    op.drop_table('base_tools')
    op.drop_table('tenant_llm_configs')
    op.drop_table('llm_models')
    op.drop_table('tenants')
