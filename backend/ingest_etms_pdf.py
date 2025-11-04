"""
Ingest eTMS USER GUIDE PDF for Demo Tenant

This script ingests the eTMS PDF into the Demo Company tenant's knowledge base
so it can be queried by the guidance agent.

Usage:
    python ingest_etms_pdf.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.rag_service import get_rag_service
from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
TENANT_ID = "128e9b53-7610-453f-a2d4-a5d2537a36c4"  # Demo Company
PDF_PATH = "../notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf"

def main():
    print("="*70)
    print("eTMS USER GUIDE PDF Ingestion - Demo Company Tenant")
    print("="*70)
    print(f"\nTenant ID: {TENANT_ID}")
    print(f"PDF Path: {PDF_PATH}\n")

    # Check if PDF exists
    if not Path(PDF_PATH).exists():
        print(f"❌ ERROR: PDF not found at {PDF_PATH}")
        return False

    try:
        # Get RAG service
        print("→ Initializing RAG Service...")
        rag_service = get_rag_service()
        print(f"✓ RAG Service initialized (backend: pgvector)")

        # Create collection (verify setup)
        print("\n→ Verifying tenant collection...")
        collection_result = rag_service.create_tenant_collection(
            tenant_id=TENANT_ID
        )

        if not collection_result["success"]:
            raise Exception(f"Collection setup failed: {collection_result.get('error')}")

        print(f"✓ Collection ready: {collection_result['collection_name']}")

        # Ingest PDF
        print(f"\n→ Processing PDF: {PDF_PATH}")
        print("  This will:")
        print("  1. Load 714 pages")
        print("  2. Split into ~910 chunks (1000 chars, 200 overlap)")
        print("  3. Generate embeddings (all-MiniLM-L6-v2, 384 dims)")
        print("  4. Store in PgVector with tenant isolation")
        print("\n  ⏳ Processing... (this may take 2-3 minutes)\n")

        ingest_result = rag_service.ingest_pdf(
            tenant_id=TENANT_ID,
            pdf_path=PDF_PATH,
            additional_metadata={
                "source": "eTMS_USER_GUIDE",
                "document_type": "user_manual",
                "version": "latest"
            }
        )

        if not ingest_result["success"]:
            raise Exception(f"PDF ingestion failed: {ingest_result.get('error')}")

        print(f"✓ PDF successfully ingested!")
        print(f"  - Chunk count: {ingest_result['document_count']}")
        print(f"  - Collection: {ingest_result['collection_name']}")
        print(f"  - First 3 doc IDs: {ingest_result['document_ids'][:3]}")

        # Test query
        print("\n→ Testing knowledge base query...")
        test_queries = [
            "What is shipment tracking in eTMS?",
            "How to create a new shipment?",
            "What are the main features of eTMS?"
        ]

        for query in test_queries:
            query_result = rag_service.query_knowledge_base(
                tenant_id=TENANT_ID,
                query=query,
                top_k=3
            )

            if not query_result["success"]:
                print(f"  ⚠️  Query failed: {query_result.get('error')}")
                continue

            print(f"\n  Query: '{query}'")
            print(f"  Results: {query_result['total_results']}")

            if query_result['documents']:
                top_doc = query_result['documents'][0]
                print(f"  Top match (distance: {top_doc['distance']:.4f}):")
                print(f"  > {top_doc['content'][:150]}...")

        # Get stats
        print("\n→ Knowledge base statistics...")
        stats_result = rag_service.get_collection_stats(tenant_id=TENANT_ID)

        if stats_result["success"]:
            print(f"✓ Total documents: {stats_result['document_count']}")
        else:
            print(f"  ⚠️  Failed to get stats: {stats_result.get('error')}")

        print("\n" + "="*70)
        print("✅ SUCCESS! eTMS USER GUIDE is now available for queries")
        print("="*70)
        print("\nYou can now test with the guidance agent:")
        print("  - Ask questions about eTMS features")
        print("  - Query shipment tracking procedures")
        print("  - Get help with system functionality")
        print("\nExample queries:")
        print("  'How do I track a shipment in eTMS?'")
        print("  'What are the steps to create a new order?'")
        print("  'Explain the eTMS dashboard features'")
        print("\n")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
