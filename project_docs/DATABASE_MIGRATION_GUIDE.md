# Database Migration: Add handler_class to agent_configs

## What Needs to Be Done

The refactoring to 100% database-driven requires adding a new column to the `agent_configs` table.

### Step 1: Add Column to Database

Connect to your PostgreSQL database and run:

```sql
-- Add handler_class column
ALTER TABLE agent_configs
ADD COLUMN handler_class VARCHAR(255) DEFAULT 'services.domain_agents.DomainAgent';

-- Update existing agents with correct handler classes
UPDATE agent_configs SET handler_class = 'services.domain_agents.AgentDebt'
WHERE name = 'AgentDebt';

UPDATE agent_configs SET handler_class = 'services.domain_agents.AgentAnalysis'
WHERE name = 'AgentAnalysis';

UPDATE agent_configs SET handler_class = 'services.domain_agents.DomainAgent'
WHERE name = 'AgentGuidance';
```

### Step 2: Verify Migration

```sql
SELECT name, handler_class FROM agent_configs ORDER BY name;
```

Expected output:
```
    name       |            handler_class
---------------+-----------------------------------
 AgentAnalysis  | services.domain_agents.AgentAnalysis
 AgentDebt      | services.domain_agents.AgentDebt
 AgentGuidance  | services.domain_agents.DomainAgent
```

### Step 3: Restart Application

After the migration, restart your FastAPI server:

```bash
# Restart backend service
pkill -f "uvicorn"
python -m uvicorn src.main:app --reload
```

## What This Enables

Once the column is added, your system becomes **100% database-driven**:

✅ **No hardcoded agent mappings** - AgentFactory uses database
✅ **Add new agents easily** - Just INSERT to agent_configs with handler_class
✅ **Custom agent logic** - Store Python module path in database
✅ **Zero code changes** - For new simple agents

## Example: Adding New Custom Agent

### Before (with old code)
```python
# Edit domain_agents.py
class AgentPayment(DomainAgent):
    pass

# Edit AgentFactory
elif agent_name == "AgentPayment":
    return AgentPayment(...)
```
❌ Code change needed

### After (100% database-driven)
```sql
-- Just add to database!
INSERT INTO agent_configs (name, handler_class, prompt_template, llm_model_id)
VALUES (
    'AgentPayment',
    'services.domain_agents.AgentPayment',
    'You are a payment agent...',
    'llm-model-id'
);

INSERT INTO tenant_agent_permissions (tenant_id, agent_id, enabled)
VALUES ('tenant-id', 'agent-id', TRUE);
```
✅ **No code change!**

## Files Changed

1. **Model:** `src/models/agent.py`
   - Added `handler_class` field with default value

2. **Service:** `src/services/domain_agents.py::AgentFactory`
   - Refactored to use dynamic class loading from database
   - No more hardcoded if/elif chains

3. **Migration Scripts:**
   - `MIGRATION_ADD_HANDLER_CLASS.sql` - SQL statements
   - `apply_handler_class_migration.py` - Python helper script

## Rollback (If Needed)

If you need to revert:

```sql
-- Remove handler_class column
ALTER TABLE agent_configs DROP COLUMN handler_class;
```

Then revert code changes in `domain_agents.py::AgentFactory`.

## Status

| Component | Status |
|-----------|--------|
| Model updated | ✅ |
| AgentFactory refactored | ✅ |
| Database migration SQL ready | ✅ |
| Database migration applied | ⏳ (waiting for user to run SQL) |
| System 100% database-driven | ⏳ |

## Next Steps

1. Run the SQL migration on your database
2. Restart the application
3. System is now 100% database-driven!

## Testing

After migration, test with:

```bash
# Test dynamic agent loading
python backend/test_dynamic_agents.py <tenant_id>
```

Should work the same as before, but now agents are loaded from `handler_class` database field!
