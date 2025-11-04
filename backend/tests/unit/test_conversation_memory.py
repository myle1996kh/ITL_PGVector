"""Tests for conversation memory manager."""
import pytest
from src.services.conversation_memory import ConversationMemoryManager, get_conversation_history
from src.models.message import Message
from src.models.session import ChatSession
from src.models.tenant import Tenant
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import uuid
from datetime import datetime, timezone


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        tenant_id=uuid.uuid4(),
        name="Test Tenant",
        api_key_hash="test_hash",
        is_active=True
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def test_session(db_session, test_tenant):
    """Create a test chat session."""
    session = ChatSession(
        tenant_id=test_tenant.tenant_id,
        user_id='test-user',
        thread_id='test-thread'
    )
    db_session.add(session)
    db_session.commit()
    return session


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
    import time
    for i in range(5):
        msg = Message(
            session_id=session_id,
            role='user' if i % 2 == 0 else 'assistant',
            content=f'Message {i}'
        )
        db_session.add(msg)
        db_session.flush()  # Ensure different timestamps
        time.sleep(0.01)  # Small delay to ensure timestamp difference
    db_session.commit()

    # Load history
    manager = ConversationMemoryManager(db_session, str(session_id))
    history = manager.get_conversation_history()

    # Verify chronological order (oldest first)
    assert history[0].content == 'Message 0'
    assert history[-1].content == 'Message 4'


def test_session_isolation(db_session, test_tenant):
    """Test that conversation history respects session isolation."""
    # Create two different sessions
    session1 = ChatSession(
        tenant_id=test_tenant.tenant_id,
        user_id='user1',
        thread_id='thread1'
    )
    session2 = ChatSession(
        tenant_id=test_tenant.tenant_id,
        user_id='user2',
        thread_id='thread2'
    )
    db_session.add_all([session1, session2])
    db_session.commit()

    session1_id = session1.session_id
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


def test_filter_system_messages(db_session, test_session):
    """Test that system messages can be filtered out."""
    session_id = test_session.session_id

    # Create mixed messages
    msg1 = Message(session_id=session_id, role='system', content='System message')
    msg2 = Message(session_id=session_id, role='user', content='User message')
    msg3 = Message(session_id=session_id, role='assistant', content='Assistant message')

    db_session.add_all([msg1, msg2, msg3])
    db_session.commit()

    # Load without system messages (default)
    manager = ConversationMemoryManager(db_session, str(session_id))
    history = manager.get_conversation_history(include_system=False)

    assert len(history) == 2
    assert all(not isinstance(msg, SystemMessage) for msg in history)

    # Load with system messages
    history_with_system = manager.get_conversation_history(include_system=True)
    assert len(history_with_system) == 3
    assert isinstance(history_with_system[0], SystemMessage)


def test_get_message_count(db_session, test_session):
    """Test getting message count for a session."""
    session_id = test_session.session_id

    # Initially empty
    manager = ConversationMemoryManager(db_session, str(session_id))
    assert manager.get_message_count() == 0

    # Add some messages
    for i in range(5):
        msg = Message(
            session_id=session_id,
            role='user',
            content=f'Message {i}'
        )
        db_session.add(msg)
    db_session.commit()

    # Check count
    assert manager.get_message_count() == 5


def test_convenience_function(db_session, test_session):
    """Test the convenience function for getting history."""
    session_id = test_session.session_id

    # Add test message
    msg = Message(
        session_id=session_id,
        role='user',
        content='Test message'
    )
    db_session.add(msg)
    db_session.commit()

    # Use convenience function
    history = get_conversation_history(
        db_session,
        str(session_id),
        max_messages=10
    )

    assert len(history) == 1
    assert history[0].content == 'Test message'


def test_unknown_role_handling(db_session, test_session):
    """Test that unknown message roles are handled gracefully."""
    session_id = test_session.session_id

    # Create message with unknown role
    msg1 = Message(session_id=session_id, role='unknown_role', content='Strange message')
    msg2 = Message(session_id=session_id, role='user', content='Normal message')

    db_session.add_all([msg1, msg2])
    db_session.commit()

    # Load history - should skip unknown role
    manager = ConversationMemoryManager(db_session, str(session_id))
    history = manager.get_conversation_history()

    # Should only get the valid message
    assert len(history) == 1
    assert history[0].content == 'Normal message'
