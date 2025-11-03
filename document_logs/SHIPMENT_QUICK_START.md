# AgentShipment Quick Start

## ✅ What's Ready

- Setup script: `backend/setup_shipment_agent.py`
- Documentation: `project_docs/SETUP_SHIPMENT_AGENT.md`
- Entity extraction: Enhanced for `shipment_id` (VSG\d{10}FM)

## 🚀 Run Setup

```bash
cd backend
python setup_shipment_agent.py
```

## 📝 What Gets Created

1. **HTTP_GET BaseTool** - Generic HTTP tool handler
2. **Shipment ToolConfig** - API configuration (base_url, endpoint, etc.)
3. **AgentShipment** - Agent (uses generic DomainAgent class)
4. **Permissions** - For tenant 2628802d-1dff-4a98-9325-704433c5d3ab

## 🧪 Test Example

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the status of shipment VSG1234567890FM?",
    "tenant_id": "2628802d-1dff-4a98-9325-704433c5d3ab"
  }'
```

## 📊 100% Database-Driven

- ✅ No Python code changes needed
- ✅ All config in database
- ✅ Easily add new agents/tools by INSERT statements

## 🔧 Update API URL (if needed)

After setup, update database:
```sql
UPDATE tool_configs
SET config = jsonb_set(
  config,
  '{base_url}',
  '"https://your-real-api.com"'::jsonb
)
WHERE name = 'get_shipment_tracking';
```

---

**Ready for next step! What would you like to do?**
