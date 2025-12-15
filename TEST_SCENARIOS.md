# Quick Test Scenarios

This document provides ready-to-use test prompts for validating the Scalekit authentication skill. Copy and paste these into Claude Code to test functionality.

## How to Use This Guide

1. Install the skill (see TESTING.md)
2. Copy a prompt from below
3. Paste into Claude Code
4. Verify the expected behavior
5. Check the validation points

---

## Category 1: Basic Activation Tests

### Scenario 1.1: Explicit Scalekit Request

**Prompt:**
```
Help me implement Scalekit authentication
```

**Expected Behavior:**
- ✅ Skill activates
- ✅ Asks which framework you're using
- ✅ Mentions installation options

**Validation:**
- Does Claude mention Scalekit SDK?
- Does it reference framework templates?
- Does it offer step-by-step guidance?

---

### Scenario 1.2: Framework + Auth Mention

**Prompt:**
```
I need to add authentication to my Express.js application using Scalekit
```

**Expected Behavior:**
- ✅ Skill activates
- ✅ Identifies Express framework
- ✅ Provides Express-specific code

**Validation:**
- Does code use Express patterns (app.get, res.cookie, etc.)?
- Are Express dependencies mentioned?
- Is code complete (not just snippets)?

---

## Category 2: Node.js/Express Tests

### Scenario 2.1: Basic Express Setup

**Prompt:**
```
I have an Express 4.x application. Show me how to integrate Scalekit for user authentication with login, logout, and session management.
```

**Expected Output Check:**
```javascript
// Should include:
import { Scalekit } from '@scalekit-sdk/node';
import cookieParser from 'cookie-parser';

// Client initialization
const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

// Login route
app.get('/auth/login', (req, res) => {
  const authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
    scopes: ['openid', 'profile', 'email', 'offline_access']
  });
  res.redirect(authUrl);
});

// Callback route with token exchange
app.get('/auth/callback', async (req, res) => {
  const { code } = req.query;
  const result = await scalekit.authenticateWithCode(code, CALLBACK_URL);
  // ... set cookies
});

// Auth middleware
async function authMiddleware(req, res, next) {
  const accessToken = req.cookies.accessToken;
  try {
    const claims = await scalekit.validateAccessToken(accessToken);
    req.user = claims;
    next();
  } catch (error) {
    // Refresh logic
  }
}
```

**Validation Checklist:**
- [ ] Complete imports present
- [ ] Environment variables referenced
- [ ] All auth routes (login, callback, logout)
- [ ] Cookie configuration with httpOnly, secure, sameSite
- [ ] Auth middleware with refresh logic
- [ ] Protected route example
- [ ] Error handling

---

### Scenario 2.2: Express with TypeScript

**Prompt:**
```
I'm using Express with TypeScript. Help me add Scalekit authentication with proper types.
```

**Expected Output Check:**
```typescript
import { Scalekit } from '@scalekit-sdk/node';
import { Request, Response, NextFunction } from 'express';

interface AuthRequest extends Request {
  user?: any;
}

async function authMiddleware(
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> {
  // ...
}
```

**Validation:**
- [ ] TypeScript syntax used
- [ ] Type annotations present
- [ ] Interface definitions for extended Request
- [ ] Proper async/Promise types

---

## Category 3: Next.js Tests

### Scenario 3.1: Next.js App Router Setup

**Prompt:**
```
I'm building with Next.js 14 and the App Router. Implement Scalekit authentication with server components, route handlers, and protected pages.
```

**Expected Output Check:**
```typescript
// lib/scalekit.ts
export const scalekit = new Scalekit(...);

// lib/auth.ts
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export async function requireAuth() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get('accessToken')?.value;
  // ...
}

// app/auth/login/route.ts
export async function GET(request: NextRequest) {
  // ...
}

// app/dashboard/page.tsx
export default async function Dashboard() {
  await requireAuth(); // Server-side auth
  // ...
}
```

