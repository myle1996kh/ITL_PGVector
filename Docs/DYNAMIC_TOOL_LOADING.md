# Dynamic Tool Loading Implementation Guide

## 📋 Overview

This document explains how to implement dynamic tool loading to allow adding new tool types without redeployment.

**Current Status**: Tools use a hardcoded registry (security whitelist)
**Goal**: Enable dynamic loading like agents already have
**Benefit**: Add new tool types via database without code changes

---

## 🎯 Option 1: Simple Dynamic Loading (Recommended)

### Files to Change: **1 file only**

#### File: `backend/src/services/tool_loader.py`

**Change 1: Add dynamic import method**

Add this method to the `ToolRegistry` class (around line 29):

```python
def _get_handler_class(self, handler_class_path: str):
    """
    Dynamically import handler class from path.

    Args:
        handler_class_path: Python path like "tools.http.HTTPGetTool"

    Returns:
        The imported handler class

    Raises:
        ValueError: If handler class cannot be imported
    """
    try:
        # Split path: "tools.http.HTTPGetTool" -> ("tools.http", "HTTPGetTool")
        module_path, class_name = handler_class_path.rsplit(".", 1)

        # Dynamic import: src.tools.http
        module = __import__(f"src.{module_path}", fromlist=[class_name])

        # Get class from module
        handler_class = getattr(module, class_name)

        logger.info(
            "tool_handler_loaded",
            handler_path=handler_class_path,
            class_name=class_name
        )

        return handler_class

    except (ImportError, AttributeError, ValueError) as e:
        logger.error(
            "tool_handler_import_failed",
            handler_path=handler_class_path,
            error=str(e)
        )
        raise ValueError(
            f"Tool handler not found: {handler_class_path}. "
            f"Ensure the handler class exists and is importable."
        ) from e
```

**Change 2: Replace hardcoded lookup**

Find line 77 (in `create_tool_from_db` method):

```python
# OLD (line 77):
handler_class = self._tool_handlers.get(base_tool.handler_class)

# NEW:
handler_class = self._get_handler_class(base_tool.handler_class)
```

**Change 3: Remove or comment out hardcoded registry** (Optional, for cleanup)

Lines 21-28 can be removed or kept as fallback:

```python
# OPTION A: Remove entirely
# def __init__(self):
#     self._cache: Dict[str, StructuredTool] = {}
#     # No more hardcoded registry!

# OPTION B: Keep as fallback (hybrid approach)
def __init__(self):
    self._cache: Dict[str, StructuredTool] = {}
    self._tool_handlers = {
        "tools.http.HTTPGetTool": HTTPGetTool,
        "tools.http.HTTPPostTool": HTTPPostTool,
        "tools.rag.RAGTool": RAGTool,
    }

# Then in _get_handler_class, try registry first, then dynamic import
def _get_handler_class(self, handler_class_path: str):
    # Try hardcoded registry first (fast path)
    if handler_class_path in self._tool_handlers:
        return self._tool_handlers[handler_class_path]

    # Fallback to dynamic import
    try:
        module_path, class_name = handler_class_path.rsplit(".", 1)
        module = __import__(f"src.{module_path}", fromlist=[class_name])
        return getattr(module, class_name)
    except Exception as e:
        raise ValueError(f"Tool handler not found: {handler_class_path}") from e
```

### Files Changed: ✅ **Only 1 file** (`tool_loader.py`)

### No Other Changes Needed

- ✅ Database models: No changes
- ✅ API endpoints: No changes
- ✅ Domain agents: Already using `tool_registry.load_agent_tools()` - no changes
- ✅ Supervisor agent: No changes
- ✅ Tool implementations: No changes

---

## 🎯 Option 2: Dynamic Loading with Security Whitelist

For production environments where you want both flexibility AND security.

### Files to Change: **2 files**

#### File 1: `backend/src/services/tool_loader.py`

Add configuration for allowed tool namespaces:

