"""
Demonstrate RAG Flow: Query → Similar Data → LLM Context

This shows the complete RAG pipeline:
1. User query
2. Retrieve similar chunks from PgVector
3. Format context for LLM
4. (Would send to LLM to generate answer)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.rag_service import get_rag_service

TENANT_ID = "128e9b53-7610-453f-a2d4-a5d2537a36c4"

def demo_rag_flow(query: str):
    """Demonstrate complete RAG flow."""

    print("="*70)
    print("RAG FLOW DEMONSTRATION")
    print("="*70)
    print(f"\n👤 User Query: {query}\n")

    # STEP 1: Get RAG service
    print("📊 STEP 1: Initializing RAG Service...")
    rag_service = get_rag_service()
    print("✓ Service ready\n")

    # STEP 2: Query knowledge base (retrieve similar chunks)
    print("🔍 STEP 2: Searching knowledge base for similar content...")
    result = rag_service.query_knowledge_base(
        tenant_id=TENANT_ID,
        query=query,
        top_k=3  # Get top 3 most similar chunks
    )

    if not result["success"]:
        print(f"❌ Search failed: {result.get('error')}")
        return

    print(f"✓ Found {result['total_results']} relevant chunks\n")

    # STEP 3: Extract and format retrieved context
    print("📝 STEP 3: Retrieved Context (what we send to LLM):")
    print("-"*70)

    context_chunks = []
    for i, doc in enumerate(result['documents'], 1):
        similarity_score = 1 - doc['distance']
        page = doc['metadata'].get('page', 'N/A')
        content = doc['content'].strip()

        print(f"\n[Chunk {i}] (Similarity: {similarity_score:.2%}, Page: {page})")
        print(f"{content[:300]}...")
        print()

        context_chunks.append(content)

    # STEP 4: Format prompt for LLM
    print("="*70)
    print("🤖 STEP 4: Formatted Prompt for LLM:")
    print("="*70)

    # This is what would be sent to the LLM (OpenRouter/GPT-4/etc)
    context = "\n\n---\n\n".join(context_chunks)

    llm_prompt = f"""You are an eTMS (Enterprise Transport Management System) guidance assistant.

Use the following context from the eTMS USER GUIDE to answer the user's question.
If the answer is not in the context, say you don't have that information.

CONTEXT FROM eTMS USER GUIDE:
{context}

USER QUESTION: {query}

ANSWER (in Vietnamese if the question is in Vietnamese):"""

    print(llm_prompt)
    print("\n" + "="*70)

    # STEP 5: What would happen next (if we had valid API key)
    print("\n💡 STEP 5: What Happens Next (requires LLM API):")
    print("-"*70)
    print("1. Send the prompt above to LLM (OpenRouter/GPT-4/Claude)")
    print("2. LLM reads the context chunks")
    print("3. LLM generates an accurate answer based on the eTMS docs")
    print("4. Return structured response to user")
    print("\nWith a valid OPENROUTER_API_KEY, AgentGuidance would:")
    print("  • Receive: User query")
    print("  • Search: PgVector knowledge base")
    print("  • Retrieve: Top 5 relevant chunks")
    print("  • Generate: Contextual answer using LLM")
    print("  • Return: Accurate, grounded response")

    print("\n" + "="*70)
    print("✅ RAG Flow Complete!")
    print("="*70)


if __name__ == "__main__":
    # Test with Vietnamese query
    query = "Hướng dẫn QUY TRÌNH VẬN HÀNH ĐƠN HÀNG"
    demo_rag_flow(query)

    print("\n\n")

    # Test with English query
    query2 = "How to create a new order in eTMS?"
    demo_rag_flow(query2)
