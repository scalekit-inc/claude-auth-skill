# Session Management Best Practices

## Overview

Proper session management is critical for security and user experience. This guide covers best practices for handling tokens, cookies, and session lifecycles with Scalekit.

## Token Types

### Access Token
- **Purpose**: Authorizes API requests
- **Lifetime**: Short-lived (5-60 minutes, configurable in dashboard)
- **Storage**: HttpOnly cookie or Authorization header
- **Usage**: Validate on every protected request

### Refresh Token
- **Purpose**: Obtain new access tokens without re-authentication
- **Lifetime**: Long-lived (days to months, configurable)
- **Storage**: HttpOnly cookie with restricted path
- **Usage**: Exchange for new access token when expired

### ID Token
- **Purpose**: Contains user identity claims
- **Lifetime**: Matches access token lifetime
- **Storage**: HttpOnly cookie
- **Usage**: Logout flow, user info display

## Cookie Configuration

### Recommended Settings

**Production (HTTPS):**
```javascript
{
  httpOnly: true,        // Prevents JavaScript access (XSS protection)
  secure: true,          // HTTPS only
  sameSite: 'strict',    // CSRF protection
  path: '/',             // Cookie scope
  maxAge: 3600           // Expiration in seconds
}
```

**Development (HTTP):**
```javascript
{
  httpOnly: true,
  secure: false,         // Allow HTTP for localhost
  sameSite: 'strict',
  path: '/',
  maxAge: 3600
}
```

### Cookie Attributes Explained

**httpOnly: true**
- Prevents client-side JavaScript from accessing the cookie
- Protects against XSS attacks
- MUST be true for access and refresh tokens

**secure: true**
- Cookie only sent over HTTPS
- MUST be true in production
- Can be false for localhost development

**sameSite: 'strict'**
- Cookie not sent on cross-site requests
- Protects against CSRF attacks
- Alternative: 'lax' for better compatibility (less strict)

**path: '/'**
- Cookie available for all routes
- Can restrict to specific paths (e.g., '/api' for API-only cookies)

**maxAge**
- Time until cookie expires (in seconds)
- Should match token expiration time

## Token Storage Strategies

### Strategy 1: Separate Cookies (Recommended)

Store each token in its own cookie with appropriate settings:

```javascript
// Access token - short path restriction
res.cookie('accessToken', accessToken, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  path: '/api',           // Only sent to API routes
  maxAge: expiresIn
});

// Refresh token - restricted path
res.cookie('refreshToken', refreshToken, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  path: '/auth/refresh',  // Only sent to refresh endpoint
  maxAge: 30 * 24 * 60 * 60  // 30 days
});

// User info - not httpOnly (frontend can read)
res.cookie('user', JSON.stringify(user), {
  secure: true,
  sameSite: 'strict',
  path: '/',
  maxAge: expiresIn
});
```

**Benefits:**
- Reduced attack surface (path restrictions)
- Granular control over token exposure
- Easy to invalidate individual tokens

### Strategy 2: Session Storage

Store tokens server-side with session ID in cookie:

```javascript
// Store tokens in session (Redis, database, etc.)
session.tokens = {
  accessToken,
  refreshToken,
  idToken,
  expiresAt
};

// Only send session ID to client
res.cookie('sessionId', session.id, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict'
});
```

**Benefits:**
- Tokens never leave server
- Easier to revoke sessions
- Centralized session management

**Tradeoffs:**
- Requires session storage infrastructure
- Additional database/Redis calls
- More complex to scale

## Token Validation Pattern

### On Every Protected Request

```javascript
async function validateRequest(req) {
  const accessToken = req.cookies.accessToken;

  if (!accessToken) {
    throw new UnauthorizedError('No access token');
  }

  try {
    // Validate token
    const claims = await scalekit.validateToken(accessToken, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
      audience: process.env.SCALEKIT_CLIENT_ID
    });
    return claims;
  } catch (error) {
    // Token invalid or expired
    throw new UnauthorizedError('Invalid or expired token');
  }
}
```

### With Automatic Refresh

