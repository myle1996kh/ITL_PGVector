# Iframe Widget Provisioning Guide - Multi-Tenant Setup

**Version**: 1.0
**Last Updated**: 2025-11-03
**Audience**: Administrators, Developers

---

## Overview: How Tenants Get Their Iframe

```
┌─────────────────────────────────────────────────────────────────────┐
│ IFRAME PROVISIONING FLOW FOR EACH TENANT                            │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Admin Creates Tenant in Database
    ↓
Step 2: Backend Generates Widget Configuration (widget_key, embed_code)
    ↓
Step 3: Admin Retrieves Embed Code from API
    ↓
Step 4: Tenant Copies Embed Code to Their Website
    ↓
Step 5: Widget Loads Dynamically with Tenant-Specific Settings
```

---

## Step-by-Step Process

### Step 1: Create Tenant (One-Time Setup)

**Admin Action**: Create new tenant via Admin API

```bash
POST /api/admin/tenants
Content-Type: application/json
Authorization: Bearer <ADMIN_JWT>

{
  "name": "Acme Corporation",
  "domain": "acme.com",
  "status": "active"
}
```

**Response**:
```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Acme Corporation",
  "domain": "acme.com",
  "status": "active",
  "created_at": "2025-11-03T10:00:00Z"
}
```

**Database Record Created**:
```sql
-- tenants table
INSERT INTO tenants (tenant_id, name, domain, status)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  'Acme Corporation',
  'acme.com',
  'active'
);
```

---

### Step 2: Generate Widget Configuration (Automatic)

**Admin Action**: Request widget configuration for tenant

```bash
POST /api/admin/widget
Content-Type: application/json
Authorization: Bearer <ADMIN_JWT>

{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "theme": "light",
  "primary_color": "#3B82F6",
  "position": "bottom-right",
  "auto_open": false,
  "welcome_message": "Hi! How can we help you today?",
  "allowed_domains": ["https://acme.com", "https://www.acme.com"],
  "cdn_base_url": "https://widget.agenthub.com"
}
```

**Backend Processing** (Automatic):
1. Generates unique `widget_key` (public identifier)
2. Generates `widget_secret` (for verification)
3. Encrypts widget_secret with Fernet
4. Creates embed code snippet
5. Stores configuration in database

**Response**:
```json
{
  "config_id": "123e4567-e89b-12d3-a456-426614174000",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "widget_key": "wk_AbC123XyZ789_RandomSecureKey",
  "theme": "light",
  "primary_color": "#3B82F6",
  "position": "bottom-right",
  "embed_script_url": "https://widget.agenthub.com/embed.js",
  "embed_code_snippet": "<!-- AgentHub Chat Widget -->\n<div id=\"agenthub-chat\"\n     data-widget-key=\"wk_AbC123XyZ789_RandomSecureKey\"></div>\n<script src=\"https://widget.agenthub.com/embed.js\" async></script>",
  "created_at": "2025-11-03T10:05:00Z"
}
```

**Database Record Created**:
```sql
-- tenant_widget_configs table
INSERT INTO tenant_widget_configs (
  config_id,
  tenant_id,
  widget_key,
  widget_secret,  -- encrypted
  theme,
  primary_color,
  position,
  allowed_domains,
  embed_script_url,
  embed_code_snippet
) VALUES (
  '123e4567-e89b-12d3-a456-426614174000',
  '550e8400-e29b-41d4-a716-446655440000',
  'wk_AbC123XyZ789_RandomSecureKey',
  'gAAAAA...encrypted...',
  'light',
  '#3B82F6',
  'bottom-right',
  '["https://acme.com", "https://www.acme.com"]',
  'https://widget.agenthub.com/embed.js',
  '<!-- AgentHub Chat Widget -->...'
);
```

---

### Step 3: Retrieve Embed Code (Admin Panel UI)

**Option A: Via API**
```bash
GET /api/admin/widget/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <ADMIN_JWT>
```

**Option B: Via Admin Panel**

Admin logs into Admin Panel UI and sees:

