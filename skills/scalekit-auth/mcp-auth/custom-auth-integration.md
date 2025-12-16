# MCP Custom Auth Integration

## Overview

Integrate Scalekit's OAuth 2.1 layer with your **existing authentication system** for MCP servers. This federated approach lets you keep your current auth logic while leveraging Scalekit for OAuth compliance and MCP client integration.

**Use this when:**
- You have existing authentication (sessions, JWT, API keys, etc.)
- You want to add MCP support without changing your auth
- You need OAuth 2.1 for MCP clients but want to control user verification
- You want to integrate with your user database and permissions

**Time to implement:** 1-2 hours

## Architecture

```
MCP Client          Scalekit OAuth           Your Login           Your Auth System
   |                     |                      Endpoint                 |
   |---(1) OAuth-------->|                         |                     |
   |     flow starts     |                         |                     |
   |                     |                         |                     |
   |                     |---(2) Redirect--------->|                     |
   |                     |   with login_request_id |                     |
   |                     |                         |                     |
   |                     |                         |---(3) Authenticate->|
   |                     |                         |     (your logic)    |
   |                     |                         |<---(4) User info----|
   |                     |                         |                     |
   |                     |<---(5) Submit user------|                     |
   |                     |     details via API     |                     |
   |                     |                         |                     |
   |<---(6) OAuth--------|                         |                     |
   |     completes       |                         |                     |
   |                     |                         |                     |
   |---(7) MCP request-->|---(8) Validate token------------------------->|
   |     with token      |                         |                     |
```

**Key concept:** Scalekit handles OAuth (steps 1, 6-8). You handle authentication (steps 2-5).

## Three-Step Integration Flow

### Step 1: Scalekit Redirects to Your Login

When OAuth starts, Scalekit redirects to your login URL with:
- `login_request_id` - Unique ID for this auth request
- `state` - OAuth state parameter (pass back later)

### Step 2: You Authenticate the User

Use your existing authentication:
- Check username/password
- Validate SSO token
- Verify API key
- Whatever your current auth does!

### Step 3: Submit User Details to Scalekit

Send authenticated user info to Scalekit, which completes the OAuth flow.

## Implementation

### Part 1: Configure Scalekit Dashboard

1. Go to **Dashboard → MCP Servers → [Your Server] → Authentication**
2. Select **Custom Authentication**
3. Configure:
   - **Login URL:** `https://yourapp.com/auth/mcp-login`
   - **Connection ID:** Note this value (e.g., `conn_12345...`)

### Part 2: Handle Login Redirect

When Scalekit redirects to your login endpoint, it sends `login_request_id` and `state`.

**Node.js (Express):**
```javascript
import { Scalekit } from '@scalekit-sdk/node';

const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

const CONNECTION_ID = process.env.SCALEKIT_CONNECTION_ID; // From Dashboard

app.get('/auth/mcp-login', (req, res) => {
  const { login_request_id, state } = req.query;

  if (!login_request_id || !state) {
    return res.status(400).send('Missing required parameters');
  }

  // Store in session for later use
  req.session.mcp_login_request_id = login_request_id;
  req.session.mcp_state = state;
  req.session.save();

  // Show YOUR login page
  res.render('mcp-login', {
    login_request_id,
    state
  });
});
```

**Python (FastAPI):**
```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

CONNECTION_ID = os.getenv("SCALEKIT_CONNECTION_ID")

@app.get("/auth/mcp-login", response_class=HTMLResponse)
async def mcp_login(request: Request, login_request_id: str, state: str):
    if not login_request_id or not state:
        raise HTTPException(status_code=400, detail="Missing parameters")

    # Store in session
    request.session["mcp_login_request_id"] = login_request_id
    request.session["mcp_state"] = state

    # Show YOUR login page
    return templates.TemplateResponse("mcp_login.html", {
        "request": request,
        "login_request_id": login_request_id,
        "state": state
    })
```

### Part 3: Authenticate User (Your Logic)

This is YOUR existing authentication - no changes needed!

