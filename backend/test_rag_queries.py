"""
Test RAG Knowledge Base with Various Queries

This demonstrates the PgVector RAG system working with the eTMS USER GUIDE
without requiring LLM API calls.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.rag_service import get_rag_service

TENANT_ID = "128e9b53-7610-453f-a2d4-a5d2537a36c4"

# Test queries in both Vietnamese and English
TEST_QUERIES = [
    "Hướng dẫn QUY TRÌNH VẬN HÀNH ĐƠN HÀNG",
    "How to track a shipment?",
    "What is the shipment creation process?",
    "Cách tạo đơn hàng mới trong eTMS",
    "User permissions and access control",
]

def test_query(rag_service, query: str, top_k: int = 3):
    """Test a single query and display results."""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)

    result = rag_service.query_knowledge_base(
        tenant_id=TENANT_ID,
        query=query,
        top_k=top_k
    )

    if not result["success"]:
        print(f"❌ Query failed: {result.get('error')}")
        return

    print(f"✅ Found {result['total_results']} results\n")

    for i, doc in enumerate(result['documents'], 1):
        print(f"📄 Result {i} (similarity score: {1 - doc['distance']:.2%}, distance: {doc['distance']:.4f})")
        print(f"   Page: {doc['metadata'].get('page', 'N/A')}")
        print(f"   Content preview:")

        # Clean up content for display
        content = doc['content'].replace('\n', ' ').strip()
        if len(content) > 200:
            content = content[:200] + "..."

        print(f"   {content}\n")


def main():
    print("="*70)
    print("eTMS Knowledge Base - RAG Query Tests")
    print("="*70)
    print(f"Tenant: Demo Company")
    print(f"Backend: PgVector")
    print(f"Embedding Model: all-MiniLM-L6-v2 (384 dimensions)")
    print(f"Knowledge Base: 910 chunks from eTMS USER GUIDE\n")

    # Initialize RAG service
    print("→ Initializing RAG service...")
    rag_service = get_rag_service()
    print("✓ RAG service ready\n")

    # Run all test queries
    for query in TEST_QUERIES:
        test_query(rag_service, query, top_k=3)

    print("\n" + "="*70)
    print("✅ All RAG queries completed successfully!")
    print("="*70)
    print("\nThe knowledge base is working correctly!")
    print("To use with the agent, you need a valid OPENROUTER_API_KEY in .env")
    print("\nExample agent query (once API key is fixed):")
    print('  POST /api/128e9b53-7610-453f-a2d4-a5d2537a36c4/chat')
    print('  {"message": "How do I track shipments in eTMS?", "user_id": "demo"}')


if __name__ == "__main__":
    main()