```
┌──────────────────────────────────────────────────────────────┐
│ Widget Configuration for Acme Corporation                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Widget Key: wk_AbC123XyZ789_RandomSecureKey                  │
│ Status: Active                                                │
│ Theme: Light                                                  │
│ Position: Bottom Right                                        │
│                                                               │
│ ─────────────────────────────────────────────────────────── │
│ Embed Code (Copy this to your website):                      │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ <!-- AgentHub Chat Widget -->                         │   │
│ │ <div id="agenthub-chat"                               │   │
│ │      data-widget-key="wk_AbC123XyZ789_RandomSecureKey"│   │
│ │ </div>                                                │   │
│ │ <script src="https://widget.agenthub.com/embed.js"   │   │
│ │         async></script>                               │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ [ Copy to Clipboard ]  [ Regenerate Widget Key ]             │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

### Step 4: Tenant Embeds Widget on Their Website

**Tenant Action**: Paste embed code into their HTML

**File**: `https://acme.com/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Acme Corporation - Home</title>
</head>
<body>
  <h1>Welcome to Acme Corporation</h1>
  <p>Our products and services...</p>

  <!-- AgentHub Chat Widget -->
  <div id="agenthub-chat"
       data-widget-key="wk_AbC123XyZ789_RandomSecureKey"></div>
  <script src="https://widget.agenthub.com/embed.js" async></script>

</body>
</html>
```

**What Happens When Page Loads**:

1. Browser loads `embed.js` script from CDN
2. Script finds `<div id="agenthub-chat">`
3. Reads `data-widget-key` attribute
4. Creates iframe dynamically with tenant configuration
5. Iframe loads widget with tenant-specific settings

---

### Step 5: Widget Loads with Tenant Configuration

**Iframe Created Dynamically**:

```html
<!-- Dynamically injected by embed.js -->
<div id="agenthub-chat" data-widget-key="wk_AbC123XyZ789_RandomSecureKey">

  <iframe
    src="https://widget.agenthub.com/widget.html?tenant=550e8400-e29b-41d4-a716-446655440000&key=wk_AbC123XyZ789_RandomSecureKey&theme=light&autoOpen=false"
    style="position: fixed; bottom: 20px; right: 20px; width: 400px; height: 600px; border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 9999;"
    sandbox="allow-scripts allow-same-origin"
    title="AgentHub Chat Widget"
  ></iframe>

</div>
```

**Inside the Iframe**:
- Widget loads React app from `widget.html`
- Parses URL params: `tenant`, `key`, `theme`
- Validates `widget_key` against backend
- Loads tenant configuration from database
- Applies theme, colors, welcome message
- Ready to chat!

---

## Database Schema Relationships

```sql
-- Tenant has widget config (1-to-1 relationship)
tenants.tenant_id  ←→  tenant_widget_configs.tenant_id

-- Widget config stores all customization
CREATE TABLE tenant_widget_configs (
  config_id UUID PRIMARY KEY,
  tenant_id UUID UNIQUE REFERENCES tenants(tenant_id),

  -- Public identifier (shown in embed code)
  widget_key VARCHAR(64) UNIQUE NOT NULL,

  -- Secret for verification (encrypted)
  widget_secret VARCHAR(255) NOT NULL,

  -- Appearance settings
  theme VARCHAR(20) DEFAULT 'light',
  primary_color VARCHAR(7) DEFAULT '#3B82F6',
  position VARCHAR(20) DEFAULT 'bottom-right',
  custom_css TEXT,

  -- Behavior
  auto_open BOOLEAN DEFAULT false,
  welcome_message TEXT,
  placeholder_text VARCHAR(255) DEFAULT 'Type your message...',

  -- Security
  allowed_domains JSON DEFAULT '[]',
  max_session_duration INTEGER DEFAULT 3600,
  rate_limit_per_minute INTEGER DEFAULT 20,

  -- Feature flags
  enable_file_upload BOOLEAN DEFAULT false,
  enable_voice_input BOOLEAN DEFAULT false,
  enable_conversation_history BOOLEAN DEFAULT true,

  -- Embed code (generated)
  embed_script_url VARCHAR(500),
  embed_code_snippet TEXT,

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  last_regenerated_at TIMESTAMP
);