**Example with username/password:**
```javascript
app.post('/auth/mcp-login/submit', async (req, res) => {
  const { username, password } = req.body;

  try {
    // YOUR existing authentication
    const user = await authenticateUser(username, password);

    if (!user) {
      return res.status(401).send('Invalid credentials');
    }

    // Continue to Step 4...
    await submitUserToScalekit(req, res, user);
  } catch (error) {
    console.error('Authentication error:', error);
    res.status(500).send('Authentication failed');
  }
});
```

**Example with existing session:**
```javascript
app.get('/auth/mcp-login/auto', async (req, res) => {
  // User already has YOUR session
  if (!req.session.userId) {
    return res.redirect('/auth/mcp-login');
  }

  try {
    // Get user from YOUR database
    const user = await db.users.findById(req.session.userId);

    await submitUserToScalekit(req, res, user);
  } catch (error) {
    console.error('Auto-auth error:', error);
    res.redirect('/auth/mcp-login');
  }
});
```

### Part 4: Submit User Details to Scalekit

After authenticating, send user info to Scalekit.

**Node.js:**
```javascript
async function submitUserToScalekit(req, res, user) {
  const login_request_id = req.session.mcp_login_request_id;
  const state = req.session.mcp_state;

  if (!login_request_id || !state) {
    return res.status(400).send('Session expired');
  }

  try {
    // Submit user details to Scalekit
    await scalekit.auth.updateLoginUserDetails(
      CONNECTION_ID,
      login_request_id,
      {
        sub: user.id.toString(),        // Your user ID
        email: user.email,               // User email (required)
        name: user.name,                 // Full name (optional)
        given_name: user.firstName,      // First name (optional)
        family_name: user.lastName,      // Last name (optional)
        // Add custom claims as needed
        roles: user.roles,
        organization_id: user.orgId
      }
    );

    // Redirect back to Scalekit to complete OAuth
    const callbackUrl = `${process.env.SCALEKIT_ENVIRONMENT_URL}/sso/v1/connections/${CONNECTION_ID}/partner:callback?state=${state}`;

    res.redirect(callbackUrl);
  } catch (error) {
    console.error('Scalekit submission error:', error);
    res.status(500).send('Failed to complete authentication');
  }
}
```

**Python:**
```python
from scalekit import ScalekitClient

scalekit = ScalekitClient(
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET")
)

async def submit_user_to_scalekit(request: Request, user: dict):
    login_request_id = request.session.get("mcp_login_request_id")
    state = request.session.get("mcp_state")

    if not login_request_id or not state:
        raise HTTPException(status_code=400, detail="Session expired")

    try:
        # Submit user details to Scalekit
        scalekit.auth.update_login_user_details(
            connection_id=CONNECTION_ID,
            login_request_id=login_request_id,
            user={
                "sub": str(user["id"]),
                "email": user["email"],
                "name": user["name"],
                "given_name": user.get("first_name"),
                "family_name": user.get("last_name"),
                # Custom claims
                "roles": user.get("roles"),
                "organization_id": user.get("org_id")
            }
        )

        # Redirect back to Scalekit
        callback_url = f"{os.getenv('SCALEKIT_ENVIRONMENT_URL')}/sso/v1/connections/{CONNECTION_ID}/partner:callback?state={state}"

        return RedirectResponse(url=callback_url)

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to complete authentication")
```

## Complete Example: Username/Password

**login.html template:**
```html
<!DOCTYPE html>
<html>
  <head>
    <title>MCP Server Login</title>
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        max-width: 400px;
        margin: 100px auto;
        padding: 20px;
      }
      input {
        width: 100%;
        padding: 12px;
        margin: 8px 0;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-sizing: border-box;
      }
      button {
        width: 100%;
        background: #0070f3;
        color: white;
        padding: 12px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 16px;
      }
      button:hover {
        background: #0051cc;
      }
    </style>
  </head>
  <body>
    <h1>Sign In to MCP Server</h1>

    <form method="POST" action="/auth/mcp-login/submit">
      <input type="hidden" name="login_request_id" value="{{ login_request_id }}" />
      <input type="hidden" name="state" value="{{ state }}" />

      <input
        type="text"
        name="username"
        placeholder="Username"
        required
        autofocus
      />

      <input
        type="password"
        name="password"
        placeholder="Password"
        required
      />

      <button type="submit">Sign In</button>
    </form>
  </body>
</html>
```