**Validation Checklist:**
- [ ] TypeScript used
- [ ] Uses `next/headers` for cookies
- [ ] Uses `redirect()` from `next/navigation`
- [ ] Route handlers in app/auth/*/route.ts
- [ ] Server components (async function)
- [ ] No client-side cookie access in protected pages

---

### Scenario 3.2: Next.js with Server Actions

**Prompt:**
```
Show me how to implement logout using Next.js server actions
```

**Expected Output Check:**
```typescript
// app/actions/auth.ts
'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

export async function logout() {
  const cookieStore = await cookies();
  // Clear cookies
  cookieStore.delete('accessToken');
  // ...
  redirect('/');
}

// Usage in component
import { logout } from '@/app/actions/auth';

export function LogoutButton() {
  return (
    <form action={logout}>
      <button type="submit">Logout</button>
    </form>
  );
}
```

**Validation:**
- [ ] 'use server' directive present
- [ ] Async server action
- [ ] Cookie deletion
- [ ] Form action usage shown

---

## Category 4: Python/FastAPI Tests

### Scenario 4.1: FastAPI Basic Setup

**Prompt:**
```
Implement Scalekit authentication in my FastAPI application with dependency injection for protected routes.
```

**Expected Output Check:**
```python
from fastapi import FastAPI, Depends, Request, Response
from scalekit import ScalekitClient

scalekit = ScalekitClient(
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET")
)

async def get_current_user(request: Request, response: Response):
    access_token = request.cookies.get("accessToken")
    try:
        claims = scalekit.validate_access_token(access_token)
        return claims
    except:
        # Refresh logic
        pass

@app.get("/api/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user": user}
```

**Validation Checklist:**
- [ ] ScalekitClient initialization
- [ ] Dependency function (get_current_user)
- [ ] Depends() used in routes
- [ ] Cookie handling with request.cookies
- [ ] Response cookie setting
- [ ] Type hints present
- [ ] Async/await used correctly

---

### Scenario 4.2: FastAPI with Token Refresh

**Prompt:**
```
Show me how to implement automatic token refresh in FastAPI middleware
```

**Expected Output Check:**
```python
async def get_current_user(request: Request, response: Response):
    access_token = request.cookies.get("accessToken")

    if not access_token:
        raise HTTPException(status_code=401)

    try:
        claims = scalekit.validate_access_token(access_token)
        return claims
    except:
        refresh_token = request.cookies.get("refreshToken")
        if not refresh_token:
            raise HTTPException(status_code=401)

        result = scalekit.refresh_access_token(refresh_token)

        # Update cookies
        response.set_cookie(
            key="accessToken",
            value=result.access_token,
            httponly=True,
            secure=True,
            samesite="strict"
        )

        return scalekit.validate_access_token(result.access_token)
```

**Validation:**
- [ ] Try-except for validation
- [ ] Refresh token retrieval
- [ ] response.set_cookie() usage
- [ ] HTTPException for errors
- [ ] Cookie flags (httponly, secure, samesite)

---

## Category 5: Security & Best Practices

### Scenario 5.1: Cookie Security

**Prompt:**
```
What are the security best practices for storing Scalekit tokens?
```

**Expected Mentions:**
- ✅ HttpOnly cookies (prevents XSS)
- ✅ Secure flag for HTTPS
- ✅ sameSite flag for CSRF protection
- ✅ Never use localStorage
- ✅ Short token lifetimes
- ✅ Token validation on every request

**Key Phrases to Look For:**
- "HttpOnly prevents JavaScript access"
- "secure flag requires HTTPS"
- "sameSite: 'strict' prevents CSRF"
- "never store tokens in localStorage"

---

### Scenario 5.2: Error Handling

**Prompt:**
```
How should I handle authentication errors in my Scalekit implementation?
```

**Expected Guidance:**
- ✅ Try-catch blocks around token operations
- ✅ Handle OAuth errors from callback
- ✅ Generic error messages to users
- ✅ Detailed logging server-side
- ✅ Graceful fallback to login

**Example Code Should Show:**
```javascript
try {
  const result = await scalekit.authenticateWithCode(code, callbackUrl);
} catch (error) {
  console.error('Auth error:', error); // Server log
  return res.status(500).json({
    error: 'Authentication failed' // Generic to user
  });
}
```

---

### Scenario 5.3: Token Refresh Strategy

**Prompt:**
```
Explain the token refresh strategy for Scalekit authentication
```

**Expected Explanation:**
- ✅ Access tokens are short-lived (5-60 min)
- ✅ Refresh tokens are long-lived (days)
- ✅ Refresh automatically when access token expires
- ✅ Store both tokens in separate HttpOnly cookies
- ✅ Clear all tokens if refresh fails

---

## Category 6: Troubleshooting

### Scenario 6.1: Environment Setup

**Prompt:**
```
I'm getting an error that SCALEKIT_CLIENT_ID is undefined. How do I fix this?
```

**Expected Response:**
- ✅ Mentions .env file
- ✅ Shows example .env content
- ✅ References validate_env.py script
- ✅ Explains to restart server after .env changes

---

### Scenario 6.2: Callback URL Mismatch

**Prompt:**
```
I'm getting a redirect_uri_mismatch error
```

**Expected Response:**
- ✅ Explains callback URL must match exactly
- ✅ Mentions protocol (http/https) and port
- ✅ References Scalekit Dashboard → Redirect URIs
- ✅ Shows example: http://localhost:3000/auth/callback

---

### Scenario 6.3: Cookies Not Persisting

**Prompt:**
```
Users are being logged out immediately after login
```

**Expected Troubleshooting:**
- ✅ Check secure flag (should be false for localhost)
- ✅ Check sameSite setting
- ✅ Verify browser accepts cookies
- ✅ Check cookie domain/path
- ✅ References session-management.md guide

---

## Category 7: Validation Scripts

### Scenario 7.1: Environment Validation

**Prompt:**
```
How do I verify my Scalekit environment is configured correctly?
```

**Expected Response:**
- ✅ Mentions validate_env.py script
- ✅ Shows how to run it
- ✅ Explains what it checks

**Expected Command:**
```bash
python scripts/validate_env.py
```

---

### Scenario 7.2: Connection Testing

**Prompt:**
```
How can I test if my Scalekit credentials work before implementing the full auth flow?
```

**Expected Response:**
- ✅ References test_connection.py
- ✅ Explains it tests SDK initialization
- ✅ Shows how to run it

**Expected Command:**
```bash
python scripts/test_connection.py
```

---

## Quick Validation Checklist

Use this checklist for each test:

**Code Quality:**
- [ ] Complete code (not snippets)
- [ ] All imports/requires present
- [ ] Environment variables used correctly
- [ ] No syntax errors
- [ ] Can be copy-pasted and run

**Security:**
- [ ] HttpOnly cookies for tokens
- [ ] Secure flag mentioned (production)
- [ ] sameSite attribute present
- [ ] Token validation on requests
- [ ] No localStorage for tokens

**Framework Accuracy:**
- [ ] Uses correct framework patterns
- [ ] Correct imports for framework
- [ ] Framework-specific features used
- [ ] No mixing of frameworks

**Completeness:**
- [ ] Login endpoint
- [ ] Callback handler
- [ ] Logout endpoint
- [ ] Auth middleware
- [ ] Protected route example
- [ ] Error handling

**Documentation:**
- [ ] Comments explain key parts
- [ ] Next steps mentioned
- [ ] References to guides
- [ ] Testing instructions

---

## Running All Tests

To systematically test the skill:

```bash
# 1. Create test log file
echo "# Scalekit Skill Test Results - $(date)" > test_results.md

# 2. For each scenario above:
#    - Copy prompt
#    - Paste into Claude Code
#    - Document results

# 3. Summary template:
cat >> test_results.md << 'EOF'

## Summary
- Total Scenarios: 20
- Passed: X
- Failed: Y
- Partial: Z

## Critical Issues
- [List any blocking issues]

## Minor Issues
- [List minor improvements needed]

## Recommendations
- [What to fix before customer release]
EOF
```

---

## Expected Test Duration

- **Quick validation** (5 key scenarios): ~15 minutes
- **Full category testing** (all 20 scenarios): ~1-2 hours
- **Real-world simulation**: ~30 minutes

Total comprehensive testing: **2-3 hours**

---

## Success Criteria

**Minimum to pass:**
- ✅ All Category 1 tests pass (Activation)
- ✅ At least 2/3 framework tests pass per framework
- ✅ All security checks pass
- ✅ Validation scripts work

**Ready for customer beta:**
- ✅ 90%+ of all tests pass
- ✅ All critical scenarios pass
- ✅ Code is copy-paste ready
- ✅ Security best practices enforced

**Ready for production:**
- ✅ 95%+ of all tests pass
- ✅ All frameworks tested thoroughly
- ✅ Edge cases handled
- ✅ Documentation complete
