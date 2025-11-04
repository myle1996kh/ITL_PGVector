"""RAG Service for managing tenant-specific knowledge bases with PgVector.

This service provides:
- Multi-tenant knowledge base management using PostgreSQL + pgvector
- Document ingestion with automatic embedding generation
- Similarity search using cosine distance
- LangChain integration for RAG pipelines
"""
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import DistanceStrategy
from langchain_core.documents import Document
from sqlalchemy import create_engine, text
from src.config import settings
from src.services.embedding_service import get_embedding_service
from src.services.document_processor import get_document_processor
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RAGService:
    """Service for managing PgVector-based knowledge bases with multi-tenant isolation."""

    def __init__(self):
        """
        Initialize RAG Service with PgVector backend.

        Uses:
            - PostgreSQL + pgvector for vector storage
            - LangChain PGVector for vector store operations
            - Sentence-transformers for embeddings (all-MiniLM-L6-v2, 384 dimensions)
        """
        try:
            # Get embedding service (singleton, cached model)
            self.embedding_service = get_embedding_service()

            # Get document processor
            self.doc_processor = get_document_processor()

            # Database connection
            self.connection_string = settings.DATABASE_URL
            self.engine = create_engine(self.connection_string)

            # Collection name (single table for all tenants, isolated by tenant_id)
            self.collection_name = "knowledge_documents"

            logger.info(
                "rag_service_initialized",
                backend="pgvector",
                embedding_model=self.embedding_service.model_name,
                embedding_dimension=self.embedding_service.dimension,
                collection_name=self.collection_name
            )
        except Exception as e:
            logger.error(
                "rag_service_init_failed",
                backend="pgvector",
                error=str(e)
            )
            raise

    def _get_vector_store(self, tenant_id: str) -> PGVector:
        """
        Get PGVector store instance with tenant-specific filtering.

        Args:
            tenant_id: Tenant UUID for isolation

        Returns:
            PGVector instance configured for this tenant

        Note:
            Multi-tenancy is handled via metadata filtering on tenant_id.
            All tenants share the same table but queries are isolated.
        """
        try:
            # Create PGVector store with tenant-specific pre-filter
            vector_store = PGVector(
                embeddings=self.embedding_service,
                collection_name=self.collection_name,
                connection=self.connection_string,
                distance_strategy=DistanceStrategy.COSINE,
                pre_delete_collection=False,  # Don't auto-drop table
                use_jsonb=True  # Use JSONB for metadata
            )

            logger.debug(
                "vector_store_initialized",
                tenant_id=tenant_id,
                collection_name=self.collection_name
            )

            return vector_store

        except Exception as e:
            logger.error(
                "vector_store_init_failed",
                tenant_id=tenant_id,
                error=str(e)
            )
            raise

    def get_collection_name(self, tenant_id: str) -> str:
        """
        Get standardized collection name for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Collection name (now same for all tenants: knowledge_documents)

        Note:
            With PgVector, all tenants share the same table.
            Isolation is via WHERE tenant_id = ? in queries.
        """
        return self.collection_name

    def create_tenant_collection(
        self,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create or get a tenant-specific collection.

        Args:
            tenant_id: Tenant UUID
            metadata: Optional collection metadata (not used in PgVector, kept for API compatibility)

        Returns:
            Dictionary with collection info

        Note:
            In PgVector, collection creation is automatic. This method exists
            for backward compatibility with ChromaDB API.
        """
        collection_name = self.get_collection_name(tenant_id)

        try:
            # Verify database connection
            with self.engine.connect() as conn:
                # Check if pgvector extension exists
                result = conn.execute(text(
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
                ))
                if not result.fetchone():
                    raise RuntimeError("pgvector extension not installed")

            logger.info(
                "tenant_collection_ready",
                tenant_id=tenant_id,
                collection_name=collection_name,
            )

            return {
                "success": True,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
            }

        except Exception as e:
            logger.error(
                "create_tenant_collection_failed",
                tenant_id=tenant_id,
                collection_name=collection_name,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to create collection: {str(e)}",
            }

    def ingest_documents(
        self,
        tenant_id: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest documents into tenant's knowledge base.

        Args:
            tenant_id: Tenant UUID
            documents: List of document texts
            metadatas: Optional list of metadata dicts (one per document)
            ids: Optional list of document IDs (stored in metadata as 'doc_id')

        Returns:
            Dictionary with ingestion results
        """
        collection_name = self.get_collection_name(tenant_id)

        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]

            # Ensure metadatas list exists
            if metadatas is None:
                metadatas = [{} for _ in documents]

            # Add tenant_id and doc_id to all metadata
            for i, metadata in enumerate(metadatas):
                metadata["tenant_id"] = str(tenant_id)
                metadata["doc_id"] = ids[i]
                metadata["ingested_at"] = datetime.utcnow().isoformat()

            # Create LangChain Document objects
            langchain_docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(documents, metadatas)
            ]

            # Get vector store
            vector_store = self._get_vector_store(tenant_id)

            # Add documents to PgVector
            vector_store.add_documents(langchain_docs)

            logger.info(
                "documents_ingested",
                tenant_id=tenant_id,
                collection_name=collection_name,
                document_count=len(documents),
            )

            return {
                "success": True,
                "tenant_id": tenant_id,
                "collection_name": collection_name,
                "document_count": len(documents),
                "document_ids": ids,
            }

        except Exception as e:
            logger.error(
                "ingest_documents_failed",
                tenant_id=tenant_id,
                collection_name=collection_name,
                document_count=len(documents),
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to ingest documents: {str(e)}",
            }

    def query_knowledge_base(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Query tenant's knowledge base using similarity search.

        Args:
            tenant_id: Tenant UUID
            query: Search query
            top_k: Number of results to return

        Returns:
            Dictionary with query results
        """
        collection_name = self.get_collection_name(tenant_id)

        try:
            # Get vector store
            vector_store = self._get_vector_store(tenant_id)

            # Query with tenant_id filter for isolation
            results = vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter={"tenant_id": str(tenant_id)}
            )

            # Format results (results is list of (Document, score) tuples)
            documents = []
            for i, (doc, score) in enumerate(results):
                documents.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "distance": float(score),  # Cosine distance (0 = identical, 2 = opposite)
                    "rank": i + 1,
                })

            logger.info(
                "knowledge_base_queried",
                tenant_id=tenant_id,
                collection_name=collection_name,
                query_length=len(query),
                results_count=len(documents),
            )

            return {
                "success": True,
                "tenant_id": tenant_id,
                "query": query,
                "documents": documents,
                "total_results": len(documents),
            }

        except Exception as e:
            logger.error(
                "query_knowledge_base_failed",
                tenant_id=tenant_id,
                collection_name=collection_name,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to query knowledge base: {str(e)}",
                "documents": [],
            }

    def delete_documents(
        self,
        tenant_id: str,
        document_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Delete documents from tenant's knowledge base.

        Args:
            tenant_id: Tenant UUID
            document_ids: List of document IDs to delete (stored in metadata as 'doc_id')

        Returns:
            Dictionary with deletion results
        """
        collection_name = self.get_collection_name(tenant_id)

        try:
            # Use raw SQL to delete by metadata filter
            # PGVector stores metadata as JSONB, so we filter by tenant_id AND doc_id
            with self.engine.connect() as conn:
                for doc_id in document_ids:
                    result = conn.execute(
                        text("""
                            DELETE FROM langchain_pg_embedding
                            WHERE cmetadata->>'tenant_id' = :tenant_id
                            AND cmetadata->>'doc_id' = :doc_id
                        """),
                        {"tenant_id": str(tenant_id), "doc_id": doc_id}
                    )
                    conn.commit()

            logger.info(
                "documents_deleted",
                tenant_id=tenant_id,
                collection_name=collection_name,
                deleted_count=len(document_ids),
            )

            return {
                "success": True,
                "tenant_id": tenant_id,
                "deleted_count": len(document_ids),
            }

        except Exception as e:
            logger.error(
                "delete_documents_failed",
                tenant_id=tenant_id,
                collection_name=collection_name,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to delete documents: {str(e)}",
            }

    def get_collection_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics for tenant's collection.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Dictionary with collection statistics
        """
        collection_name = self.get_collection_name(tenant_id)

        try:
            # Count documents for this tenant
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT COUNT(*) as count
                        FROM langchain_pg_embedding
                        WHERE cmetadata->>'tenant_id' = :tenant_id
                    """),
                    {"tenant_id": str(tenant_id)}
                )
                count = result.fetchone()[0]

            logger.info(
                "collection_stats_retrieved",
                tenant_id=tenant_id,
                collection_name=collection_name,
                document_count=count,
            )

            return {
                "success": True,
                "tenant_id": tenant_id,
                "collection_name": collection_name,
                "document_count": count,
            }

        except Exception as e:
            logger.error(
                "get_collection_stats_failed",
                tenant_id=tenant_id,
                collection_name=collection_name,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to get collection stats: {str(e)}",
            }

    def ingest_pdf(
        self,
        tenant_id: str,
        pdf_path: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process and ingest a PDF file into tenant's knowledge base.

        Args:
            tenant_id: Tenant UUID
            pdf_path: Path to PDF file
            additional_metadata: Optional metadata to add to all chunks

        Returns:
            Dictionary with ingestion results
        """
        try:
            logger.info(
                "pdf_ingestion_started",
                tenant_id=tenant_id,
                pdf_path=pdf_path
            )

            # Process PDF: Load → Chunk → Enrich
            chunks = self.doc_processor.process_pdf(
                pdf_path=pdf_path,
                tenant_id=tenant_id,
                additional_metadata=additional_metadata
            )

            # Extract texts and metadatas
            documents = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]

            # Ingest into vector store
            result = self.ingest_documents(
                tenant_id=tenant_id,
                documents=documents,
                metadatas=metadatas
            )

            if result["success"]:
                logger.info(
                    "pdf_ingestion_completed",
                    tenant_id=tenant_id,
                    pdf_path=pdf_path,
                    chunk_count=len(chunks)
                )

            return result

        except Exception as e:
            logger.error(
                "pdf_ingestion_failed",
                tenant_id=tenant_id,
                pdf_path=pdf_path,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to ingest PDF: {str(e)}",
            }


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get or create RAG service singleton.

    Returns:
        RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
        logger.info("rag_service_singleton_created")
    return _rag_service
