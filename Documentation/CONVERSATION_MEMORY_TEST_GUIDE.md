# Conversation Memory Integration Test Guide

**Date**: 2025-11-03
**Status**: Phase 1 Implementation Complete

---

## ✅ Implementation Summary

### Files Created:
1. **`backend/src/services/conversation_memory.py`** - ConversationMemoryManager service
2. **`backend/tests/unit/test_conversation_memory.py`** - Unit tests (need db_session fixture)
3. **This test guide**

### Files Modified:
1. **`backend/src/services/supervisor_agent.py`**
   - Added `session_id` parameter to `__init__`
   - Updated `_detect_intent()` to load conversation history
   - Passed `session_id` to `AgentFactory.create_agent()`

2. **`backend/src/services/domain_agents.py`**
   - Added `session_id` parameter to `DomainAgent.__init__`
   - Updated `invoke()` to load conversation history (both with tools and without tools)
   - Updated `AgentFactory.create_agent()` signature and implementation

3. **`backend/src/api/chat.py`**
   - Updated both `chat_endpoint` and `test_chat_endpoint` to pass `session_id` to SupervisorAgent

---

## 🧪 Integration Testing

### Test Scenario 1: Basic Conversation Memory

**Objective**: Verify chatbot remembers user's name across messages.

#### Step 1: Start Backend

```bash
cd backend
.\venv\Scripts\python.exe -m uvicorn src.main:app --reload
```

#### Step 2: First Message - Introduce Yourself

**Request** (using Bruno/Postman/curl):
```http
POST http://localhost:8000/api/{tenant_id}/test/chat
Content-Type: application/json

{
    "message": "Hello, my name is Alice",
    "user_id": "test-user",
    "session_id": "test-session-memory-001"
}
```

**Expected Response**:
- Status: 200 OK
- Response contains greeting acknowledging the name

#### Step 3: Second Message - Test Memory

**Request**:
```http
POST http://localhost:8000/api/{tenant_id}/test/chat
Content-Type: application/json

{
    "message": "What is my name?",
    "user_id": "test-user",
    "session_id": "test-session-memory-001"  ← Same session!
}
```

**Expected Response ✅**:
- Status: 200 OK
- Response should say: "Your name is Alice" or similar
- **This proves conversation memory works!**

---

### Test Scenario 2: Previous Question Memory

**Objective**: Verify chatbot can recall previous questions.

#### Step 1: Ask First Question

```http
POST http://localhost:8000/api/{tenant_id}/test/chat
Content-Type: application/json

{
    "message": "What is the weather like?",
    "user_id": "test-user-2",
    "session_id": "test-session-memory-002"
}
```

#### Step 2: Ask About Previous Question

```http
POST http://localhost:8000/api/{tenant_id}/test/chat
Content-Type: application/json

{
    "message": "What was my previous question?",
    "user_id": "test-user-2",
    "session_id": "test-session-memory-002"  ← Same session!
}
```

**Expected Response ✅**:
- Should mention "weather" or reference the previous question

---

### Test Scenario 3: Session Isolation

**Objective**: Verify different sessions don't share memory.

#### Setup: Create two sessions with different names

**Session A**:
```json
{
    "message": "My name is Bob",
    "user_id": "user-a",
    "session_id": "session-a"
}
```

**Session B**:
```json
{
    "message": "My name is Carol",
    "user_id": "user-b",
    "session_id": "session-b"
}
```

#### Test: Ask names in each session

**Session A - Ask Name**:
```json
{
    "message": "What is my name?",
    "user_id": "user-a",
    "session_id": "session-a"
}
```

**Expected**: "Bob" ✅

**Session B - Ask Name**:
```json
{
    "message": "What is my name?",
    "user_id": "user-b",
    "session_id": "session-b"
}
```

**Expected**: "Carol" ✅ (NOT "Bob" - proves isolation)

---

### Test Scenario 4: Long Conversation

**Objective**: Test max_messages windowing.

#### Setup: Have a 20-message conversation

Send 20 messages in the same session:
- Messages 1-10: Various questions
- Messages 11-15: Technical questions
- Message 16: "What was my first question?"

**Expected Behavior**:
- If max_messages=15 (domain agents), should remember back 15 messages
- If max_messages=10 (supervisor), should remember back 10 messages
- Older messages should be dropped (gracefully)

---

## 🔍 Verification Checklist

### Code Review Checklist:

- [x] `ConversationMemoryManager` created
- [x] `SupervisorAgent` loads conversation history
- [x] `DomainAgent` loads conversation history
- [x] `AgentFactory` passes session_id
- [x] Chat API passes session_id
- [x] Unit tests written (need fixtures)

### Runtime Verification:

Use these commands to verify implementation:

```bash
# 1. Check that conversation_memory.py exists
ls backend/src/services/conversation_memory.py

# 2. Grep for session_id usage in agents
grep -n "session_id" backend/src/services/supervisor_agent.py
grep -n "session_id" backend/src/services/domain_agents.py
grep -n "session_id" backend/src/api/chat.py

# 3. Check imports
grep -n "conversation_memory" backend/src/services/supervisor_agent.py
grep -n "conversation_memory" backend/src/services/domain_agents.py
```

### Database Verification:

```sql
-- Check messages are being saved
SELECT session_id, role, content, created_at
FROM messages
WHERE session_id = 'test-session-memory-001'
ORDER BY created_at DESC;

-- Check message count per session
SELECT session_id, COUNT(*) as message_count
FROM messages
GROUP BY session_id;
```

### Log Verification:

Look for these log entries in backend output:

```
INFO conversation_history_loaded session_id=xxx message_count=X
DEBUG supervisor_using_conversation_history session_id=xxx history_length=X
DEBUG domain_agent_using_history agent_name=xxx session_id=xxx history_length=X
```

---

## 🐛 Troubleshooting

### Issue: "AttributeError: 'SupervisorAgent' object has no attribute 'session_id'"

**Cause**: SupervisorAgent not updated
**Fix**: Verify `self.session_id = session_id` in `__init__`

### Issue: Chatbot still doesn't remember

**Debugging Steps**:

1. **Check session_id is same**:
   ```python
   # In logs, verify same session_id
   logger.info("Session ID", session_id=session.session_id)
   ```

2. **Check messages are saved**:
   ```sql
   SELECT * FROM messages WHERE session_id = 'your-session-id';
   ```

3. **Check history is loaded**:
   - Look for `conversation_history_loaded` log
   - Check `message_count > 0`

4. **Check LLM receives history**:
   - Add debug logging in `_detect_intent` / `invoke`
   - Print `len(messages)` before calling LLM

### Issue: "ImportError: cannot import name 'get_conversation_history'"

**Cause**: Import path issue
**Fix**: Verify import statement:
```python
from src.services.conversation_memory import get_conversation_history
```

---

## 📊 Performance Monitoring

### Metrics to Track:

1. **History Load Time**:
   - Expected: <100ms from database
   - Watch for slow queries if session has 1000+ messages

2. **Token Usage**:
   - Phase 1: No token budget (loads all max_messages)
   - Future Phase 2: Token-aware windowing

3. **Memory Overhead**:
   - Each session history: ~1-5KB in memory
   - Cleared after request completes

### Optimization Opportunities:

- [ ] Add Redis caching (Phase 3)
- [ ] Token-aware windowing (Phase 2)
- [ ] Database query optimization
- [ ] Lazy loading for very long conversations

---

## ✅ Success Criteria

**Phase 1 is successful if**:

1. ✅ Multi-turn conversations work (chatbot remembers context)
2. ✅ Session isolation maintained (different sessions don't cross-contaminate)
3. ✅ No errors in production logs
4. ✅ Performance acceptable (<2.5s response time including memory load)
5. ✅ Can answer "what was my previous question?" correctly

**Test with real tenant**:
```bash
# Use actual tenant_id from database
POST http://localhost:8000/api/2628802d-1dff-4a98-9325-704433c5d3ab/test/chat

{
    "message": "Test conversation memory",
    "user_id": "real-user",
    "session_id": "real-session-123"
}
```

---

## 🚀 Next Steps (Phase 2 & 3)

### Phase 2: Token-Aware Windowing

**Goal**: Optimize token usage
**Files to modify**:
- `conversation_memory.py` - Add `tiktoken` support
- Add `max_tokens` parameter
- Implement smart windowing

**Test**: Conversation with 50 messages should still fit in token budget

### Phase 3: Redis Caching

**Goal**: Performance optimization
**Files to modify**:
- `conversation_memory.py` - Add Redis caching layer
- `chat.py` - Cache invalidation on new message

**Test**: Cache hit rate >80% for active sessions

---

## 📝 Notes

**Current Configuration**:
- `max_messages` for SupervisorAgent: 10
- `max_messages` for DomainAgent: 15
- `include_system`: False (system messages filtered out)

**Known Limitations (Phase 1)**:
- No token budgeting (could exceed context window with very long conversations)
- No caching (loads from DB every time)
- No summarization (old messages just dropped)

**Future Enhancements**:
- Semantic memory (using pgvector!)
- Conversation summarization
- Multi-modal memory (images, files)
- Analytics dashboard

---

**Document Status**: ✅ Ready for Testing
**Last Updated**: 2025-11-03
**Phase**: Phase 1 Complete
**Next Phase**: Token-Aware Windowing (Phase 2)
