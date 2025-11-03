# AgentShipment Setup Guide

## What's Been Set Up

✅ **Created setup script:** `backend/setup_shipment_agent.py`

This script creates:
1. **HTTP_GET BaseTool** - Generic HTTP GET tool handler
2. **Shipment ToolConfig** - Specific shipment tracking API configuration
3. **AgentShipment** - Agent for shipment tracking (100% database-driven, uses generic DomainAgent class)
4. **Tool-Agent Link** - Connects shipment tool to AgentShipment
5. **Tenant Permissions** - Grants tenant access to agent and tool

## Data Structure

### BaseTool (HTTP_GET)
```
base_tool_id: [generated]
type: "HTTP_GET"
handler_class: "tools.http.HTTPGetTool"
description: "HTTP GET request tool for external API calls"
```

### ToolConfig (Shipment Tracking)
```
tool_id: [generated]
name: "get_shipment_tracking"
base_tool_id: [HTTP_GET base tool]
config:
  - base_url: "https://api.shipment.example.com"
  - endpoint: "/v1/shipment/{shipment_id}"
  - headers: {"Content-Type": "application/json"}
  - timeout: 30

input_schema:
  - shipment_id: "Shipment ID (VSG + 10 digits + FM)"

description: "Get shipment tracking information and status by shipment ID"
```

### AgentConfig (AgentShipment)
```
agent_id: [generated]
name: "AgentShipment"
handler_class: "services.domain_agents.DomainAgent"  ← Generic class, no special code
prompt_template: "You are a Shipment Tracking Assistant..."
llm_model_id: [uses active LLM model]
description: "Shipment tracking agent for delivery status and information"
```

### Entity Extraction
Enhanced to support shipment tracking:
- **shipment_id** pattern: `VSG\d{10}FM` (e.g., VSG1234567890FM)
- **Example:** "What is the status of shipment VSG1234567890FM?"

## How to Run Setup

```bash
cd backend
python setup_shipment_agent.py
```

Expected output:
```
✅ Setup Complete!
Agent ID: [agent-uuid]
Tool ID: [tool-uuid]
Base Tool ID: [base-tool-uuid]
Tenant ID: 2628802d-1dff-4a98-9325-704433c5d3ab

You can now:
1. Send message to /test/chat with shipment tracking request
2. Example: 'What is the status of shipment VSG1234567890FM?'
3. Shipment tracking tool will automatically be loaded and used
4. SupervisorAgent will auto-detect and route to AgentShipment
5. Responses will be in user's language (EN/VI)
```

## Testing

### Test with shipment tracking request:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the status of shipment VSG1234567890FM?",
    "tenant_id": "2628802d-1dff-4a98-9325-704433c5d3ab"
  }'
```

Expected flow:
1. SupervisorAgent detects intent for shipment tracking
2. Routes to AgentShipment
3. AgentShipment extracts shipment_id: "VSG1234567890FM"
4. Loads shipment_tracking tool
5. Calls HTTP GET to `https://api.shipment.example.com/v1/shipment/VSG1234567890FM`
6. Returns shipment tracking information

## 100% Database-Driven ✅

- ✅ No code changes needed to add agent
- ✅ Agent class is generic DomainAgent (configured in DB)
- ✅ Tool configuration entirely in database
- ✅ Entity extraction supports shipment_id
- ✅ All permissions managed in database

## Notes

- Base URL is dummy: `https://api.shipment.example.com`
  - Update in database after running setup if you have real API
- HTTP timeout set to 30 seconds
- Tool supports JWT token injection from context
- Shipment ID pattern: VSG + 10 digits + FM

## To Update Shipment API URL

After running setup, update the tool config:

```sql
UPDATE tool_configs
SET config = jsonb_set(
  config,
  '{base_url}',
  '"https://your-real-shipment-api.com"'::jsonb
)
WHERE name = 'get_shipment_tracking';
```

Or update endpoint pattern:
```sql
UPDATE tool_configs
SET config = jsonb_set(
  config,
  '{endpoint}',
  '"/api/v2/tracking/{shipment_id}"'::jsonb
)
WHERE name = 'get_shipment_tracking';
```
