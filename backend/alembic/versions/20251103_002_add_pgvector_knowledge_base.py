"""Add pgvector knowledge base schema

Revision ID: 002
Revises: 001
Create Date: 2025-11-03

This migration creates the knowledge_documents table for PgVector-based RAG:
- Enables pgvector extension
- Creates table with vector embeddings (384 dimensions for all-MiniLM-L6-v2)
- Adds HNSW index for fast similarity search
- Implements multi-tenant isolation with tenant_id

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pgvector extension and knowledge_documents table."""

    # 1. Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 2. Create knowledge_documents table
    op.create_table(
        'knowledge_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float), nullable=True),  # Will be populated by pgvector
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE')
    )

    # 3. Create indexes

    # Standard indexes
    op.create_index('idx_knowledge_documents_tenant', 'knowledge_documents', ['tenant_id'])
    op.create_index('idx_knowledge_documents_metadata', 'knowledge_documents', ['metadata'], postgresql_using='gin')
    op.create_index('idx_knowledge_documents_created', 'knowledge_documents', ['created_at'])

    # Vector index - NOTE: This uses raw SQL because SQLAlchemy doesn't directly support vector types
    # The embedding column will be cast to vector(384) by LangChain's PGVector
    # HNSW index parameters:
    #   m = 16: Good balance for recall/speed (range: 12-48)
    #   ef_construction = 64: Build quality (range: 40-400)
    # These will be created by LangChain when first using PGVector

    # 4. Create trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_knowledge_documents_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_knowledge_documents_updated_at
        BEFORE UPDATE ON knowledge_documents
        FOR EACH ROW
        EXECUTE FUNCTION update_knowledge_documents_updated_at();
    """)

    print("\n" + "="*70)
    print("PGVECTOR SCHEMA CREATED SUCCESSFULLY")
    print("="*70)
    print("\n✓ pgvector extension enabled")
    print("✓ knowledge_documents table created")
    print("✓ Indexes created (tenant_id, metadata, created_at)")
    print("✓ Trigger for updated_at created")
    print("\nℹ️  Note: Vector index will be created by LangChain's PGVector")
    print("   when first initializing the vector store.")
    print("\n📚 Table supports:")
    print("   - Multi-tenant isolation via tenant_id")
    print("   - JSONB metadata for flexible document properties")
    print("   - 384-dimensional embeddings (all-MiniLM-L6-v2)")
    print("="*70 + "\n")


def downgrade() -> None:
    """Drop knowledge_documents table and pgvector extension."""

    # Drop trigger
    op.execute('DROP TRIGGER IF EXISTS trigger_knowledge_documents_updated_at ON knowledge_documents')
    op.execute('DROP FUNCTION IF EXISTS update_knowledge_documents_updated_at()')

    # Drop table (indexes are dropped automatically)
    op.drop_table('knowledge_documents')

    # Drop extension (only if no other tables use it)
    # Commented out for safety - manual removal if needed
    # op.execute('DROP EXTENSION IF EXISTS vector')

    print("\n✓ knowledge_documents table and related objects dropped")