-- Index for fast widget key lookup
CREATE INDEX idx_widget_key ON tenant_widget_configs(widget_key);
```

---

## How Widget Key Validation Works

### Frontend (embed.js)
```javascript
// 1. Extract widget_key from HTML
const widgetKey = container.dataset.widgetKey;

// 2. Include in iframe URL
const iframeUrl = `https://widget.agenthub.com/widget.html?key=${widgetKey}`;
```

### Widget App (widget.tsx)
```typescript
// 3. Parse URL params
const urlParams = new URLSearchParams(window.location.search);
const widgetKey = urlParams.get('key');

// 4. Call backend to validate and get config
const response = await fetch(
  `https://api.agenthub.com/api/widget/validate/${widgetKey}`
);

if (!response.ok) {
  // Invalid widget key
  showError('Widget configuration not found');
  return;
}

const config = await response.json();
// config contains: tenant_id, theme, colors, etc.
```

### Backend (widget validation endpoint)
```python
@router.get("/widget/validate/{widget_key}")
async def validate_widget_key(
    widget_key: str,
    db: Session = Depends(get_db)
):
    """Validate widget key and return configuration."""

    config = db.query(TenantWidgetConfig).filter_by(
        widget_key=widget_key
    ).first()

    if not config:
        raise HTTPException(404, "Widget key not found")

    # Check if tenant is active
    tenant = db.query(Tenant).filter_by(
        tenant_id=config.tenant_id,
        status='active'
    ).first()

    if not tenant:
        raise HTTPException(403, "Tenant inactive")

    # Return config (without secrets)
    return {
        "tenant_id": str(config.tenant_id),
        "theme": config.theme,
        "primary_color": config.primary_color,
        "position": config.position,
        "welcome_message": config.welcome_message,
        "allowed_domains": config.allowed_domains
    }
```

---

## Security Considerations

### 1. Widget Key vs Widget Secret

| Aspect | Widget Key | Widget Secret |
|--------|------------|---------------|
| **Visibility** | Public (in HTML) | Private (database only) |
| **Purpose** | Identify tenant | Verify authenticity |
| **Location** | Embed code | Backend database (encrypted) |
| **Can be rotated?** | Yes (regenerate) | Auto-generated with key |

### 2. Domain Whitelisting

```javascript
// In embed.js - validate parent domain
const allowedDomains = ['https://acme.com', 'https://www.acme.com'];
const parentDomain = window.location.origin;

