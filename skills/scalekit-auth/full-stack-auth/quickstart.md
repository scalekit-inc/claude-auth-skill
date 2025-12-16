# Full-Stack Authentication Quickstart

## Overview

This guide walks through implementing Scalekit's complete authentication system in your web application. By the end, you'll have:

- User login and sign-up flows
- Secure session management
- Token refresh handling
- User logout
- Protected routes/endpoints

**Time to implement:** 30-45 minutes

## Architecture Overview

```
User Browser                Your Application              Scalekit
    |                              |                          |
    |---(1) Click Login----------->|                          |
    |                              |                          |
    |<---(2) Redirect to Scalekit--|                          |
    |                              |                          |
    |---(3) Login with Credentials-------------------------->|
    |                              |                          |
    |<---(4) Redirect with Code-----------------------------|
    |                              |                          |
    |---(5) Send Code------------->|                          |
    |                              |---(6) Exchange Code---->|
    |                              |<---(7) Return Tokens----|
    |                              |                          |
    |<---(8) Set Session Cookies---|                          |
    |                              |                          |
    |---(9) Access Protected------>|                          |
    |     Route                    |                          |
```

## Step-by-Step Implementation

### Step 1: Environment Setup

**1.1 Create `.env` file:**

```bash
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_12345...
SCALEKIT_CLIENT_SECRET=test_12345...

# Application settings
APP_URL=http://localhost:3000
CALLBACK_URL=http://localhost:3000/auth/callback
POST_LOGOUT_URL=http://localhost:3000

# Cookie settings (adjust for production)
COOKIE_SECURE=false  # Set to true in production with HTTPS
```

**1.2 Register callback URL in Scalekit Dashboard:**

1. Go to https://app.scalekit.com
2. Navigate to Settings → Redirect URIs
3. Add `http://localhost:3000/auth/callback` for development
4. Add your production callback URL when deploying

**1.3 Validate environment:**

```bash
python scripts/validate_env.py
```

### Step 2: Install SDK and Dependencies

**Node.js:**
```bash
npm install @scalekit-sdk/node
npm install express cookie-parser dotenv
```

**Python:**
```bash
pip install scalekit-sdk-python
pip install fastapi uvicorn python-dotenv
```

### Step 3: Initialize Scalekit Client

Create a centralized client instance:

**Node.js (lib/scalekit.js):**
```javascript
import { Scalekit } from '@scalekit-sdk/node';
import dotenv from 'dotenv';

dotenv.config();

export const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

export const CALLBACK_URL = process.env.CALLBACK_URL;
export const POST_LOGOUT_URL = process.env.POST_LOGOUT_URL;
```

**Python (lib/scalekit.py):**
```python
from scalekit import ScalekitClient
import os
from dotenv import load_dotenv

load_dotenv()

scalekit = ScalekitClient(
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET")
)

CALLBACK_URL = os.getenv("CALLBACK_URL")
POST_LOGOUT_URL = os.getenv("POST_LOGOUT_URL")
```

### Step 4: Implement Login Endpoint

**Node.js:**
```javascript
import express from 'express';
import { scalekit, CALLBACK_URL } from './lib/scalekit.js';

const app = express();

app.get('/auth/login', (req, res) => {
  const authorizationUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
    scopes: ['openid', 'profile', 'email', 'offline_access']
  });

  res.redirect(authorizationUrl);
});
```

**Python:**
```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from lib.scalekit import scalekit, CALLBACK_URL

app = FastAPI()

@app.get("/auth/login")
async def login():
    authorization_url = scalekit.get_authorization_url(
        redirect_uri=CALLBACK_URL,
        options={
            "scopes": ["openid", "profile", "email", "offline_access"]
        }
    )
    return RedirectResponse(url=authorization_url)
```

### Step 5: Implement Callback Handler

This endpoint receives the authorization code and exchanges it for tokens.

**Node.js:**
```javascript
import cookieParser from 'cookie-parser';

app.use(cookieParser());

app.get('/auth/callback', async (req, res) => {
  try {
    const { code } = req.query;

    if (!code) {
      return res.status(400).send('Authorization code missing');
    }

    // Exchange code for tokens
    const result = await scalekit.authenticateWithCode(code, CALLBACK_URL);

    // Extract tokens and user info
    const { accessToken, refreshToken, idToken, user, expiresIn } = result;

    // Set secure cookies
    const cookieOptions = {
      httpOnly: true,
      secure: process.env.COOKIE_SECURE === 'true',
      sameSite: 'strict'
    };

    res.cookie('accessToken', accessToken, {
      ...cookieOptions,
      maxAge: expiresIn * 1000 // Convert to milliseconds
    });

    res.cookie('refreshToken', refreshToken, {
      ...cookieOptions,
      maxAge: 30 * 24 * 60 * 60 * 1000 // 30 days
    });

    res.cookie('idToken', idToken, {
      ...cookieOptions,
      maxAge: expiresIn * 1000
    });

    // Store user info (optional)
    res.cookie('user', JSON.stringify(user), {
      maxAge: expiresIn * 1000,
      secure: process.env.COOKIE_SECURE === 'true',
      sameSite: 'strict'
      // Note: Not httpOnly so frontend can access user info
    });

    // Redirect to dashboard or home
    res.redirect('/dashboard');
  } catch (error) {
    console.error('Authentication error:', error);
    res.status(500).send('Authentication failed');
  }
});
```