```javascript
async function validateWithRefresh(req, res) {
  const accessToken = req.cookies.accessToken;

  if (!accessToken) {
    throw new UnauthorizedError('No access token');
  }

  try {
    const claims = await scalekit.validateToken(accessToken, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
      audience: process.env.SCALEKIT_CLIENT_ID
    });
    return claims;
  } catch (validationError) {
    // Try to refresh
    const refreshToken = req.cookies.refreshToken;

    if (!refreshToken) {
      throw new UnauthorizedError('Session expired');
    }

    try {
      const result = await scalekit.refreshAccessToken(refreshToken);

      // Update cookies
      res.cookie('accessToken', result.accessToken, {
        httpOnly: true,
        secure: true,
        sameSite: 'strict',
        maxAge: result.expiresIn
      });

      if (result.refreshToken) {
        res.cookie('refreshToken', result.refreshToken, {
          httpOnly: true,
          secure: true,
          sameSite: 'strict',
          maxAge: 30 * 24 * 60 * 60
        });
      }

      // Validate new token
      const claims = await scalekit.validateToken(result.accessToken, {
        issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
        audience: process.env.SCALEKIT_CLIENT_ID
      });
      return claims;
    } catch (refreshError) {
      // Refresh failed, require re-authentication
      clearAuthCookies(res);
      throw new UnauthorizedError('Session expired');
    }
  }
}
```

## Token Refresh Strategies

### Strategy 1: On-Demand Refresh (Recommended)

Refresh tokens only when access token expires:

```javascript
async function authMiddleware(req, res, next) {
  try {
    // Validate access token
    req.user = await scalekit.validateToken(req.cookies.accessToken, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
      audience: process.env.SCALEKIT_CLIENT_ID
    });
    next();
  } catch (error) {
    // Token expired, attempt refresh
    await refreshAndContinue(req, res, next);
  }
}
```

**Benefits:**
- Minimal refresh token usage
- Better performance (fewer refresh calls)
- Reduced load on Scalekit servers

### Strategy 2: Proactive Refresh

Refresh tokens before they expire (e.g., when 80% of lifetime has passed):

```javascript
async function authMiddleware(req, res, next) {
  const claims = await scalekit.validateToken(req.cookies.accessToken, {
    issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
    audience: process.env.SCALEKIT_CLIENT_ID
  });

  // Check if token expires soon (within 20% of lifetime)
  const now = Math.floor(Date.now() / 1000);
  const expiresIn = claims.exp - now;
  const tokenLifetime = claims.exp - claims.iat;

  if (expiresIn < tokenLifetime * 0.2) {
    // Refresh proactively
    await refreshTokens(req, res);
  }

  req.user = claims;
  next();
}
```

**Benefits:**
- Reduces "token expired" errors for users
- Smoother user experience
- Can implement in background

**Tradeoffs:**
- More refresh API calls
- Slightly more complex logic

### Strategy 3: Scheduled Refresh

Use client-side timer to refresh periodically:

```javascript
// Client-side code
setInterval(async () => {
  try {
    await fetch('/auth/refresh', {
      method: 'POST',
      credentials: 'include'
    });
  } catch (error) {
    // Refresh failed, redirect to login
    window.location.href = '/auth/login';
  }
}, 10 * 60 * 1000); // Every 10 minutes
```

**Benefits:**
- Explicit refresh control
- Can show UI feedback
- Works well for SPAs

**Tradeoffs:**
- Requires client-side JavaScript
- Less efficient (refresh even when inactive)
- Doesn't work for API-only applications

## Session Expiration

### Absolute Timeout

Session expires after a fixed duration regardless of activity:

```javascript
const SESSION_LIFETIME = 8 * 60 * 60; // 8 hours

res.cookie('accessToken', accessToken, {
  maxAge: Math.min(expiresIn, SESSION_LIFETIME)
});
```

### Sliding Expiration

Session extends with each request:

```javascript
async function authMiddleware(req, res, next) {
  const claims = await scalekit.validateToken(req.cookies.accessToken, {
    issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
    audience: process.env.SCALEKIT_CLIENT_ID
  });

  // Extend session
  res.cookie('accessToken', req.cookies.accessToken, {
    maxAge: expiresIn  // Reset expiration
  });

  req.user = claims;
  next();
}
```

### Hybrid Approach (Recommended)

Sliding expiration with absolute maximum:

```javascript
const SESSION_CREATED_AT = 'sessionCreatedAt';
const MAX_SESSION_LIFETIME = 24 * 60 * 60; // 24 hours

async function authMiddleware(req, res, next) {
  const sessionStart = req.cookies[SESSION_CREATED_AT];
  const now = Date.now();

  // Check absolute timeout
  if (sessionStart && (now - sessionStart) > MAX_SESSION_LIFETIME * 1000) {
    clearAuthCookies(res);
    return res.redirect('/auth/login');
  }

  // Continue with sliding expiration
  const claims = await validateWithRefresh(req, res);

  // Set session start time if not exists
  if (!sessionStart) {
    res.cookie(SESSION_CREATED_AT, now);
  }

  req.user = claims;
  next();
}
```