if (!allowedDomains.includes(parentDomain)) {
  console.error('[AgentHub] Domain not authorized');
  return;
}
```

### 3. Iframe Sandbox

```html
<iframe sandbox="allow-scripts allow-same-origin">
```

**Restrictions**:
- ✅ Allow JavaScript (needed for React app)
- ✅ Allow same-origin requests (API calls)
- ❌ Block form submission to external sites
- ❌ Block popups
- ❌ Block top-level navigation

### 4. PostMessage Origin Validation

```javascript
// In widget app
window.addEventListener('message', (event) => {
  // CRITICAL: Validate origin
  const allowedOrigins = ['https://acme.com', 'https://www.acme.com'];

  if (!allowedOrigins.includes(event.origin)) {
    console.warn('[AgentHub] Rejected message from', event.origin);
    return;
  }

  // Safe to process message
  if (event.data.type === 'RESIZE') {
    // Handle resize
  }
});
```

---

## Advanced Configuration Options

### Custom CSS Overrides

Tenants can customize widget appearance:

```html
<div id="agenthub-chat"
     data-widget-key="wk_AbC123XyZ789_RandomSecureKey"
     data-custom-css="
       .chat-container { border-radius: 20px; }
       .message-bubble.user { background: #FF6B6B; }
     "></div>
```

### Dynamic Positioning

```html
<div id="agenthub-chat"
     data-widget-key="wk_AbC123XyZ789_RandomSecureKey"
     data-position="top-left"
     data-offset-x="10"
     data-offset-y="80"></div>
```

### Auto-Open on Specific Pages

```html
<div id="agenthub-chat"
     data-widget-key="wk_AbC123XyZ789_RandomSecureKey"
     data-auto-open="true"
     data-auto-open-delay="3000"></div>
```

---

## Multi-Environment Setup

### Development
```html
<!-- Use dev widget server -->
<div id="agenthub-chat" data-widget-key="wk_dev_test123"></div>
<script src="http://localhost:3000/embed.js" async></script>
```

### Staging
```html
<!-- Use staging widget server -->
<div id="agenthub-chat" data-widget-key="wk_staging_AbC123"></div>
<script src="https://widget-staging.agenthub.com/embed.js" async></script>
```

### Production
```html
<!-- Use production CDN -->
<div id="agenthub-chat" data-widget-key="wk_prod_XyZ789"></div>
<script src="https://widget.agenthub.com/embed.js" async></script>
```

---

## Widget Key Rotation

**When to Rotate**:
- Security breach suspected
- Tenant changes ownership
- Regular security policy (e.g., every 90 days)

**Process**:

1. Admin triggers rotation:
```bash
POST /api/admin/widget/550e8400.../rotate
Authorization: Bearer <ADMIN_JWT>
```

2. Backend generates new key:
```python
new_widget_key = f"wk_{secrets.token_urlsafe(32)}"
new_widget_secret = secrets.token_urlsafe(64)

config.widget_key = new_widget_key
config.widget_secret = encrypt_fernet(new_widget_secret)
config.last_regenerated_at = datetime.utcnow()
config.embed_code_snippet = generate_embed_snippet(new_widget_key, cdn_url)

db.commit()
```

3. Admin provides new embed code to tenant

4. Tenant updates their website

5. Old key disabled after grace period (e.g., 7 days)

---

## Monitoring & Analytics

### Track Widget Usage

```sql
-- Create widget_analytics table
CREATE TABLE widget_analytics (
  id UUID PRIMARY KEY,
  tenant_id UUID REFERENCES tenants(tenant_id),
  widget_key VARCHAR(64),
  event_type VARCHAR(50),  -- 'loaded', 'message_sent', 'error'
  domain VARCHAR(255),
  user_agent TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Example queries
-- Widget loads per day
SELECT
  DATE(timestamp) as date,
  COUNT(*) as loads
FROM widget_analytics
WHERE event_type = 'loaded' AND tenant_id = '550e8400...'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Most active domains
SELECT
  domain,
  COUNT(*) as message_count
FROM widget_analytics
WHERE event_type = 'message_sent' AND tenant_id = '550e8400...'
GROUP BY domain
ORDER BY message_count DESC;
```

---

## Troubleshooting Guide

### Issue 1: Widget Not Appearing

**Symptoms**: Blank space where widget should be

**Checklist**:
- [ ] `embed.js` script loaded? (Check Network tab)
- [ ] `<div id="agenthub-chat">` exists on page?
- [ ] `data-widget-key` attribute present and correct?
- [ ] Console errors? (CORS, CSP violations)
- [ ] Tenant status = 'active' in database?

**Fix**:
```javascript
// Debug mode - add to embed.js
console.log('[AgentHub] Widget key:', container.dataset.widgetKey);
console.log('[AgentHub] Iframe URL:', iframe.src);
```

---

### Issue 2: Invalid Widget Key Error

**Symptoms**: "Widget configuration not found" error

**Causes**:
- Widget key typo in HTML
- Tenant deleted/deactivated
- Database record missing

**Fix**:
```bash
# Verify widget key in database
SELECT * FROM tenant_widget_configs WHERE widget_key = 'wk_AbC123...';

# If missing, regenerate
POST /api/admin/widget
{
  "tenant_id": "550e8400...",
  ...
}
```

---

### Issue 3: CORS Errors

**Symptoms**: API calls blocked by browser

**Causes**:
- Parent domain not in `allowed_domains`
- CORS headers misconfigured on backend

**Fix**:
```python
# Update allowed_domains for tenant
UPDATE tenant_widget_configs
SET allowed_domains = '["https://acme.com", "https://www.acme.com"]'
WHERE tenant_id = '550e8400...';

# Verify backend CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://widget.agenthub.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Complete Example: Tenant Onboarding Flow

### Admin Script (Python)

```python
import requests

ADMIN_TOKEN = "eyJhbGciOi..."
API_BASE = "https://api.agenthub.com"
HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# 1. Create tenant
tenant_response = requests.post(
    f"{API_BASE}/api/admin/tenants",
    headers=HEADERS,
    json={
        "name": "Acme Corporation",
        "domain": "acme.com",
        "status": "active"
    }
)
tenant_id = tenant_response.json()["tenant_id"]
print(f"✓ Created tenant: {tenant_id}")

# 2. Create LLM config
llm_response = requests.post(
    f"{API_BASE}/api/admin/tenants/{tenant_id}/llm-config",
    headers=HEADERS,
    json={
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "sk-..."  # Encrypted by backend
    }
)
print("✓ Configured LLM")

# 3. Grant agent permissions
requests.post(
    f"{API_BASE}/api/admin/tenants/{tenant_id}/permissions",
    headers=HEADERS,
    json={
        "agent_id": "uuid-agent-debt",
        "enabled": True
    }
)
print("✓ Granted AgentDebt permission")

# 4. Generate widget config
widget_response = requests.post(
    f"{API_BASE}/api/admin/widget",
    headers=HEADERS,
    json={
        "tenant_id": tenant_id,
        "theme": "light",
        "primary_color": "#3B82F6",
        "position": "bottom-right",
        "allowed_domains": ["https://acme.com"],
        "cdn_base_url": "https://widget.agenthub.com"
    }
)
widget_config = widget_response.json()
print("✓ Generated widget configuration")

# 5. Output embed code for tenant
print("\n" + "="*60)
print("EMBED CODE FOR ACME CORPORATION:")
print("="*60)
print(widget_config["embed_code_snippet"])
print("="*60)
```

**Output**:
```
✓ Created tenant: 550e8400-e29b-41d4-a716-446655440000
✓ Configured LLM
✓ Granted AgentDebt permission
✓ Generated widget configuration

============================================================
EMBED CODE FOR ACME CORPORATION:
============================================================
<!-- AgentHub Chat Widget -->
<div id="agenthub-chat"
     data-widget-key="wk_AbC123XyZ789_RandomSecureKey"></div>
<script src="https://widget.agenthub.com/embed.js" async></script>
============================================================
```

---

## Summary: Key Takeaways

### Where Iframe Comes From
1. **Not pre-created** - Generated dynamically by `embed.js` when page loads
2. **Tenant-specific** - Each tenant gets unique `widget_key`
3. **Database-driven** - Configuration stored in `tenant_widget_configs` table
4. **Secure** - Widget key validated on every load

### What Tenant Receives
1. **Embed code snippet** (2 lines of HTML)
2. **Widget key** (public identifier)
3. **Configuration options** (theme, colors, position)
4. **Documentation** on how to paste code

### What Gets Stored in Database
```sql
tenant_widget_configs:
  - widget_key (public, in embed code)
  - widget_secret (private, encrypted)
  - theme, colors, position
  - allowed_domains (security)
  - embed_code_snippet (ready-to-copy)
```

### How It All Connects
```
Tenant HTML (data-widget-key)
    ↓
embed.js (creates iframe)
    ↓
widget.html?key=wk_... (validates key)
    ↓
Backend API (returns tenant config)
    ↓
React Widget App (applies theme, loads chat)
```

---

**End of Iframe Widget Provisioning Guide**

---

## Quick Reference

### Admin Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/widget` | POST | Create widget config |
| `/api/admin/widget/{tenant_id}` | GET | Get widget config |
| `/api/admin/widget/{tenant_id}/rotate` | POST | Rotate widget key |

### Public Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/widget/validate/{widget_key}` | GET | Validate key, get config |
| `/embed.js` | GET | Widget loader script |
| `/widget.html` | GET | Iframe host page |

### Database Tables
- `tenants` - Tenant master data
- `tenant_widget_configs` - Widget settings per tenant
- `tenant_agent_permissions` - Which agents tenant can use
- `tenant_llm_configs` - LLM API keys per tenant

---

**Document Status**: ✅ Complete
**Next Steps**: Implement Phase 3 of Frontend Plan
**Support**: Contact dev team for provisioning assistance