**Server code:**
```javascript
// Full implementation
import express from 'express';
import session from 'express-session';
import { Scalekit } from '@scalekit-sdk/node';

const app = express();
const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

const CONNECTION_ID = process.env.SCALEKIT_CONNECTION_ID;

app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false
}));

// Step 1: Receive login redirect from Scalekit
app.get('/auth/mcp-login', (req, res) => {
  const { login_request_id, state } = req.query;

  req.session.mcp_login_request_id = login_request_id;
  req.session.mcp_state = state;
  req.session.save();

  res.render('mcp-login', { login_request_id, state });
});

// Step 2: Handle login form submission
app.post('/auth/mcp-login/submit', async (req, res) => {
  const { username, password } = req.body;

  try {
    // YOUR authentication logic
    const user = await db.users.findOne({
      username,
      password: hashPassword(password) // Use proper password hashing!
    });

    if (!user) {
      return res.render('mcp-login', {
        error: 'Invalid credentials',
        login_request_id: req.session.mcp_login_request_id,
        state: req.session.mcp_state
      });
    }

    // Step 3: Submit user to Scalekit
    await scalekit.auth.updateLoginUserDetails(
      CONNECTION_ID,
      req.session.mcp_login_request_id,
      {
        sub: user.id.toString(),
        email: user.email,
        name: user.name
      }
    );

    // Step 4: Redirect back to Scalekit
    const callbackUrl = `${process.env.SCALEKIT_ENVIRONMENT_URL}/sso/v1/connections/${CONNECTION_ID}/partner:callback?state=${req.session.mcp_state}`;

    res.redirect(callbackUrl);
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).send('Authentication failed');
  }
});

app.listen(3000);
```

## Integration Patterns

### Pattern 1: SSO Integration

If you have SSO, verify the SSO token and pass user details:

```javascript
app.get('/auth/mcp-login/sso', async (req, res) => {
  const ssoToken = req.cookies.sso_token;

  try {
    // Validate YOUR SSO token
    const user = await validateSSOToken(ssoToken);

    await scalekit.auth.updateLoginUserDetails(
      CONNECTION_ID,
      req.session.mcp_login_request_id,
      {
        sub: user.id.toString(),
        email: user.email,
        name: user.name
      }
    );

    const callbackUrl = `${process.env.SCALEKIT_ENVIRONMENT_URL}/sso/v1/connections/${CONNECTION_ID}/partner:callback?state=${req.session.mcp_state}`;

    res.redirect(callbackUrl);
  } catch (error) {
    res.redirect('/auth/mcp-login'); // Fall back to manual login
  }
});
```

### Pattern 2: API Key Authentication

For service accounts or API-based auth:

```javascript
app.post('/auth/mcp-login/api-key', async (req, res) => {
  const { api_key } = req.body;

  try {
    // Validate API key
    const serviceAccount = await db.apiKeys.findOne({ key: api_key });

    if (!serviceAccount || !serviceAccount.isActive) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    await scalekit.auth.updateLoginUserDetails(
      CONNECTION_ID,
      req.session.mcp_login_request_id,
      {
        sub: serviceAccount.id.toString(),
        email: serviceAccount.email,
        name: serviceAccount.name
      }
    );

    const callbackUrl = `${process.env.SCALEKIT_ENVIRONMENT_URL}/sso/v1/connections/${CONNECTION_ID}/partner:callback?state=${req.session.mcp_state}`;

    res.redirect(callbackUrl);
  } catch (error) {
    res.status(500).json({ error: 'Authentication failed' });
  }
});
```

### Pattern 3: JWT Token Validation

If you use JWTs for auth:

```javascript
import jwt from 'jsonwebtoken';

app.post('/auth/mcp-login/jwt', async (req, res) => {
  const { token } = req.body;

  try {
    // Verify YOUR JWT
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    await scalekit.auth.updateLoginUserDetails(
      CONNECTION_ID,
      req.session.mcp_login_request_id,
      {
        sub: decoded.user_id.toString(),
        email: decoded.email,
        name: decoded.name
      }
    );

    const callbackUrl = `${process.env.SCALEKIT_ENVIRONMENT_URL}/sso/v1/connections/${CONNECTION_ID}/partner:callback?state=${req.session.mcp_state}`;

    res.redirect(callbackUrl);
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' });
  }
});
```

