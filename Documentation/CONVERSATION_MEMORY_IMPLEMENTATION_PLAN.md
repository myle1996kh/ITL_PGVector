# Conversation Memory Implementation Plan

**Document Version**: 1.0
**Date Created**: 2025-11-03
**Status**: Ready for Implementation
**Estimated Effort**: 4-6 hours
**Priority**: HIGH (Critical Bug Fix)

---

## Executive Summary

**Problem**: Chatbot currently has NO conversation memory - agents cannot access previous messages within a session, making multi-turn conversations impossible.

**Root Cause**:
- Messages are saved to PostgreSQL but never retrieved
- `SupervisorAgent` and `DomainAgent` only pass current message to LLM
- No conversation history loaded into LangChain message context

**Solution**: Implement `ConversationMemoryManager` - a hybrid approach using PostgreSQL with intelligent context windowing and optional Redis caching.

**Benefits**:
- ✅ **Multi-turn conversations**: Chatbot remembers previous questions/answers
- ✅ **Token optimization**: Smart windowing prevents context overflow
- ✅ **Persistent memory**: Survives server restarts
- ✅ **Multi-tenant safe**: Leverages existing database isolation
- ✅ **Scalable**: Works with load balancers (shared DB state)
- ✅ **Performance**: Redis caching for hot sessions
- ✅ **Architecture consistency**: Matches pgvector migration approach

---

## Current vs Future Architecture

### Current (Broken Memory)

```
User Message
    ↓
SupervisorAgent._detect_intent()
    ↓
messages = [
    SystemMessage(prompt),
    HumanMessage(current_message)  ← Only current message!
]
    ↓
LLM has NO context of previous conversation
    ↓
Cannot answer "what was my previous question?"
```

### Future (Working Memory)

```
User Message
    ↓
ConversationMemoryManager.get_history(session_id)
    ↓
Load last N messages from PostgreSQL
    ↓
Apply token-aware windowing
    ↓
messages = [
    SystemMessage(prompt),
    *conversation_history,  ← Previous messages!
    HumanMessage(current_message)
]
    ↓
LLM has full conversation context
    ↓
Can answer "my previous question was X"
```

---

## Architecture Design

### Core Component: ConversationMemoryManager

**Location**: `backend/src/services/conversation_memory.py`

**Responsibilities**:
1. Load conversation history from PostgreSQL `messages` table
2. Convert database messages to LangChain `BaseMessage` objects
3. Apply intelligent windowing (recency-based, token-based)
4. Cache hot sessions in Redis
5. Maintain multi-tenant isolation

