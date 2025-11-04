"""
End-to-End Test for PgVector RAG Migration

This script tests the complete RAG pipeline:
1. Load eTMS USER GUIDE PDF
2. Process into chunks with embeddings
3. Store in PgVector
4. Query for relevant information
5. Verify multi-tenant isolation

Run from backend directory:
    python test_pgvector_rag.py
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.rag_service import get_rag_service
from services.embedding_service import get_embedding_service
from services.document_processor import get_document_processor
from utils.logging import get_logger

logger = get_logger(__name__)


def test_embedding_service():
    """Test 1: Embedding Service"""
    print("\n" + "="*70)
    print("TEST 1: Embedding Service")
    print("="*70)

    try:
        embedding_service = get_embedding_service()

        # Test single embedding
        test_text = "What is the shipment tracking process?"
        embedding = embedding_service.embed_text(test_text)

        print(f"✓ Model: {embedding_service.model_name}")
        print(f"✓ Dimension: {embedding_service.dimension}")
        print(f"✓ Embedding length: {len(embedding)}")
        print(f"✓ Sample values: {embedding[:5]}")

        assert len(embedding) == 384, "Expected 384 dimensions for all-MiniLM-L6-v2"
        print("\n✓ Embedding Service: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Embedding Service: FAILED - {e}")
        return False


def test_document_processor():
    """Test 2: Document Processor (PDF Loading & Chunking)"""
    print("\n" + "="*70)
    print("TEST 2: Document Processor")
    print("="*70)

    # Check if PDF exists
    pdf_path = "../notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf"
    if not os.path.exists(pdf_path):
        print(f"✗ PDF not found: {pdf_path}")
        print("  Skipping document processor test")
        return False

    try:
        doc_processor = get_document_processor()
        tenant_id = "test-tenant-123"

        # Process PDF
        chunks = doc_processor.process_pdf(
            pdf_path=pdf_path,
            tenant_id=tenant_id,
            additional_metadata={"source": "eTMS_USER_GUIDE"}
        )

        print(f"✓ PDF loaded: {pdf_path}")
        print(f"✓ Total chunks: {len(chunks)}")
        print(f"✓ Chunk size: {doc_processor.chunk_size}")
        print(f"✓ Chunk overlap: {doc_processor.chunk_overlap}")

        # Inspect first chunk
        if chunks:
            first_chunk = chunks[0]
            print(f"\n✓ First chunk preview:")
            print(f"  Content length: {len(first_chunk.page_content)} chars")
            print(f"  Metadata keys: {list(first_chunk.metadata.keys())}")
            print(f"  Tenant ID: {first_chunk.metadata.get('tenant_id')}")
            print(f"  Page: {first_chunk.metadata.get('page')}")
            print(f"  Chunk index: {first_chunk.metadata.get('chunk_index')}")

        print("\n✓ Document Processor: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Document Processor: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_service():
    """Test 3: RAG Service (PgVector Integration)"""
    print("\n" + "="*70)
    print("TEST 3: RAG Service (PgVector)")
    print("="*70)

    # Check if PDF exists
    pdf_path = "../notebook_test_pgvector/eTMS USER GUIDE DOCUMENT.pdf"
    if not os.path.exists(pdf_path):
        print(f"✗ PDF not found: {pdf_path}")
        print("  Skipping RAG service test")
        return False

    try:
        rag_service = get_rag_service()
        test_tenant_id = "demo-tenant-test"

        print(f"✓ RAG Service initialized")
        print(f"  Backend: pgvector")
        print(f"  Collection: {rag_service.collection_name}")

        # Test 1: Create collection (verify pgvector extension)
        print("\n→ Creating tenant collection...")
        collection_result = rag_service.create_tenant_collection(
            tenant_id=test_tenant_id
        )

        if not collection_result["success"]:
            raise Exception(f"Collection creation failed: {collection_result.get('error')}")

        print(f"✓ Collection created: {collection_result['collection_name']}")

        # Test 2: Ingest PDF
        print(f"\n→ Ingesting PDF: {pdf_path}")
        ingest_result = rag_service.ingest_pdf(
            tenant_id=test_tenant_id,
            pdf_path=pdf_path,
            additional_metadata={
                "source": "eTMS_USER_GUIDE",
                "test_run": "pgvector_migration"
            }
        )

        if not ingest_result["success"]:
            raise Exception(f"PDF ingestion failed: {ingest_result.get('error')}")

        print(f"✓ PDF ingested successfully")
        print(f"  Document count: {ingest_result['document_count']}")
        print(f"  Document IDs (first 3): {ingest_result['document_ids'][:3]}")

        # Test 3: Query knowledge base
        print(f"\n→ Querying knowledge base...")
        test_queries = [
            "What is shipment tracking?",
            "How do I create a new shipment?",
            "What are the system requirements?"
        ]

        for query in test_queries:
            query_result = rag_service.query_knowledge_base(
                tenant_id=test_tenant_id,
                query=query,
                top_k=3
            )

            if not query_result["success"]:
                raise Exception(f"Query failed: {query_result.get('error')}")

            print(f"\n  Query: '{query}'")
            print(f"  Results: {query_result['total_results']}")

            if query_result['documents']:
                top_doc = query_result['documents'][0]
                print(f"  Top match distance: {top_doc['distance']:.4f}")
                print(f"  Content preview: {top_doc['content'][:100]}...")

        # Test 4: Get collection stats
        print(f"\n→ Getting collection stats...")
        stats_result = rag_service.get_collection_stats(tenant_id=test_tenant_id)

        if not stats_result["success"]:
            raise Exception(f"Stats retrieval failed: {stats_result.get('error')}")

        print(f"✓ Collection stats:")
        print(f"  Document count: {stats_result['document_count']}")
        print(f"  Collection: {stats_result['collection_name']}")

        # Test 5: Multi-tenant isolation
        print(f"\n→ Testing multi-tenant isolation...")
        other_tenant_id = "other-tenant-999"

        # Query from different tenant (should return 0 results)
        isolation_result = rag_service.query_knowledge_base(
            tenant_id=other_tenant_id,
            query="shipment tracking",
            top_k=5
        )

        if isolation_result["total_results"] == 0:
            print(f"✓ Multi-tenant isolation verified")
            print(f"  Query from tenant '{other_tenant_id}' returned 0 results (expected)")
        else:
            raise Exception(f"Multi-tenant isolation FAILED: {isolation_result['total_results']} results found")

        print("\n✓ RAG Service: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ RAG Service: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Optional: Clean up test data"""
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)
    print("Note: Test data remains in database for inspection.")
    print("To clean up manually, run:")
    print("  DELETE FROM langchain_pg_embedding WHERE cmetadata->>'tenant_id' = 'demo-tenant-test';")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PgVector RAG Migration - End-to-End Test")
    print("="*70)

    results = {
        "embedding_service": test_embedding_service(),
        "document_processor": test_document_processor(),
        "rag_service": test_rag_service(),
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests PASSED! PgVector RAG migration is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED. Please review errors above.")

    cleanup()

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
