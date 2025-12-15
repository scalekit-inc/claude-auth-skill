---
name: scalekit-auth
description: Implement authentication with Scalekit for web applications. Handles sign-up, login, logout, session management, token validation, and refresh flows. Supports Node.js, Next.js, Python, FastAPI, and Express. Use when adding authentication, implementing login/signup flows, managing user sessions, or securing web applications.
---

# Scalekit Authentication Implementation

## Overview

This skill helps you implement Scalekit's full-stack authentication system in your web application. Scalekit provides a managed authentication solution that handles:

- User sign-up and login
- Session management with secure token storage
- Token refresh and validation
- Logout flows
- Support for multiple authentication methods (passwordless, social login, enterprise SSO)

## Quick Start

**Choose your framework to get started:**

1. **Node.js + Express** → See [templates/nodejs-express.md](full-stack-auth/templates/nodejs-express.md)
2. **Next.js (App Router)** → See [templates/nextjs.md](full-stack-auth/templates/nextjs.md)
3. **Python + FastAPI** → See [templates/python-fastapi.md](full-stack-auth/templates/python-fastapi.md)

Or follow the comprehensive guide: [Full-Stack Auth Quickstart](full-stack-auth/quickstart.md)

## Prerequisites

Before implementing, ensure you have:

1. **Scalekit Account**: Sign up at https://scalekit.com
2. **Environment Variables**: From your Scalekit Dashboard → Settings
   - `SCALEKIT_ENVIRONMENT_URL`
   - `SCALEKIT_CLIENT_ID`
   - `SCALEKIT_CLIENT_SECRET`
3. **Callback URL Registered**: Add your redirect URI in Scalekit Dashboard

**Validate your setup:**
```bash
python scripts/validate_env.py
```

## Implementation Workflow

### Step 1: Install SDK

Choose your language:

**Node.js:**
```bash
npm install @scalekit-sdk/node
```

**Python:**
```bash
pip install scalekit-sdk-python
```

### Step 2: Initialize Client

**Node.js:**
```javascript
import { Scalekit } from '@scalekit-sdk/node';

const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);
```

**Python:**
```python
from scalekit import ScalekitClient

scalekit = ScalekitClient(
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET")
)
```

### Step 3: Implement Core Flows

The skill guides you through implementing:

1. **Login Flow**
   - Generate authorization URL with required scopes
   - Redirect user to Scalekit login page
   - Handle callback and exchange code for tokens

2. **Session Management**
   - Store tokens securely in HttpOnly cookies
   - Validate access tokens on protected routes
   - Refresh tokens when expired

3. **Logout Flow**
   - Generate logout URL
   - Clear session cookies
   - Redirect to post-logout page

See [full-stack-auth/quickstart.md](full-stack-auth/quickstart.md) for detailed implementation.

### Step 4: Add Middleware Protection

**Node.js Express:**
```javascript
import { authMiddleware } from './middleware/auth';

// Protect routes
app.use('/api/protected', authMiddleware);
app.use('/dashboard', authMiddleware);
```

**Python FastAPI:**
```python
from middleware.auth import require_auth

@app.get("/api/protected")
async def protected_route(user = Depends(require_auth)):
    return {"user": user}
```

## Required Scopes

For full-stack authentication, request these scopes:

- `openid` - User identity (required)
- `profile` - User profile data (name, etc.)
- `email` - Email address
- `offline_access` - Enables refresh tokens

Example:
```javascript
const authUrl = scalekit.getAuthorizationUrl(
  'http://localhost:3000/auth/callback',
  {
    scopes: ['openid', 'profile', 'email', 'offline_access']
  }
);
```

## Session Configuration

**Recommended cookie settings:**

```javascript
{
  httpOnly: true,        // Prevent XSS attacks
  secure: true,          // HTTPS only (use false in development)
  sameSite: 'strict',    // CSRF protection
  maxAge: 3600000,       // 1 hour for access token
  path: '/'              // Cookie scope
}
```

Store tokens in separate cookies:
- `accessToken` - Short-lived (5-60 minutes)
- `refreshToken` - Long-lived (days to months)
- `idToken` - User identity claims

See [reference/session-management.md](reference/session-management.md) for best practices.

## Token Validation

**On every protected request:**

```javascript
try {
  const claims = await scalekit.validateAccessToken(accessToken);
  // User is authenticated, proceed with request
  req.user = claims;
} catch (error) {
  // Token invalid or expired
  // Attempt to refresh or redirect to login
}
```

**When access token expires:**

```javascript
try {
  const result = await scalekit.refreshAccessToken(refreshToken);
  // Update cookies with new tokens
  setTokenCookies(result.accessToken, result.refreshToken);
} catch (error) {
  // Refresh failed, redirect to login
}
```

## Reference Documentation

- **[Session Management](reference/session-management.md)** - Token storage, refresh patterns, cookie security
- **[Security Best Practices](reference/security-best-practices.md)** - CORS, CSP, XSS prevention
- **[Environment Setup](reference/environment-setup.md)** - Configuration guide for all supported languages

## Validation Scripts

Before deploying to production, run:

```bash
# Validate environment variables
python scripts/validate_env.py

# Test Scalekit connectivity
python scripts/test_connection.py

# Validate token flow (interactive)
python scripts/test_auth_flow.py
```

## Common Issues & Troubleshooting

**Redirect URI mismatch:**
- Ensure the callback URL in your code exactly matches the one registered in Scalekit Dashboard
- Include protocol (http:// or https://) and port if not standard (80/443)

**Token validation fails:**
- Check that tokens are being passed correctly (Bearer header or cookie)
- Verify environment variables are loaded
- Ensure access token hasn't expired (check `exp` claim)

**CORS errors:**
- Configure CORS to allow your frontend domain
- Include credentials in fetch requests: `credentials: 'include'`

**Session not persisting:**
- Verify cookies are HttpOnly and Secure (in production)
- Check sameSite settings match your domain setup
- Ensure cookie path is correct

For more help, see [reference/troubleshooting.md](reference/troubleshooting.md)

## Framework-Specific Examples

**Quick copy-paste implementations:**

- [Node.js + Express](full-stack-auth/templates/nodejs-express.md) - Complete Express app with auth
- [Next.js App Router](full-stack-auth/templates/nextjs.md) - App Router with server actions
- [Python + FastAPI](full-stack-auth/templates/python-fastapi.md) - FastAPI with dependency injection

## Next Steps

After implementing authentication:

1. **Add Authorization** - Implement role-based access control
2. **Enable Social Login** - Configure Google, GitHub, Microsoft in Scalekit Dashboard
3. **Add Enterprise SSO** - Enable SAML/OIDC for B2B customers
4. **Customize UI** - White-label the login experience

See Scalekit documentation at https://docs.scalekit.com for advanced features.

---

**Note:** This prototype focuses on full-stack authentication. Additional implementation paths (Modular SSO, MCP Server Auth) will be added in future versions.
