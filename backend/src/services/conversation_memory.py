"""Conversation memory management with intelligent context windowing."""
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.models.message import Message
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConversationMemoryManager:
    """
    Manages conversation history with intelligent context windowing.

    Features:
    - Load history from PostgreSQL messages table
    - Convert to LangChain message format
    - Recency-based windowing
    - Multi-tenant isolation
    - Token-aware context management (future)
    """

    def __init__(self, db: Session, session_id: str):
        """
        Initialize memory manager.

        Args:
            db: Database session
            session_id: Chat session UUID
        """
        self.db = db
        self.session_id = session_id
        logger.debug(
            "memory_manager_initialized",
            session_id=session_id
        )

    def get_conversation_history(
        self,
        max_messages: int = 20,
        include_system: bool = False
    ) -> List[BaseMessage]:
        """
        Load conversation history as LangChain messages.

        Args:
            max_messages: Maximum number of messages to load (default: 20)
            include_system: Whether to include system messages (default: False)

        Returns:
            List of LangChain BaseMessage objects ordered chronologically

        Strategy:
            - Load last N messages from database
            - Filter by role if needed
            - Convert to LangChain message format
            - Order chronologically (oldest first)
        """
        try:
            # Query messages from database
            query = self.db.query(Message).filter(
                Message.session_id == self.session_id
            )

            # Filter out system messages if requested
            if not include_system:
                query = query.filter(Message.role != 'system')

            # Order by timestamp descending and limit
            messages = query.order_by(desc(Message.created_at)).limit(max_messages).all()

            # Reverse to get chronological order (oldest first)
            messages = list(reversed(messages))

            # Convert to LangChain messages
            langchain_messages = []
            for msg in messages:
                langchain_msg = self._convert_to_langchain_message(msg)
                if langchain_msg:
                    langchain_messages.append(langchain_msg)

            logger.info(
                "conversation_history_loaded",
                session_id=self.session_id,
                message_count=len(langchain_messages),
                max_messages=max_messages
            )

            return langchain_messages

        except Exception as e:
            logger.error(
                "conversation_history_load_failed",
                session_id=self.session_id,
                error=str(e)
            )
            # Return empty list on error to not block conversation
            return []

    def _convert_to_langchain_message(self, message: Message) -> Optional[BaseMessage]:
        """
        Convert database Message to LangChain BaseMessage.

        Args:
            message: Database Message object

        Returns:
            LangChain BaseMessage (HumanMessage, AIMessage, or SystemMessage)
        """
        try:
            role = message.role.lower()
            content = message.content

            if role == 'user':
                return HumanMessage(content=content)
            elif role == 'assistant':
                return AIMessage(content=content)
            elif role == 'system':
                return SystemMessage(content=content)
            else:
                logger.warning(
                    "unknown_message_role",
                    role=role,
                    message_id=message.message_id
                )
                return None

        except Exception as e:
            logger.error(
                "message_conversion_failed",
                message_id=message.message_id,
                error=str(e)
            )
            return None

    def get_message_count(self) -> int:
        """
        Get total message count for this session.

        Returns:
            Number of messages in the session
        """
        try:
            count = self.db.query(Message).filter(
                Message.session_id == self.session_id
            ).count()
            return count
        except Exception as e:
            logger.error(
                "message_count_failed",
                session_id=self.session_id,
                error=str(e)
            )
            return 0


def get_conversation_history(
    db: Session,
    session_id: str,
    max_messages: int = 20,
    include_system: bool = False
) -> List[BaseMessage]:
    """
    Convenience function to get conversation history.

    Args:
        db: Database session
        session_id: Chat session UUID
        max_messages: Maximum messages to load
        include_system: Include system messages

    Returns:
        List of LangChain BaseMessage objects
    """
    manager = ConversationMemoryManager(db, session_id)
    return manager.get_conversation_history(max_messages, include_system)