**Python:**
```python
from fastapi import Cookie, Response
from fastapi.responses import RedirectResponse
import json

@app.get("/auth/callback")
async def callback(code: str, response: Response):
    try:
        # Exchange code for tokens
        result = scalekit.authenticate_with_code(
            code=code,
            redirect_uri=CALLBACK_URL
        )

        # Extract tokens
        access_token = result.access_token
        refresh_token = result.refresh_token
        id_token = result.id_token
        user = result.user
        expires_in = result.expires_in

        # Create redirect response
        redirect = RedirectResponse(url="/dashboard", status_code=302)

        # Set secure cookies
        cookie_secure = os.getenv("COOKIE_SECURE", "false") == "true"

        redirect.set_cookie(
            key="accessToken",
            value=access_token,
            httponly=True,
            secure=cookie_secure,
            samesite="strict",
            max_age=expires_in
        )

        redirect.set_cookie(
            key="refreshToken",
            value=refresh_token,
            httponly=True,
            secure=cookie_secure,
            samesite="strict",
            max_age=30 * 24 * 60 * 60  # 30 days
        )

        redirect.set_cookie(
            key="idToken",
            value=id_token,
            httponly=True,
            secure=cookie_secure,
            samesite="strict",
            max_age=expires_in
        )

        redirect.set_cookie(
            key="user",
            value=json.dumps(user.__dict__),
            secure=cookie_secure,
            samesite="strict",
            max_age=expires_in
        )

        return redirect

    except Exception as error:
        print(f"Authentication error: {error}")
        return {"error": "Authentication failed"}, 500
```

### Step 6: Create Authentication Middleware

**Node.js (middleware/auth.js):**
```javascript
import { scalekit } from '../lib/scalekit.js';

export async function authMiddleware(req, res, next) {
  try {
    const accessToken = req.cookies.accessToken;

    if (!accessToken) {
      return res.redirect('/auth/login');
    }

    // Validate token
    try {
      const claims = await scalekit.validateAccessToken(accessToken);
      req.user = claims;
      next();
    } catch (validationError) {
      // Token invalid or expired, try to refresh
      const refreshToken = req.cookies.refreshToken;

      if (!refreshToken) {
        return res.redirect('/auth/login');
      }

      try {
        const result = await scalekit.refreshAccessToken(refreshToken);

        // Update cookies with new tokens
        const cookieOptions = {
          httpOnly: true,
          secure: process.env.COOKIE_SECURE === 'true',
          sameSite: 'strict'
        };

        res.cookie('accessToken', result.accessToken, {
          ...cookieOptions,
          maxAge: result.expiresIn * 1000
        });

        if (result.refreshToken) {
          res.cookie('refreshToken', result.refreshToken, {
            ...cookieOptions,
            maxAge: 30 * 24 * 60 * 60 * 1000
          });
        }

        // Validate new token and continue
        const claims = await scalekit.validateAccessToken(result.accessToken);
        req.user = claims;
        next();
      } catch (refreshError) {
        // Refresh failed, redirect to login
        res.clearCookie('accessToken');
        res.clearCookie('refreshToken');
        res.clearCookie('idToken');
        res.clearCookie('user');
        return res.redirect('/auth/login');
      }
    }
  } catch (error) {
    console.error('Auth middleware error:', error);
    res.status(500).send('Internal server error');
  }
}
```

**Python (middleware/auth.py):**
```python
from fastapi import Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from lib.scalekit import scalekit
import os

async def require_auth(request: Request, response: Response):
    access_token = request.cookies.get("accessToken")

    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Validate token
        claims = scalekit.validate_access_token(access_token)
        return claims
    except Exception as validation_error:
        # Token invalid or expired, try to refresh
        refresh_token = request.cookies.get("refreshToken")

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Session expired")

        try:
            result = scalekit.refresh_access_token(refresh_token)

            # Update cookies
            cookie_secure = os.getenv("COOKIE_SECURE", "false") == "true"

            response.set_cookie(
                key="accessToken",
                value=result.access_token,
                httponly=True,
                secure=cookie_secure,
                samesite="strict",
                max_age=result.expires_in
            )

            if result.refresh_token:
                response.set_cookie(
                    key="refreshToken",
                    value=result.refresh_token,
                    httponly=True,
                    secure=cookie_secure,
                    samesite="strict",
                    max_age=30 * 24 * 60 * 60
                )

            # Validate new token
            claims = scalekit.validate_access_token(result.access_token)
            return claims
        except Exception as refresh_error:
            # Clear cookies
            response.delete_cookie("accessToken")
            response.delete_cookie("refreshToken")
            response.delete_cookie("idToken")
            response.delete_cookie("user")
            raise HTTPException(status_code=401, detail="Session expired")
```

