# MCP Server OAuth 2.1 Quickstart

## Overview

Secure your Model Context Protocol (MCP) server with Scalekit's OAuth 2.1 implementation. Scalekit provides a complete OAuth server that integrates seamlessly with MCP clients like Claude Desktop, Cursor, and VS Code.

**Use this when:**
- Building a new MCP server that needs authentication
- You want OAuth 2.1 compliance out of the box
- You need to support multiple authentication methods (SSO, social login, etc.)
- You want Scalekit to handle all OAuth complexity

**Time to implement:** 30-45 minutes

## Architecture

```
MCP Client (Claude Desktop)     Your MCP Server          Scalekit OAuth Server
        |                              |                            |
        |---(1) Discover metadata----->|                            |
        |<---(2) OAuth server URL------|                            |
        |                              |                            |
        |---(3) Start OAuth flow----------------------->|
        |                              |                            |
        |                              |         (4) User authenticates
        |                              |                            |
        |<---(5) Authorization code--------------------------|
        |                              |                            |
        |---(6) Exchange code-------------------------->|
        |<---(7) Access token---------------------------|
        |                              |                            |
        |---(8) MCP request + token--->|                            |
        |     (Bearer header)          |                            |
        |                              |                            |
        |                              |---(9) Validate token------>|
        |                              |<---(10) Token valid--------|
        |                              |                            |
        |<---(11) MCP response---------|                            |
```

## Step 1: Register MCP Server in Scalekit Dashboard

1. Go to **Dashboard → MCP Servers → Add MCP Server**
2. Enter server details:
   - **Name:** Your MCP server name (e.g., "Todo MCP Server")
   - **Server URL:** Your server identifier (e.g., `https://mcp.yourapp.com`)
3. Enable OAuth features:
   - ✅ **Dynamic Client Registration (DCR)**
   - ✅ **Client-Initiated Metadata Document (CIMD)**
4. Configure token settings:
   - **Access Token Lifetime:** 300-3600 seconds (5-60 minutes)
   - **Refresh Token:** Optional (enable for longer sessions)
5. Define scopes:
   - Example: `todo:read`, `todo:write`, `todo:delete`

**Save and note:**
- Resource ID (e.g., `res_12345...`)
- Resource metadata JSON (needed for discovery endpoint)

## Step 2: Install SDK

**Node.js:**
```bash
npm install @scalekit-sdk/node
```

**Python:**
```bash
pip install scalekit-sdk-python
```

## Step 3: Configure Environment

```bash
# .env
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_...
SCALEKIT_CLIENT_SECRET=test_...

# Your MCP server details
MCP_SERVER_URL=https://mcp.yourapp.com
RESOURCE_ID=res_12345...
```

## Step 4: Initialize Scalekit Client

**Node.js:**
```javascript
import { Scalekit } from '@scalekit-sdk/node';

const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

const RESOURCE_ID = process.env.RESOURCE_ID;
const MCP_SERVER_URL = process.env.MCP_SERVER_URL;
```

**Python:**
```python
from scalekit import ScalekitClient
from scalekit.common.scalekit import TokenValidationOptions

scalekit = ScalekitClient(
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET")
)

RESOURCE_ID = os.getenv("RESOURCE_ID")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
```

## Step 5: Implement OAuth Discovery Endpoint

MCP clients use `.well-known/oauth-protected-resource` to discover your OAuth configuration.

**Node.js (Express):**
```javascript
app.get('/.well-known/oauth-protected-resource', (req, res) => {
  res.json({
    "resource": MCP_SERVER_URL,
    "authorization_servers": [
      `${process.env.SCALEKIT_ENVIRONMENT_URL}/resources/${RESOURCE_ID}`
    ],
    "bearer_methods_supported": ["header"],
    "resource_documentation": `${MCP_SERVER_URL}/docs`,
    "scopes_supported": ["todo:read", "todo:write", "todo:delete"]
  });
});
```

**Python (FastAPI):**
```python
@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    return {
        "resource": MCP_SERVER_URL,
        "authorization_servers": [
            f"{os.getenv('SCALEKIT_ENVIRONMENT_URL')}/resources/{RESOURCE_ID}"
        ],
        "bearer_methods_supported": ["header"],
        "resource_documentation": f"{MCP_SERVER_URL}/docs",
        "scopes_supported": ["todo:read", "todo:write", "todo:delete"]
    }
```

## Step 6: Create Authentication Middleware

Extract and validate the Bearer token on every request.