```python
class ToolRegistry:
    # Whitelist of allowed tool module prefixes
    ALLOWED_TOOL_MODULES = [
        "tools.http",      # HTTP tools
        "tools.rag",       # RAG tools
        "tools.database",  # Database tools
        "tools.ocr",       # OCR tools
        "tools.custom",    # Custom tools (add as needed)
    ]

    def _get_handler_class(self, handler_class_path: str):
        """Dynamically import handler with security check."""
        # Security check: only allow whitelisted modules
        module_prefix = handler_class_path.rsplit(".", 1)[0]
        if module_prefix not in self.ALLOWED_TOOL_MODULES:
            raise ValueError(
                f"Tool module '{module_prefix}' not in allowed list. "
                f"Allowed modules: {self.ALLOWED_TOOL_MODULES}"
            )

        try:
            module_path, class_name = handler_class_path.rsplit(".", 1)
            module = __import__(f"src.{module_path}", fromlist=[class_name])
            handler_class = getattr(module, class_name)

            # Validate it's a tool class (optional extra security)
            if not hasattr(handler_class, 'execute'):
                raise ValueError(f"{handler_class_path} does not implement execute() method")

            return handler_class

        except Exception as e:
            raise ValueError(f"Tool handler error: {handler_class_path}") from e
```

#### File 2: `backend/src/config.py` (Optional - for configuration)

Add to settings:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Tool Security Settings
    ALLOWED_TOOL_MODULES: List[str] = [
        "tools.http",
        "tools.rag",
        "tools.database",
        "tools.ocr",
    ]

    # Enable dynamic tool loading (default: True)
    ENABLE_DYNAMIC_TOOL_LOADING: bool = True
```

---

## 🎯 Option 3: Keep Current (No Changes)

**Pros:**
- ✅ Maximum security (no arbitrary code execution)
- ✅ Simple and predictable
- ✅ Easy to audit what tools are available
- ✅ No changes needed

**Cons:**
- ❌ Requires redeployment for new tool types
- ❌ Less flexible

**When to use:** Production environments with strict security requirements

---

## 📊 Comparison Table

| Aspect | Current (Hardcoded) | Option 1 (Full Dynamic) | Option 2 (Whitelist) | Option 3 (No Change) |
|--------|-------------------|----------------------|-------------------|-------------------|
| **Files to change** | N/A | 1 file | 2 files | 0 files |
| **Redeployment for new types** | ❌ Required | ✅ Not required | ✅ Not required | ❌ Required |
| **Security** | 🔒 High | ⚠️ Medium | 🔒 High | 🔒 Highest |
| **Flexibility** | Low | High | High | Low |
| **Production ready** | ✅ Yes | ⚠️ With caution | ✅ Yes | ✅ Yes |
| **Recommended for** | Current state | Development | Production | High security |

---

## 🔧 Implementation Steps (Option 1 - Recommended)

### Step 1: Backup Current File
```bash
cd backend/src/services
cp tool_loader.py tool_loader.py.backup
```

### Step 2: Edit tool_loader.py

Add the `_get_handler_class` method (see code above)

### Step 3: Replace Line 77
```python
# OLD:
handler_class = self._tool_handlers.get(base_tool.handler_class)

# NEW:
handler_class = self._get_handler_class(base_tool.handler_class)
```

### Step 4: Remove hardcoded check (Line 78-79)
```python
# OLD - Remove these lines:
if not handler_class:
    raise ValueError(f"Unsupported tool handler: {base_tool.handler_class}")

# These lines are now in _get_handler_class
```

### Step 5: Test with Existing Tools

```bash
# Restart Docker
docker-compose restart app

# Test that existing tools still work
curl -X POST http://localhost:8000/api/<tenant-id>/chat \
  -d '{"message": "Hướng dẫn FCL", "user_id": "test"}'
```

### Step 6: Add New Tool Type (No Redeployment!)

```python
# 1. Create new tool handler: backend/src/tools/database.py
from src.tools.base import BaseTool

class DatabaseTool(BaseTool):
    async def execute(self, jwt_token: str, tenant_id: str, **params):
        query = params.get("query")
        # Execute SQL with tenant isolation
        return {"results": [...]}

# 2. Add base_tool to database via SQL or Admin API
INSERT INTO base_tools (base_tool_id, name, handler_class, description)
VALUES (
    uuid_generate_v4(),
    'DB_QUERY',
    'tools.database.DatabaseTool',  # No code changes needed!
    'Execute database queries'
);

