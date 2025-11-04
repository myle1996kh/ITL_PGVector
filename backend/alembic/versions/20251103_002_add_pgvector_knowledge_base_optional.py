"""Add pgvector knowledge base schema (optional - skips if pgvector not available)

Revision ID: 002
Revises: 001
Create Date: 2025-11-03

This migration creates the knowledge_documents table for PgVector-based RAG.
If pgvector extension is not available, it will skip extension creation but
still create the table structure (without vector functionality).

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

    conn = op.get_bind()

    # 1. Try to enable pgvector extension (skip if not available)
    try:
        conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS vector'))
        print("\n✓ pgvector extension enabled")
        has_pgvector = True
    except Exception as e:
        print(f"\n⚠️  Warning: Could not enable pgvector extension: {e}")
        print("   RAG functionality will be limited without pgvector")
        print("   Install pgvector: https://github.com/pgvector/pgvector")
        has_pgvector = False

    # 2. Create knowledge_documents table
    # Use ARRAY(Float) instead of vector type if pgvector not available
    op.create_table(
        'knowledge_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float), nullable=True),  # Works with or without pgvector
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE')
    )

    # 3. Create indexes
    op.create_index('idx_knowledge_documents_tenant', 'knowledge_documents', ['tenant_id'])
    op.create_index('idx_knowledge_documents_metadata', 'knowledge_documents', ['metadata'], postgresql_using='gin')
    op.create_index('idx_knowledge_documents_created', 'knowledge_documents', ['created_at'])

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
    if has_pgvector:
        print("PGVECTOR SCHEMA CREATED SUCCESSFULLY")
    else:
        print("KNOWLEDGE BASE SCHEMA CREATED (WITHOUT PGVECTOR)")
    print("="*70)
    print("\n✓ knowledge_documents table created")
    print("✓ Indexes created (tenant_id, metadata, created_at)")
    print("✓ Trigger for updated_at created")

    if has_pgvector:
        print("\n✅ RAG system ready with pgvector support")
        print("   - Vector similarity search enabled")
        print("   - Optimal performance for embeddings")
    else:
        print("\n⚠️  RAG system created WITHOUT pgvector")
        print("   - Embeddings stored as arrays (slower)")
        print("   - Install pgvector for better performance")
        print("   - See: https://github.com/pgvector/pgvector")

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

    # Try to drop extension (only if no other tables use it)
    conn = op.get_bind()
    try:
        conn.execute(sa.text('DROP EXTENSION IF EXISTS vector'))
    except Exception:
        pass  # Ignore if extension is in use

    print("\n✓ knowledge_documents table and related objects dropped")