**Design Principles** (matching existing codebase):
- Database-first (PostgreSQL as source of truth)
- Abstraction layer (agents don't know about DB queries)
- Caching strategy (Redis for performance)
- Observable (structured logging)
- Testable (dependency injection)

---

## Implementation Phases

### Phase 1: Core Memory Manager (2-3 hours) 🎯 HIGH PRIORITY

**Goal**: Fix the memory bug - chatbot can remember conversation history.

#### Step 1.1: Create ConversationMemoryManager Service

**File**: `backend/src/services/conversation_memory.py`

```python
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
```

---

#### Step 1.2: Integrate with SupervisorAgent

**File**: `backend/src/services/supervisor_agent.py`

**Changes**:
1. Pass `session_id` to SupervisorAgent
2. Load conversation history before routing
3. Include history in LLM context

**Modifications**:

```python
# Line 38: Update __init__ signature
def __init__(self, db: Session, tenant_id: str, jwt_token: str, session_id: Optional[str] = None):
    """
    Initialize supervisor agent.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        jwt_token: User JWT token
        session_id: Optional session ID for conversation memory
    """
    self.db = db
    self.tenant_id = tenant_id
    self.jwt_token = jwt_token
    self.session_id = session_id  # ← Add this

    # ... rest of initialization


# Line 164: Update _detect_intent to use conversation history
async def _detect_intent(self, user_message: str, language: str = "en") -> str:
    """
    Detect user intent and determine appropriate agent.

    Args:
        user_message: User's message
        language: Detected user language code (en, vi)

    Returns:
        Agent name or special status (MULTI_INTENT, UNCLEAR)
    """
    from src.services.conversation_memory import get_conversation_history

    # Add language hint to prompt for better routing
    language_hint = f"\nUser's language: {language}. Route appropriately and respond in user's language."

    # Load conversation history if session_id available
    messages = [SystemMessage(content=self.supervisor_prompt + language_hint)]

    if self.session_id:
        history = get_conversation_history(
            self.db,
            self.session_id,
            max_messages=10,  # Last 10 messages for context
            include_system=False
        )
        messages.extend(history)

        logger.debug(
            "supervisor_using_conversation_history",
            session_id=self.session_id,
            history_length=len(history)
        )

    messages.append(HumanMessage(content=user_message))

    response = await self.llm.ainvoke(messages)
    agent_name = response.content.strip()

    logger.debug(
        "intent_detected",
        user_message=user_message[:100],
        detected_agent=agent_name,
        language=language,
        available_agents=[a["name"] for a in self.available_agents],
        tenant_id=self.tenant_id,
        history_used=self.session_id is not None
    )

    return agent_name
```

---

#### Step 1.3: Integrate with DomainAgent

**File**: `backend/src/services/domain_agents.py`

**Changes**:
1. Pass `session_id` to DomainAgent
2. Load conversation history before invoking
3. Include history in LLM context

**Modifications**:

```python
# Line 18: Update __init__ signature
def __init__(
    self,
    db: Session,
    agent_id: str,
    tenant_id: str,
    jwt_token: str,
    session_id: Optional[str] = None  # ← Add this parameter
):
    """
    Initialize domain agent.

    Args:
        db: Database session
        agent_id: Agent UUID
        tenant_id: Tenant UUID
        jwt_token: User JWT token
        session_id: Optional session ID for conversation memory
    """
    self.db = db
    self.agent_id = agent_id
    self.tenant_id = tenant_id
    self.jwt_token = jwt_token
    self.session_id = session_id  # ← Store session_id

    # ... rest of initialization


# Line 181: Update invoke() to use conversation history
async def invoke(self, user_message: str) -> Dict[str, Any]:
    """
    Invoke agent with user message.

    Args:
        user_message: User's message

    Returns:
        Agent response dictionary
    """
    from src.services.conversation_memory import get_conversation_history

    try:
        # Extract intent and entities from user message
        detected_intent, initial_entities = await self._extract_intent_and_entities(user_message)

        # ... (tool loading logic remains same)

        if self.tools:
            # Build system prompt
            system_prompt = self.agent_config.prompt_template
            # ... (tool descriptions logic remains same)

            # Create messages with conversation history
            messages = [SystemMessage(content=system_prompt)]

            # Load conversation history if available
            if self.session_id:
                history = get_conversation_history(
                    self.db,
                    self.session_id,
                    max_messages=15,  # Last 15 messages for domain agents
                    include_system=False
                )
                messages.extend(history)

                logger.debug(
                    "domain_agent_using_history",
                    agent_name=self.agent_config.name,
                    session_id=self.session_id,
                    history_length=len(history)
                )

            # Add current user message
            messages.append(HumanMessage(content=user_message))

            # ... rest of invoke logic
        else:
            # No tools - same pattern
            messages = [SystemMessage(content=self.agent_config.prompt_template)]

            if self.session_id:
                history = get_conversation_history(
                    self.db,
                    self.session_id,
                    max_messages=15,
                    include_system=False
                )
                messages.extend(history)

            messages.append(HumanMessage(content=user_message))
            response = await self.llm.ainvoke(messages)

        # ... rest of method
```

**Update AgentFactory.create_agent()** (Line 462):

```python
@staticmethod
async def create_agent(
    db: Session,
    agent_name: str,
    tenant_id: str,
    jwt_token: str,
    handler_class: str = None,
    session_id: Optional[str] = None  # ← Add this parameter
) -> DomainAgent:
    """
    Create domain agent by name with dynamic class loading.

    Args:
        db: Database session
        agent_name: Name of the agent (e.g., "AgentDebt")
        tenant_id: Tenant UUID
        jwt_token: User JWT token
        handler_class: Optional pre-loaded handler_class path
        session_id: Optional session ID for conversation memory

    Returns:
        Domain agent instance
    """
    # ... (existing logic)

    # Create and return agent instance with session_id
    return AgentClass(db, str(agent_config.agent_id), tenant_id, jwt_token, session_id)
```

---

#### Step 1.4: Update Chat API to Pass session_id

**File**: `backend/src/api/chat.py`

**Changes**: Pass `session_id` when creating agents

**Modifications**:

```python
# Line 87: Update SupervisorAgent initialization
supervisor = SupervisorAgent(
    db=db,
    tenant_id=tenant_id,
    jwt_token=jwt_token,
    session_id=session.session_id  # ← Add session_id
)

# Also update in supervisor_agent.py line 117-123 when calling AgentFactory:
agent = await AgentFactory.create_agent(
    self.db,
    agent_name,
    self.tenant_id,
    self.jwt_token,
    handler_class=handler_class,
    session_id=self.session_id  # ← Add session_id
)
```

**Same changes for test_chat_endpoint** (Line 290).

---

#### Step 1.5: Testing

**File**: `backend/tests/unit/test_conversation_memory.py`

```python
"""Tests for conversation memory manager."""
import pytest
from src.services.conversation_memory import ConversationMemoryManager, get_conversation_history
from src.models.message import Message
from src.models.session import ChatSession
from langchain_core.messages import HumanMessage, AIMessage
import uuid


def test_get_conversation_history_empty(db_session):
    """Test loading history from session with no messages."""
    session_id = str(uuid.uuid4())

    manager = ConversationMemoryManager(db_session, session_id)
    history = manager.get_conversation_history()

    assert history == []


def test_get_conversation_history_with_messages(db_session, test_session):
    """Test loading conversation history with existing messages."""
    session_id = test_session.session_id

    # Create test messages
    msg1 = Message(
        session_id=session_id,
        role='user',
        content='Hello, what is my account balance?'
    )
    msg2 = Message(
        session_id=session_id,
        role='assistant',
        content='Your account balance is $1000'
    )
    msg3 = Message(
        session_id=session_id,
        role='user',
        content='What was my previous question?'
    )

    db_session.add_all([msg1, msg2, msg3])
    db_session.commit()

    # Load history
    manager = ConversationMemoryManager(db_session, str(session_id))
    history = manager.get_conversation_history(max_messages=10)

    # Verify
    assert len(history) == 3
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    assert isinstance(history[2], HumanMessage)
    assert history[0].content == 'Hello, what is my account balance?'
    assert history[2].content == 'What was my previous question?'


def test_max_messages_limit(db_session, test_session):
    """Test that max_messages limit is respected."""
    session_id = test_session.session_id

    # Create 10 messages
    for i in range(10):
        msg = Message(
            session_id=session_id,
            role='user' if i % 2 == 0 else 'assistant',
            content=f'Message {i}'
        )
        db_session.add(msg)
    db_session.commit()

    # Load with limit
    manager = ConversationMemoryManager(db_session, str(session_id))
    history = manager.get_conversation_history(max_messages=5)

    assert len(history) == 5
    # Should get last 5 messages (most recent)
    assert history[-1].content == 'Message 9'


def test_message_ordering(db_session, test_session):
    """Test that messages are ordered chronologically."""
    session_id = test_session.session_id

    # Create messages (will have sequential timestamps)
    messages = []
    for i in range(5):
        msg = Message(
            session_id=session_id,
            role='user' if i % 2 == 0 else 'assistant',
            content=f'Message {i}'
        )
        messages.append(msg)
        db_session.add(msg)
    db_session.commit()

    # Load history
    manager = ConversationMemoryManager(db_session, str(session_id))
    history = manager.get_conversation_history()

    # Verify chronological order (oldest first)
    assert history[0].content == 'Message 0'
    assert history[-1].content == 'Message 4'


def test_tenant_isolation(db_session, test_session):
    """Test that conversation history respects session isolation."""
    # Create two different sessions
    session1_id = test_session.session_id

    session2 = ChatSession(
        tenant_id=test_session.tenant_id,
        user_id='user2',
        thread_id='thread2'
    )
    db_session.add(session2)
    db_session.commit()
    session2_id = session2.session_id

    # Add messages to session 1
    msg1 = Message(session_id=session1_id, role='user', content='Session 1 message')
    db_session.add(msg1)

    # Add messages to session 2
    msg2 = Message(session_id=session2_id, role='user', content='Session 2 message')
    db_session.add(msg2)
    db_session.commit()

    # Load history for session 1
    manager1 = ConversationMemoryManager(db_session, str(session1_id))
    history1 = manager1.get_conversation_history()

    # Load history for session 2
    manager2 = ConversationMemoryManager(db_session, str(session2_id))
    history2 = manager2.get_conversation_history()

    # Verify isolation
    assert len(history1) == 1
    assert len(history2) == 1
    assert history1[0].content == 'Session 1 message'
    assert history2[0].content == 'Session 2 message'
```

---

#### Step 1.6: Integration Testing

**Test Scenario**:
```bash
# Start backend
cd backend
uvicorn src.main:app --reload

# Test conversation memory via Bruno/Postman
POST http://localhost:8000/api/{tenant_id}/test/chat
{
    "message": "Hello, my name is John",
    "user_id": "test-user",
    "session_id": "test-session-123"
}

# Response: greeting

POST http://localhost:8000/api/{tenant_id}/test/chat
{
    "message": "What is my name?",
    "user_id": "test-user",
    "session_id": "test-session-123"  # ← Same session
}

# Expected response: "Your name is John" ✅
```

---

### Phase 2: Token-Aware Windowing (2-3 hours) 🎯 MEDIUM PRIORITY

**Goal**: Optimize token usage to prevent context overflow and reduce LLM costs.

#### Step 2.1: Add Token Counting

**File**: `backend/requirements.txt`

```
tiktoken>=0.5.0
```

**File**: `backend/src/services/conversation_memory.py`

Add token counting capability:

```python
import tiktoken
from typing import Tuple

class ConversationMemoryManager:
    # ... existing code

    def __init__(self, db: Session, session_id: str, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize memory manager.

        Args:
            db: Database session
            session_id: Chat session UUID
            model_name: Model name for token encoding (default: gpt-3.5-turbo)
        """
        self.db = db
        self.session_id = session_id
        self.model_name = model_name

        # Initialize token encoder
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")

        logger.debug(
            "memory_manager_initialized",
            session_id=session_id,
            model_name=model_name
        )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def count_message_tokens(self, message: BaseMessage) -> int:
        """
        Count tokens in a LangChain message.

        Args:
            message: LangChain message

        Returns:
            Approximate token count (content + role overhead)
        """
        # Add 4 tokens for message formatting overhead
        return self.count_tokens(message.content) + 4

    def get_conversation_history(
        self,
        max_messages: int = 20,
        max_tokens: Optional[int] = None,  # ← New parameter
        include_system: bool = False
    ) -> Tuple[List[BaseMessage], int]:
        """
        Load conversation history with token budget management.

        Args:
            max_messages: Maximum number of messages to load
            max_tokens: Maximum token budget for history (optional)
            include_system: Include system messages

        Returns:
            Tuple of (messages list, total token count)

        Strategy:
            1. Load last max_messages from database
            2. If max_tokens specified, trim from oldest until under budget
            3. Always keep at least 2 messages (1 turn)
        """
        try:
            # Query messages
            query = self.db.query(Message).filter(
                Message.session_id == self.session_id
            )

            if not include_system:
                query = query.filter(Message.role != 'system')

            messages = query.order_by(desc(Message.created_at)).limit(max_messages).all()
            messages = list(reversed(messages))

            # Convert to LangChain messages
            langchain_messages = []
            for msg in messages:
                langchain_msg = self._convert_to_langchain_message(msg)
                if langchain_msg:
                    langchain_messages.append(langchain_msg)

            # Apply token budget if specified
            if max_tokens:
                langchain_messages, total_tokens = self._apply_token_budget(
                    langchain_messages,
                    max_tokens
                )
            else:
                total_tokens = sum(
                    self.count_message_tokens(msg) for msg in langchain_messages
                )

            logger.info(
                "conversation_history_loaded",
                session_id=self.session_id,
                message_count=len(langchain_messages),
                total_tokens=total_tokens,
                max_messages=max_messages,
                max_tokens=max_tokens
            )

            return langchain_messages, total_tokens

        except Exception as e:
            logger.error(
                "conversation_history_load_failed",
                session_id=self.session_id,
                error=str(e)
            )
            return [], 0

    def _apply_token_budget(
        self,
        messages: List[BaseMessage],
        max_tokens: int
    ) -> Tuple[List[BaseMessage], int]:
        """
        Trim messages to fit within token budget.

        Strategy: Remove oldest messages first, keep at least 2 messages (1 turn).

        Args:
            messages: List of messages (chronological order)
            max_tokens: Maximum token budget

        Returns:
            Tuple of (trimmed messages, actual token count)
        """
        if not messages:
            return [], 0

        # Always keep at least 2 messages (1 conversation turn)
        min_messages = min(2, len(messages))

        # Count tokens from newest to oldest
        total_tokens = 0
        included_messages = []

        # Iterate from newest (end of list) to oldest
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            msg_tokens = self.count_message_tokens(msg)

            # Check if adding this message exceeds budget
            if total_tokens + msg_tokens > max_tokens:
                # Only stop if we have minimum messages
                if len(included_messages) >= min_messages:
                    break

            included_messages.insert(0, msg)  # Insert at beginning to maintain order
            total_tokens += msg_tokens

        logger.debug(
            "token_budget_applied",
            original_count=len(messages),
            trimmed_count=len(included_messages),
            total_tokens=total_tokens,
            max_tokens=max_tokens
        )

        return included_messages, total_tokens
```

#### Step 2.2: Update Agent Integration

Update `SupervisorAgent` and `DomainAgent` to use token budgets:

```python
# supervisor_agent.py
history, token_count = manager.get_conversation_history(
    max_messages=10,
    max_tokens=1500  # Reserve 1500 tokens for history
)

# domain_agents.py
history, token_count = manager.get_conversation_history(
    max_messages=15,
    max_tokens=2000  # Domain agents get more context
)

logger.debug(
    "conversation_context_tokens",
    session_id=self.session_id,
    history_tokens=token_count,
    message_count=len(history)
)
```

#### Step 2.3: Configuration

Add to `backend/src/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings

    # Conversation Memory Settings
    MEMORY_MAX_MESSAGES: int = Field(default=20)
    MEMORY_MAX_TOKENS_SUPERVISOR: int = Field(default=1500)
    MEMORY_MAX_TOKENS_DOMAIN: int = Field(default=2000)
    MEMORY_TOKEN_MODEL: str = Field(default="gpt-3.5-turbo")
```

#### Step 2.4: Testing

**File**: `backend/tests/unit/test_memory_tokens.py`

```python
def test_token_counting():
    """Test token counting accuracy."""
    manager = ConversationMemoryManager(db_session, session_id)

    text = "Hello, how are you?"
    tokens = manager.count_tokens(text)
    assert tokens > 0
    assert tokens < 10  # Approximate


def test_token_budget_enforcement():
    """Test that token budget is enforced."""
    # Create session with many messages
    for i in range(20):
        msg = Message(
            session_id=session_id,
            role='user' if i % 2 == 0 else 'assistant',
            content='This is a test message ' * 20  # ~100 tokens each
        )
        db_session.add(msg)
    db_session.commit()

    # Load with tight budget
    manager = ConversationMemoryManager(db_session, session_id)
    history, total_tokens = manager.get_conversation_history(
        max_messages=20,
        max_tokens=500  # Only allow ~5 messages
    )

    assert total_tokens <= 500
    assert len(history) < 20
    assert len(history) >= 2  # At least 1 turn preserved
```

---

### Phase 3: Redis Caching (1-2 hours) 🎯 LOW PRIORITY

**Goal**: Cache conversation history in Redis for hot sessions to reduce database load.

#### Step 3.1: Add Caching Logic

**File**: `backend/src/services/conversation_memory.py`

```python
from typing import Optional
from redis import asyncio as aioredis
import json

class ConversationMemoryManager:
    # ... existing code

    def __init__(
        self,
        db: Session,
        session_id: str,
        model_name: str = "gpt-3.5-turbo",
        redis_client: Optional[aioredis.Redis] = None
    ):
        """Initialize with optional Redis cache."""
        self.db = db
        self.session_id = session_id
        self.model_name = model_name
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour

        # ... rest of init

    async def get_conversation_history_cached(
        self,
        max_messages: int = 20,
        max_tokens: Optional[int] = None,
        include_system: bool = False
    ) -> Tuple[List[BaseMessage], int]:
        """
        Load conversation history with Redis caching.

        Cache key: history:{session_id}:{max_messages}:{max_tokens}
        TTL: 1 hour
        """
        if not self.redis:
            # No Redis, fall back to DB query
            return self.get_conversation_history(max_messages, max_tokens, include_system)

        # Build cache key
        cache_key = f"history:{self.session_id}:{max_messages}:{max_tokens}"

        try:
            # Try to get from cache
            cached = await self.redis.get(cache_key)
            if cached:
                # Deserialize and convert back to LangChain messages
                data = json.loads(cached)
                messages = self._deserialize_messages(data['messages'])

                logger.debug(
                    "conversation_history_cache_hit",
                    session_id=self.session_id,
                    cache_key=cache_key
                )

                return messages, data['total_tokens']
        except Exception as e:
            logger.warning(
                "cache_read_failed",
                session_id=self.session_id,
                error=str(e)
            )

        # Cache miss or error - load from database
        messages, total_tokens = self.get_conversation_history(
            max_messages, max_tokens, include_system
        )

        # Store in cache
        try:
            cache_data = {
                'messages': self._serialize_messages(messages),
                'total_tokens': total_tokens
            }
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(cache_data)
            )

            logger.debug(
                "conversation_history_cached",
                session_id=self.session_id,
                cache_key=cache_key,
                message_count=len(messages)
            )
        except Exception as e:
            logger.warning(
                "cache_write_failed",
                session_id=self.session_id,
                error=str(e)
            )

        return messages, total_tokens

    def _serialize_messages(self, messages: List[BaseMessage]) -> List[dict]:
        """Serialize LangChain messages to JSON-compatible format."""
        return [
            {
                'type': type(msg).__name__,
                'content': msg.content
            }
            for msg in messages
        ]

    def _deserialize_messages(self, data: List[dict]) -> List[BaseMessage]:
        """Deserialize JSON data to LangChain messages."""
        messages = []
        for item in data:
            msg_type = item['type']
            content = item['content']

            if msg_type == 'HumanMessage':
                messages.append(HumanMessage(content=content))
            elif msg_type == 'AIMessage':
                messages.append(AIMessage(content=content))
            elif msg_type == 'SystemMessage':
                messages.append(SystemMessage(content=content))

        return messages

    async def invalidate_cache(self):
        """Invalidate cache when new message is added."""
        if not self.redis:
            return

        try:
            # Delete all cache keys for this session
            pattern = f"history:{self.session_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)

            logger.debug(
                "cache_invalidated",
                session_id=self.session_id,
                keys_deleted=len(keys)
            )
        except Exception as e:
            logger.warning(
                "cache_invalidation_failed",
                session_id=self.session_id,
                error=str(e)
            )
```

#### Step 3.2: Update Chat API

**File**: `backend/src/api/chat.py`

```python
from src.config import get_redis

# After saving assistant message (line 121)
db.commit()

# Invalidate cache since conversation history changed
try:
    redis = await get_redis().__anext__()
    from src.services.conversation_memory import ConversationMemoryManager
    memory = ConversationMemoryManager(db, session.session_id, redis_client=redis)
    await memory.invalidate_cache()
except Exception as e:
    logger.warning("cache_invalidation_failed", error=str(e))
```

---

### Phase 4: Monitoring & Optimization (Ongoing)

#### Metrics to Track

Add to logging:

```python
logger.info(
    "conversation_memory_metrics",
    session_id=session_id,
    total_messages=total_messages,
    loaded_messages=len(history),
    total_tokens=token_count,
    cache_hit=cache_hit,
    db_query_ms=query_duration,
    strategy="token_budget"  # or "recency"
)
```

#### Database Indexes

Ensure optimal query performance:

```sql
-- Already exists, verify:
CREATE INDEX idx_messages_session_timestamp
ON messages (session_id, timestamp DESC);

-- Check query performance:
EXPLAIN ANALYZE
SELECT * FROM messages
WHERE session_id = 'uuid-here'
ORDER BY timestamp DESC
LIMIT 20;
```

---

## Success Criteria

✅ **Phase 1 Complete**:
- ConversationMemoryManager implemented
- SupervisorAgent uses conversation history
- DomainAgent uses conversation history
- Chat API passes session_id
- Integration tests pass
- Chatbot can answer "what was my previous question?"

✅ **Phase 2 Complete**:
- Token counting implemented
- Token budget enforced
- Tests verify token limits
- Configuration added

✅ **Phase 3 Complete**:
- Redis caching implemented
- Cache invalidation works
- Performance improved for active sessions

**Performance Targets**:
- Memory load latency: <20ms from cache, <100ms from database
- Token budget: 1500-2000 tokens for history (reasonable context)
- Cache hit rate: >80% for active sessions

**Verification**:
```bash
# Test multi-turn conversation
curl -X POST http://localhost:8000/api/{tenant}/test/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is Alice",
    "user_id": "test",
    "session_id": "test-123"
  }'

curl -X POST http://localhost:8000/api/{tenant}/test/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my name?",
    "user_id": "test",
    "session_id": "test-123"
  }'

# Expected: "Your name is Alice" ✅
```

---

## Timeline Estimate

| Phase | Estimated Time | Priority |
|-------|---------------|----------|
| Phase 1: Core Memory Manager | 2-3 hours | HIGH 🔥 |
| Phase 2: Token Windowing | 2-3 hours | MEDIUM |
| Phase 3: Redis Caching | 1-2 hours | LOW |
| Phase 4: Monitoring | Ongoing | MEDIUM |

**Sequential (worst case)**: 6-8 hours
**Optimized (Phase 1 only)**: **2-3 hours** ← Start here!

---

## Rollback Plan

If issues arise:

1. **Immediate rollback**: Set `max_messages=0` in config (disables history)
2. **Code rollback**: Revert commits
3. **Database**: No schema changes, safe to rollback
4. **Cache**: Clear Redis cache: `FLUSHDB`

---

## Next Steps

### Immediate Actions (Phase 1 - Critical)

1. ✅ Review this plan
2. ✅ Create `backend/src/services/conversation_memory.py`
3. ✅ Update `SupervisorAgent.__init__` and `_detect_intent`
4. ✅ Update `DomainAgent.__init__` and `invoke`
5. ✅ Update `AgentFactory.create_agent`
6. ✅ Update `chat.py` to pass `session_id`
7. ✅ Write unit tests
8. ✅ Run integration tests
9. ✅ Deploy to staging
10. ✅ Verify multi-turn conversations work

### Future Enhancements (Phase 2-4)

- Token-aware windowing
- Redis caching
- Semantic filtering (using pgvector!)
- Conversation summarization
- Analytics dashboard

---

## References

**Internal Documentation**:
- [System Architecture](02_SYSTEM_ARCHITECTURE.md)
- [Database Schema](04_DATABASE_SCHEMA_ERD.md)
- [pgvector Migration Plan](PGVECTOR_MIGRATION_PLAN.md)

**LangChain Resources**:
- [Message History](https://python.langchain.com/docs/modules/memory/chat_messages/)
- [Custom Memory](https://python.langchain.com/docs/modules/memory/custom_memory)
- [Token Counting](https://github.com/openai/tiktoken)

**Files to Modify**:
- `backend/src/services/conversation_memory.py` (NEW)
- `backend/src/services/supervisor_agent.py` (update)
- `backend/src/services/domain_agents.py` (update)
- `backend/src/api/chat.py` (update)
- `backend/tests/unit/test_conversation_memory.py` (NEW)
- `backend/requirements.txt` (add tiktoken)

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: 2025-11-03
**Prepared By**: Architecture & LangChain Expert Team
**Approved By**: Pending developer review