# 3. Create tool instance via Admin API
# 4. Assign to agent
# 5. DONE! No restart needed (tool loads on first use)
```

---

## 🧪 Testing Plan

### Test 1: Existing Tools Still Work
```bash
# Should succeed with current RAG tool
curl -X POST http://localhost:8000/api/<tenant-id>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test query", "user_id": "test"}'
```

### Test 2: Invalid Handler Fails Gracefully
```sql
-- Create tool with invalid handler
INSERT INTO base_tools (base_tool_id, name, handler_class)
VALUES (uuid_generate_v4(), 'BadTool', 'tools.nonexistent.BadTool');

-- Should return clear error: "Tool handler not found: tools.nonexistent.BadTool"
```

### Test 3: New Tool Type Works
```python
# After creating new handler class + base_tool in database
# Tool should load dynamically without restart
```

---

## 🔍 Related Files Reference

Files that use `tool_registry` (READ ONLY - no changes needed):

1. **`src/services/domain_agents.py`** (line 7)
   - Imports: `from src.services.tool_loader import tool_registry`
   - Uses: `self.tools = tool_registry.load_agent_tools(...)`
   - **No changes needed** - already using the registry singleton

2. **`src/services/supervisor_agent.py`**
   - Loads agents, which in turn load tools from registry
   - **No changes needed**

3. **`src/api/admin/tools.py`**
   - CRUD operations on `tool_configs` table
   - **No changes needed** - just database operations

4. **`src/models/tool.py`**
   - SQLAlchemy model for `tool_configs` table
   - **No changes needed**

5. **`src/models/base_tool.py`**
   - SQLAlchemy model for `base_tools` table
   - **No changes needed**

---

## 🎯 Recommended Approach

**For your eTMS project, I recommend Option 1 (Simple Dynamic Loading):**

**Why:**
1. ✅ Only 1 file to change
2. ✅ You control the codebase (not public-facing)
3. ✅ Matches agent loading pattern (consistency)
4. ✅ Maximum flexibility for rapid development
5. ✅ Can add security layer later if needed

**When to use Option 2 instead:**
- Multi-tenant SaaS with untrusted tenants
- Database accessible by external parties
- Compliance requirements (SOC2, ISO27001)
- Production with high security standards

**When to use Option 3:**
- You rarely add new tool types (once per quarter)
- Security is paramount
- You prefer explicit over implicit

---

## 📈 Migration Path

### Phase 1: Development (Now)
- Implement Option 1 (dynamic loading)
- Test thoroughly with existing tools
- Add new tools as needed without redeployment

### Phase 2: Staging
- Monitor for any issues with dynamic loading
- Add logging for tool handler loads
- Performance testing

### Phase 3: Production (Later)
- Consider upgrading to Option 2 (whitelist) for security
- Add monitoring/alerting for failed tool loads
- Document allowed tool modules

---

## 🔐 Security Considerations

### Current (Hardcoded):
- ✅ Only pre-approved tools can run
- ✅ No risk of arbitrary code execution
- ✅ Easy to audit

### Option 1 (Dynamic):
- ⚠️ Any class in `src/tools/*` can be loaded
- ⚠️ Requires database security (SQL injection prevention)
- ⚠️ Requires code review for new tool classes

### Option 2 (Whitelist):
- ✅ Only approved modules can be loaded
- ✅ Flexible but controlled
- ✅ Best of both worlds

### Mitigation Strategies:
1. **Database Security**: Use parameterized queries (already done with SQLAlchemy)
2. **Code Review**: Review all new tool handler classes
3. **Validation**: Check tool classes implement required interface
4. **Logging**: Log all tool handler loads with user context
5. **Monitoring**: Alert on failed tool loads or unusual patterns

---

## 📝 Summary

**To enable dynamic tool loading:**

1. Edit 1 file: `src/services/tool_loader.py`
2. Add `_get_handler_class()` method
3. Replace hardcoded lookup on line 77
4. Test with existing tools
5. Add new tool types without redeployment!

**No other files need changes** - the architecture is already designed for this, just the lookup mechanism needs updating.

---

## 🆘 Rollback Plan

If anything breaks:

```bash
# Restore backup
cd backend/src/services
cp tool_loader.py.backup tool_loader.py

# Restart
docker-compose restart app
```

Changes are isolated to 1 file, so rollback is simple!
