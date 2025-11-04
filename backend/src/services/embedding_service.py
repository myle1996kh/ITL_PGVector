"""Embedding Service for centralized embedding generation.

This service provides:
- Singleton pattern for model caching
- Support for multiple embedding models
- Consistent embedding generation across the application
- Integration with PgVector and LangChain

"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model.

        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
                       - all-MiniLM-L6-v2: 384 dimensions, fast, good quality
                       - all-mpnet-base-v2: 768 dimensions, slower, best quality
        """
        self.model_name = model_name

        try:
            logger.info("embedding_service_initializing", model_name=model_name)

            # Load model (cached in memory)
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()

            logger.info(
                "embedding_service_initialized",
                model_name=model_name,
                dimension=self.dimension
            )

        except Exception as e:
            logger.error(
                "embedding_service_init_failed",
                model_name=model_name,
                error=str(e)
            )
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()

        except Exception as e:
            logger.error(
                "embed_text_failed",
                text_length=len(text),
                error=str(e)
            )
            raise

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched for efficiency).

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch

        Returns:
            List of embedding vectors
        """
        try:
            logger.debug(
                "embed_texts_started",
                text_count=len(texts),
                batch_size=batch_size
            )

            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            logger.debug(
                "embed_texts_completed",
                text_count=len(texts),
                embedding_dimension=self.dimension
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(
                "embed_texts_failed",
                text_count=len(texts),
                error=str(e)
            )
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents (LangChain compatibility).

        This is an alias for embed_texts() to match the LangChain Embeddings interface.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embed_texts(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query (LangChain compatibility).

        This is an alias for embed_text() to match the LangChain Embeddings interface.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return self.embed_text(text)

    def get_dimension(self) -> int:
        """
        Get embedding dimension for this model.

        Returns:
            Integer dimension (e.g., 384 for all-MiniLM-L6-v2)
        """
        return self.dimension


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """
    Get or create embedding service singleton.

    Args:
        model_name: HuggingFace model name (only used on first call)

    Returns:
        EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name=model_name)
        logger.info(
            "embedding_service_singleton_created",
            model_name=model_name,
            dimension=_embedding_service.dimension
        )

    return _embedding_service


def reset_embedding_service():
    """
    Reset singleton (useful for testing or model switching).

    Warning: This will reload the model, which takes time.
    """
    global _embedding_service
    _embedding_service = None
    logger.warning("embedding_service_singleton_reset")
