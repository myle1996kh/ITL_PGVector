"""Document Processing Service for RAG knowledge base.

This service handles:
- PDF loading and text extraction
- Document chunking with overlap
- Metadata enrichment
- Integration with LangChain document loaders

"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """Service for processing documents for RAG ingestion."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize document processor.

        Args:
            chunk_size: Maximum characters per chunk (default: 1000)
            chunk_overlap: Character overlap between chunks (default: 200)
            separators: Custom split separators (default: paragraph/sentence/word)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Default separators optimized for technical documentation
        self.separators = separators or [
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            " ",     # Words
            ""       # Characters (fallback)
        ]

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=self.separators,
            is_separator_regex=False
        )

        logger.info(
            "document_processor_initialized",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            overlap_percentage=f"{(chunk_overlap/chunk_size)*100:.1f}%"
        )

    def load_pdf(self, pdf_path: str) -> List[Document]:
        """
        Load PDF and return LangChain documents (one per page).

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of Document objects with page_content and metadata

        Metadata includes:
            - source: PDF file path
            - page: Page number (0-indexed)
        """
        try:
            # Validate file exists
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            logger.info("loading_pdf", pdf_path=pdf_path)

            # Load PDF using PyPDFLoader
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()

            logger.info(
                "pdf_loaded_successfully",
                pdf_path=pdf_path,
                page_count=len(documents),
                total_chars=sum(len(doc.page_content) for doc in documents)
            )

            return documents

        except Exception as e:
            logger.error(
                "pdf_load_failed",
                pdf_path=pdf_path,
                error=str(e)
            )
            raise

    def chunk_documents(
        self,
        documents: List[Document],
        add_chunk_metadata: bool = True
    ) -> List[Document]:
        """
        Split documents into smaller chunks.

        Args:
            documents: List of LangChain Document objects
            add_chunk_metadata: Whether to add chunk_index to metadata

        Returns:
            List of chunked Document objects

        Metadata preservation:
            - Original metadata is preserved
            - New metadata added: chunk_index, chunk_total (if add_chunk_metadata=True)
        """
        try:
            logger.info(
                "chunking_documents",
                document_count=len(documents),
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )

            # Split documents
            chunks = self.text_splitter.split_documents(documents)

            # Add chunk metadata
            if add_chunk_metadata:
                chunk_index = 0
                for chunk in chunks:
                    chunk.metadata['chunk_index'] = chunk_index
                    chunk_index += 1

                # Add total chunk count to all chunks
                for chunk in chunks:
                    chunk.metadata['chunk_total'] = len(chunks)

            logger.info(
                "documents_chunked_successfully",
                original_document_count=len(documents),
                chunk_count=len(chunks),
                avg_chunk_size=sum(len(c.page_content) for c in chunks) / len(chunks) if chunks else 0
            )

            return chunks

        except Exception as e:
            logger.error(
                "document_chunking_failed",
                document_count=len(documents),
                error=str(e)
            )
            raise

    def enrich_metadata(
        self,
        documents: List[Document],
        tenant_id: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Add metadata to documents for multi-tenancy and tracking.

        Args:
            documents: List of Document objects
            tenant_id: Tenant UUID
            additional_metadata: Optional extra metadata to add

        Returns:
            Documents with enriched metadata

        Metadata added:
            - tenant_id: For multi-tenant isolation
            - ingested_at: ISO timestamp
            - Any additional_metadata provided
        """
        from datetime import datetime

        try:
            for doc in documents:
                # Add tenant_id (required for isolation)
                doc.metadata['tenant_id'] = tenant_id

                # Add timestamp
                doc.metadata['ingested_at'] = datetime.utcnow().isoformat()

                # Add any additional metadata
                if additional_metadata:
                    for key, value in additional_metadata.items():
                        # Don't override tenant_id
                        if key != 'tenant_id':
                            doc.metadata[key] = value

            logger.debug(
                "metadata_enriched",
                document_count=len(documents),
                tenant_id=tenant_id,
                additional_fields=list(additional_metadata.keys()) if additional_metadata else []
            )

            return documents

        except Exception as e:
            logger.error(
                "metadata_enrichment_failed",
                document_count=len(documents),
                error=str(e)
            )
            raise

    def process_pdf(
        self,
        pdf_path: str,
        tenant_id: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Complete PDF processing pipeline: Load → Chunk → Enrich.

        Args:
            pdf_path: Path to PDF file
            tenant_id: Tenant UUID
            additional_metadata: Optional metadata to add to all chunks

        Returns:
            List of processed Document chunks ready for embedding

        Pipeline:
            1. Load PDF (one Document per page)
            2. Chunk pages into smaller pieces
            3. Enrich metadata (tenant_id, timestamp, custom fields)
        """
        try:
            logger.info(
                "processing_pdf_started",
                pdf_path=pdf_path,
                tenant_id=tenant_id
            )

            # 1. Load PDF
            pages = self.load_pdf(pdf_path)

            # 2. Chunk documents
            chunks = self.chunk_documents(pages, add_chunk_metadata=True)

            # 3. Enrich metadata
            enriched_chunks = self.enrich_metadata(
                chunks,
                tenant_id=tenant_id,
                additional_metadata=additional_metadata
            )

            logger.info(
                "pdf_processing_completed",
                pdf_path=pdf_path,
                tenant_id=tenant_id,
                page_count=len(pages),
                chunk_count=len(enriched_chunks),
                avg_chars_per_chunk=sum(len(c.page_content) for c in enriched_chunks) / len(enriched_chunks)
            )

            return enriched_chunks

        except Exception as e:
            logger.error(
                "pdf_processing_failed",
                pdf_path=pdf_path,
                tenant_id=tenant_id,
                error=str(e)
            )
            raise

    def process_text(
        self,
        text: str,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process raw text (alternative to PDF processing).

        Args:
            text: Raw text content
            tenant_id: Tenant UUID
            metadata: Optional metadata

        Returns:
            List of processed Document chunks
        """
        try:
            logger.info(
                "processing_text_started",
                text_length=len(text),
                tenant_id=tenant_id
            )

            # Create a single document from text
            doc = Document(
                page_content=text,
                metadata=metadata or {}
            )

            # Chunk it
            chunks = self.chunk_documents([doc], add_chunk_metadata=True)

            # Enrich metadata
            enriched_chunks = self.enrich_metadata(
                chunks,
                tenant_id=tenant_id,
                additional_metadata=metadata
            )

            logger.info(
                "text_processing_completed",
                text_length=len(text),
                tenant_id=tenant_id,
                chunk_count=len(enriched_chunks)
            )

            return enriched_chunks

        except Exception as e:
            logger.error(
                "text_processing_failed",
                text_length=len(text),
                tenant_id=tenant_id,
                error=str(e)
            )
            raise


# Singleton instance
_document_processor: Optional[DocumentProcessor] = None


def get_document_processor(
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> DocumentProcessor:
    """
    Get or create document processor singleton.

    Args:
        chunk_size: Chunk size (only used on first call)
        chunk_overlap: Chunk overlap (only used on first call)

    Returns:
        DocumentProcessor instance
    """
    global _document_processor

    if _document_processor is None:
        _document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        logger.info("document_processor_singleton_created")

    return _document_processor