### Step 7: Protect Routes

**Node.js:**
```javascript
import { authMiddleware } from './middleware/auth.js';

// Protect specific routes
app.get('/dashboard', authMiddleware, (req, res) => {
  res.json({
    message: 'Welcome to your dashboard',
    user: req.user
  });
});

// Protect all API routes
app.use('/api', authMiddleware);

app.get('/api/profile', (req, res) => {
  res.json({
    user: req.user
  });
});
```

**Python:**
```python
from fastapi import Depends
from middleware.auth import require_auth

@app.get("/dashboard")
async def dashboard(user = Depends(require_auth)):
    return {
        "message": "Welcome to your dashboard",
        "user": user
    }

@app.get("/api/profile")
async def profile(user = Depends(require_auth)):
    return {"user": user}
```

### Step 8: Implement Logout

**Node.js:**
```javascript
import { scalekit, POST_LOGOUT_URL } from './lib/scalekit.js';

app.get('/auth/logout', (req, res) => {
  const idToken = req.cookies.idToken;

  // Clear cookies
  res.clearCookie('accessToken');
  res.clearCookie('refreshToken');
  res.clearCookie('idToken');
  res.clearCookie('user');

  // Generate Scalekit logout URL
  const logoutUrl = scalekit.getLogoutUrl(idToken, POST_LOGOUT_URL);

  res.redirect(logoutUrl);
});
```

**Python:**
```python
from lib.scalekit import scalekit, POST_LOGOUT_URL

@app.get("/auth/logout")
async def logout(request: Request):
    id_token = request.cookies.get("idToken")

    # Generate logout URL
    logout_url = scalekit.get_logout_url(
        id_token_hint=id_token,
        post_logout_redirect_uri=POST_LOGOUT_URL
    )

    # Create redirect and clear cookies
    response = RedirectResponse(url=logout_url)
    response.delete_cookie("accessToken")
    response.delete_cookie("refreshToken")
    response.delete_cookie("idToken")
    response.delete_cookie("user")

    return response
```

## Testing the Implementation

### 1. Start your application

**Node.js:**
```bash
node app.js
# Visit http://localhost:3000
```

**Python:**
```bash
uvicorn app:app --reload
# Visit http://localhost:8000
```

### 2. Test the flow

1. Navigate to `/auth/login`
2. You'll be redirected to Scalekit
3. Sign up or log in
4. After authentication, you'll be redirected to `/dashboard`
5. Access protected routes (should work)
6. Navigate to `/auth/logout`
7. Try accessing protected routes (should redirect to login)

### 3. Validate with scripts

```bash
# Test environment setup
python scripts/validate_env.py

# Test Scalekit connectivity
python scripts/test_connection.py

# Interactive auth flow test
python scripts/test_auth_flow.py
```

## Next Steps

### Add Frontend Login Button

**HTML:**
```html
<a href="/auth/login">
  <button>Sign In with Scalekit</button>
</a>
```

**React:**
```jsx
function LoginButton() {
  return (
    <button onClick={() => window.location.href = '/auth/login'}>
      Sign In with Scalekit
    </button>
  );
}
```

### Display User Information

**Node.js:**
```javascript
app.get('/api/me', authMiddleware, (req, res) => {
  const user = JSON.parse(req.cookies.user || '{}');
  res.json(user);
});
```

**Python:**
```python
@app.get("/api/me")
async def get_current_user(request: Request):
    user = request.cookies.get("user")
    return json.loads(user) if user else {}
```

### Enable Additional Auth Methods

1. Go to Scalekit Dashboard → Authentication
2. Enable desired methods:
   - Social login (Google, GitHub, Microsoft)
   - Magic link / Email OTP
   - Enterprise SSO (for B2B customers)
3. No code changes required - users will see new options automatically

## Production Checklist

Before deploying to production:

- [ ] Set `COOKIE_SECURE=true` in environment
- [ ] Use HTTPS for all URLs
- [ ] Register production callback URLs in Scalekit Dashboard
- [ ] Configure CORS properly
- [ ] Add error logging and monitoring
- [ ] Test token refresh flow
- [ ] Test logout flow
- [ ] Set appropriate token expiration times in Scalekit Dashboard
- [ ] Review security best practices: [reference/security-best-practices.md](../reference/security-best-practices.md)

## Troubleshooting

**"Redirect URI mismatch" error:**
- Verify callback URL in code matches exactly what's registered in Dashboard
- Include protocol and port

**Tokens not being set:**
- Check cookie settings (secure flag in production)
- Verify domain matches

**Session not persisting:**
- Ensure cookies are HttpOnly
- Check sameSite settings
- Verify max-age is set correctly

**CORS errors:**
- Configure CORS middleware to allow credentials
- Set proper allowed origins

For more help, see [reference/troubleshooting.md](../reference/troubleshooting.md)

## Complete Examples

For fully working examples, see:
- [Node.js + Express template](templates/nodejs-express.md)
- [Next.js App Router template](templates/nextjs.md)
- [Python + FastAPI template](templates/python-fastapi.md)