## Logout Implementation

### Complete Logout

Clear all session data and redirect to Scalekit logout:

```javascript
app.get('/auth/logout', (req, res) => {
  const idToken = req.cookies.idToken;

  // Clear all auth cookies
  res.clearCookie('accessToken');
  res.clearCookie('refreshToken');
  res.clearCookie('idToken');
  res.clearCookie('user');
  res.clearCookie('sessionCreatedAt');

  // Redirect to Scalekit logout (invalidates SSO session)
  const logoutUrl = scalekit.getLogoutUrl(idToken, POST_LOGOUT_URL);
  res.redirect(logoutUrl);
});
```

### Logout from All Devices

Require backend session tracking:

```javascript
// On login, store session
await db.sessions.create({
  userId: user.sub,
  sessionId: generateSessionId(),
  refreshToken: refreshToken,
  createdAt: new Date()
});

// Logout from all devices
app.post('/auth/logout-all', authMiddleware, async (req, res) => {
  // Invalidate all user sessions
  await db.sessions.deleteMany({ userId: req.user.sub });

  // Clear current session
  clearAuthCookies(res);

  res.json({ success: true });
});
```

## Security Considerations

### 1. Never Log Tokens

```javascript
// ❌ NEVER DO THIS
console.log('Access token:', accessToken);
logger.info({ accessToken, refreshToken });

// ✅ DO THIS
console.log('User authenticated:', user.email);
logger.info({ userId: user.sub, email: user.email });
```

### 2. Validate Tokens Server-Side

```javascript
// ❌ NEVER trust client-provided claims
const userId = req.cookies.userId;  // Can be tampered

// ✅ Always validate token server-side
const claims = await scalekit.validateToken(req.cookies.accessToken, {
  issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
  audience: process.env.SCALEKIT_CLIENT_ID
});
const userId = claims.sub;  // Cryptographically verified
```

### 3. Use HTTPS in Production

```javascript
// Environment-based configuration
const cookieConfig = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict'
};
```

### 4. Implement Rate Limiting

```javascript
import rateLimit from 'express-rate-limit';

const refreshLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 10,  // 10 requests per window
  message: 'Too many refresh attempts'
});

app.post('/auth/refresh', refreshLimiter, refreshHandler);
```

### 5. Monitor for Anomalies

```javascript
async function authMiddleware(req, res, next) {
  const claims = await scalekit.validateToken(req.cookies.accessToken, {
    issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
    audience: process.env.SCALEKIT_CLIENT_ID
  });

  // Log authentication events
  await logger.logAuthEvent({
    userId: claims.sub,
    ip: req.ip,
    userAgent: req.get('user-agent'),
    timestamp: new Date()
  });

  // Check for suspicious activity
  const recentAttempts = await getRecentAuthAttempts(claims.sub);
  if (recentAttempts.length > 100) {
    await alertSecurityTeam(claims.sub);
  }

  req.user = claims;
  next();
}
```

## Troubleshooting

### Cookies Not Being Set

**Symptoms:** User logs in but session doesn't persist

**Solutions:**
1. Check `secure` flag matches protocol (false for HTTP, true for HTTPS)
2. Verify `sameSite` setting allows your use case
3. Check browser console for cookie warnings
4. Ensure domain matches (cookies don't work across subdomains by default)

### Token Refresh Fails

**Symptoms:** Users logged out frequently

**Solutions:**
1. Verify refresh token is being stored correctly
2. Check refresh token hasn't expired
3. Ensure refresh endpoint has access to refresh token cookie
4. Validate callback URL matches registered URL exactly

### CORS Issues

**Symptoms:** Cookies not sent with cross-origin requests

**Solutions:**
1. Set `credentials: 'include'` in fetch requests
2. Configure CORS to allow credentials: `credentials: true`
3. Set specific origin, not wildcard: `origin: 'https://app.example.com'`
4. Ensure `sameSite: 'none'` for cross-site cookies (requires `secure: true`)

## Next Steps

- Review [security-best-practices.md](security-best-practices.md)
- Configure token lifetimes in Scalekit Dashboard
- Implement session monitoring
- Set up alerts for suspicious activity