**Node.js (Express):**
```javascript
async function authMiddleware(req, res, next) {
  try {
    // Skip auth for discovery endpoint
    if (req.path.includes('.well-known')) {
      return next();
    }

    // Extract Bearer token
    const authHeader = req.headers['authorization'];
    const token = authHeader?.startsWith('Bearer ')
      ? authHeader.split('Bearer ')[1]?.trim()
      : null;

    if (!token) {
      return res.status(401)
        .set('WWW-Authenticate',
          `Bearer realm="OAuth", resource_metadata="${MCP_SERVER_URL}/.well-known/oauth-protected-resource"`)
        .json({ error: 'Missing or invalid Bearer token' });
    }

    // Validate token with Scalekit
    const claims = await scalekit.validateToken(token, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
      audience: [RESOURCE_ID]
    });

    // Attach user info to request
    req.user = claims;
    req.scopes = claims.scope?.split(' ') || [];

    next();
  } catch (error) {
    console.error('Auth middleware error:', error);
    return res.status(401)
      .set('WWW-Authenticate',
        `Bearer realm="OAuth", error="invalid_token", resource_metadata="${MCP_SERVER_URL}/.well-known/oauth-protected-resource"`)
      .json({ error: 'Invalid or expired token' });
  }
}

// Apply to all routes except discovery
app.use('/', authMiddleware);
```

**Python (FastAPI):**
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def auth_middleware(request: Request, call_next):
    # Skip auth for discovery endpoint
    if '.well-known' in request.url.path:
        return await call_next(request)

    # Extract Bearer token
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1].strip()

    if not token:
        return JSONResponse(
            status_code=401,
            headers={
                "WWW-Authenticate": f'Bearer realm="OAuth", resource_metadata="{MCP_SERVER_URL}/.well-known/oauth-protected-resource"'
            },
            content={"error": "Missing or invalid Bearer token"}
        )

    try:
        # Validate token
        claims = scalekit.validate_token(
            token,
            options=TokenValidationOptions(
                issuer=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
                audience=[RESOURCE_ID]
            )
        )

        # Attach user info to request
        request.state.user = claims
        request.state.scopes = claims.get("scope", "").split()

        return await call_next(request)

    except Exception as error:
        return JSONResponse(
            status_code=401,
            headers={
                "WWW-Authenticate": f'Bearer realm="OAuth", error="invalid_token", resource_metadata="{MCP_SERVER_URL}/.well-known/oauth-protected-resource"'
            },
            content={"error": "Invalid or expired token"}
        )

# Apply middleware
app.middleware("http")(auth_middleware)
```

## Step 7: Implement Scope-Based Authorization

Protect specific tools/endpoints with required scopes.

**Node.js:**
```javascript
function requireScope(scope) {
  return (req, res, next) => {
    if (!req.scopes || !req.scopes.includes(scope)) {
      return res.status(403).json({
        error: 'insufficient_scope',
        error_description: `Required scope: ${scope}`,
        scope: scope
      });
    }
    next();
  };
}

// Protect endpoints with scopes
app.get('/todos', requireScope('todo:read'), async (req, res) => {
  const todos = await getTodos(req.user.sub);
  res.json({ todos });
});

app.post('/todos', requireScope('todo:write'), async (req, res) => {
  const todo = await createTodo(req.user.sub, req.body);
  res.json({ todo });
});

app.delete('/todos/:id', requireScope('todo:delete'), async (req, res) => {
  await deleteTodo(req.user.sub, req.params.id);
  res.json({ success: true });
});
```

**Python:**
```python
def require_scope(scope: str):
    async def check_scope(request: Request):
        scopes = getattr(request.state, 'scopes', [])
        if scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_scope",
                    "error_description": f"Required scope: {scope}",
                    "scope": scope
                }
            )
        return True
    return check_scope

# Protect endpoints
@app.get("/todos")
async def get_todos(request: Request, _: bool = Depends(require_scope("todo:read"))):
    user = request.state.user
    todos = await get_user_todos(user["sub"])
    return {"todos": todos}

@app.post("/todos")
async def create_todo(request: Request, todo_data: dict, _: bool = Depends(require_scope("todo:write"))):
    user = request.state.user
    todo = await create_user_todo(user["sub"], todo_data)
    return {"todo": todo}

@app.delete("/todos/{todo_id}")
async def delete_todo(request: Request, todo_id: str, _: bool = Depends(require_scope("todo:delete"))):
    user = request.state.user
    await delete_user_todo(user["sub"], todo_id)
    return {"success": True}
```

## Step 8: Handle CORS (If Needed)

**Node.js:**
```javascript
import cors from 'cors';