## MCP Server Token Validation

After Scalekit issues OAuth tokens, your MCP server validates them:

```javascript
import { Scalekit } from '@scalekit-sdk/node';

const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

async function authMiddleware(req, res, next) {
  const token = req.headers['authorization']?.split('Bearer ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Missing token' });
  }

  try {
    const claims = await scalekit.validateToken(token, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
      audience: [process.env.RESOURCE_ID]
    });

    // Claims include your custom user data
    req.user = {
      id: claims.sub,              // Your user ID
      email: claims.email,
      name: claims.name,
      roles: claims.roles,         // Your custom claims
      orgId: claims.organization_id
    };

    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' });
  }
}
```

## Complete Flow Example

```
1. MCP Client → Scalekit OAuth Server
   "I want to access MCP server"

2. Scalekit → Your Login URL
   GET /auth/mcp-login?login_request_id=lri_123&state=xyz

3. Your Login Page → User
   Shows your branded login form

4. User → Your Server
   POST /auth/mcp-login/submit
   { username, password }

5. Your Server validates credentials
   user = authenticate(username, password)

6. Your Server → Scalekit API
   POST /api/v1/connections/{conn_id}/auth-requests/{login_request_id}/user
   { sub: user.id, email: user.email, name: user.name }

7. Your Server → Scalekit Callback
   Redirect to: /sso/v1/connections/{conn_id}/partner:callback?state=xyz

8. Scalekit → MCP Client
   Issues OAuth access token

9. MCP Client → Your MCP Server
   Authorization: Bearer <access_token>

10. Your MCP Server → Scalekit
    Validates token, extracts user claims

11. Your MCP Server → MCP Client
    Returns protected data
```

## Security Considerations

### 1. Validate State Parameter

Always pass back the exact `state` value:

```javascript
const state = req.session.mcp_state;
if (!state) {
  return res.status(400).send('Invalid state');
}

// Use in redirect
const callbackUrl = `...?state=${state}`;
```

### 2. Session Security

Protect session data:

```javascript
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: true,      // HTTPS only
    httpOnly: true,
    sameSite: 'strict'
  }
}));
```

### 3. CSRF Protection

For form-based login:

```javascript
import csrf from 'csurf';

const csrfProtection = csrf({ cookie: true });

app.get('/auth/mcp-login', csrfProtection, (req, res) => {
  res.render('mcp-login', {
    csrfToken: req.csrfToken(),
    login_request_id,
    state
  });
});

app.post('/auth/mcp-login/submit', csrfProtection, async (req, res) => {
  // Handles login
});
```

## Troubleshooting

### Redirect Loop

**Symptoms:** Login page keeps redirecting

**Solutions:**
- Ensure `state` parameter is passed correctly
- Check session is being saved before redirect
- Verify callback URL format

### User Details Rejected

**Symptoms:** Scalekit API returns error

**Solutions:**
- `sub` and `email` are required fields
- `sub` must be a string
- Email must be valid format
- Check API credentials are correct

### Token Validation Fails

**Symptoms:** MCP requests return 401

**Solutions:**
- Verify token is in `Authorization: Bearer <token>` header
- Check issuer matches Scalekit environment URL
- Ensure audience includes Resource ID
- Token may have expired

## Production Checklist

- [ ] HTTPS enabled for login endpoint
- [ ] Session secret is cryptographically random
- [ ] CSRF protection enabled
- [ ] Rate limiting on login endpoint
- [ ] Logging for authentication events
- [ ] Error messages don't leak info
- [ ] Connection ID configured correctly
- [ ] Test full OAuth flow end-to-end

## Next Steps

- See [templates/nodejs-mcp-custom.md](templates/nodejs-mcp-custom.md) for complete example
- Review [oauth-quickstart.md](oauth-quickstart.md) for Scalekit-managed auth
- Read [../reference/mcp-best-practices.md](../reference/mcp-best-practices.md) for security patterns