app.use(cors({
  origin: '*', // Or specify allowed origins
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
```

**Python:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 9: Test with MCP Client

### Configure Claude Desktop

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "your-mcp-server": {
      "url": "https://mcp.yourapp.com",
      "transport": "sse"
    }
  }
}
```

### Test Flow

1. Start your MCP server
2. Open Claude Desktop
3. Claude discovers OAuth via `.well-known` endpoint
4. Claude initiates OAuth flow → redirects to Scalekit
5. User authenticates
6. Claude receives access token
7. Claude makes MCP requests with Bearer token
8. Your server validates token and responds

## Complete Example: Todo MCP Server

See [templates/nodejs-mcp-oauth.md](templates/nodejs-mcp-oauth.md) for a complete working MCP server with OAuth.

## Authentication Methods

Scalekit supports multiple authentication methods for your MCP server:

### 1. Email/Password (Default)

Users sign in with email and password.

### 2. Social Login

Enable in Dashboard → Authentication:
- Google
- GitHub
- Microsoft

### 3. Enterprise SSO

Enable SAML/OIDC for enterprise users:
- Okta
- Azure AD
- Google Workspace

### 4. Magic Link

Passwordless authentication via email.

**All methods work automatically** - no code changes needed!

## Token Management

### Access Token Validation

```javascript
// Tokens are validated on every request
const claims = await scalekit.validateToken(token, {
  issuer: SCALEKIT_ENVIRONMENT_URL,
  audience: [RESOURCE_ID]
});

// Claims include:
// - sub: User ID
// - scope: Granted scopes
// - exp: Expiration timestamp
// - iat: Issued at timestamp
```

### Token Refresh

If you enabled refresh tokens:

```javascript
// MCP client handles refresh automatically
// No server-side code needed
```

### Token Expiration

Set in Scalekit Dashboard:
- **Short-lived:** 300 seconds (5 min) - More secure
- **Medium:** 1800 seconds (30 min) - Balanced
- **Long-lived:** 3600 seconds (1 hour) - Fewer refreshes

## Production Deployment

### 1. HTTPS Required

OAuth requires HTTPS in production:

```javascript
// Ensure server uses HTTPS
const server = https.createServer(sslOptions, app);
server.listen(443);
```

### 2. Register Production URLs

In Scalekit Dashboard:
- Update Server URL to production domain
- Ensure all redirect URIs are HTTPS

### 3. Environment Variables

```bash
# Production
SCALEKIT_ENVIRONMENT_URL=https://prod-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_prod_...
SCALEKIT_CLIENT_SECRET=prod_...
MCP_SERVER_URL=https://mcp.yourapp.com
```

### 4. Monitoring

Log authentication events:

```javascript
app.use((req, res, next) => {
  if (req.user) {
    console.log('Authenticated request:', {
      user: req.user.sub,
      path: req.path,
      scopes: req.scopes,
      timestamp: new Date()
    });
  }
  next();
});
```

## Troubleshooting

### Discovery Endpoint Not Working

**Check:**
- `.well-known/oauth-protected-resource` returns valid JSON
- `authorization_servers` URL is correct
- CORS headers allow MCP client

**Test:**
```bash
curl https://mcp.yourapp.com/.well-known/oauth-protected-resource
```

### Token Validation Fails

**Check:**
- Token is being sent in `Authorization: Bearer <token>` header
- Issuer matches your Scalekit environment URL
- Audience includes your Resource ID
- Token hasn't expired

### MCP Client Can't Connect

**Check:**
- Server is running and accessible
- Discovery endpoint returns 200 OK
- HTTPS is enabled (in production)
- No firewall blocking

### Scope Errors

**Check:**
- Scopes are defined in Dashboard
- Scopes match exactly (case-sensitive)
- User has been granted required scopes

## Security Best Practices

1. **Always validate tokens** - Never trust client-provided claims
2. **Use HTTPS** - Required for OAuth security
3. **Short token lifetime** - 5-30 minutes recommended
4. **Log security events** - Track authentication attempts
5. **Scope principle** - Minimal necessary scopes only
6. **Rate limiting** - Prevent abuse

## Next Steps

- See [templates/nodejs-mcp-oauth.md](templates/nodejs-mcp-oauth.md) for complete example
- See [templates/python-mcp-oauth.md](templates/python-mcp-oauth.md) for Python example
- Read [custom-auth-integration.md](custom-auth-integration.md) for integrating with existing auth
- Review [../reference/mcp-best-practices.md](../reference/mcp-best-practices.md) for advanced patterns
