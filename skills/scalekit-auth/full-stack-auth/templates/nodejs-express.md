# Node.js + Express Template

Complete authentication implementation for Express applications.

## Quick Setup

```bash
# 1. Install dependencies
npm install express @scalekit-sdk/node cookie-parser dotenv

# 2. Create the files below
# 3. Set up .env file
# 4. Run: node app.js
```

## Project Structure

```
your-app/
├── .env
├── app.js
├── lib/
│   └── scalekit.js
├── middleware/
│   └── auth.js
└── package.json
```

## File 1: package.json

```json
{
  "name": "scalekit-auth-express",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "start": "node app.js",
    "dev": "node --watch app.js"
  },
  "dependencies": {
    "@scalekit-sdk/node": "^1.0.0",
    "express": "^4.18.2",
    "cookie-parser": "^1.4.6",
    "dotenv": "^16.3.1"
  }
}
```

## File 2: .env

```bash
# Scalekit credentials (from Dashboard → Settings)
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_12345...
SCALEKIT_CLIENT_SECRET=test_12345...

# Application URLs
APP_URL=http://localhost:3000
CALLBACK_URL=http://localhost:3000/auth/callback
POST_LOGOUT_URL=http://localhost:3000

# Server config
PORT=3000

# Cookie settings
COOKIE_SECURE=false  # Set to true in production with HTTPS
```

## File 3: lib/scalekit.js

```javascript
import { Scalekit } from '@scalekit-sdk/node';
import dotenv from 'dotenv';

dotenv.config();

// Initialize Scalekit client
export const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

// Application URLs
export const CALLBACK_URL = process.env.CALLBACK_URL;
export const POST_LOGOUT_URL = process.env.POST_LOGOUT_URL;

// Cookie configuration
export const cookieConfig = {
  httpOnly: true,
  secure: process.env.COOKIE_SECURE === 'true',
  sameSite: 'strict'
};
```

## File 4: middleware/auth.js

```javascript
import { scalekit } from '../lib/scalekit.js';
import { cookieConfig } from '../lib/scalekit.js';

/**
 * Authentication middleware
 * Validates access token and refreshes if expired
 */
export async function authMiddleware(req, res, next) {
  try {
    const accessToken = req.cookies.accessToken;

    if (!accessToken) {
      return res.status(401).json({
        error: 'Not authenticated',
        loginUrl: '/auth/login'
      });
    }

    // Validate access token
    try {
      const claims = await scalekit.validateAccessToken(accessToken);
      req.user = claims;
      next();
    } catch (validationError) {
      // Token expired or invalid, attempt refresh
      const refreshToken = req.cookies.refreshToken;

      if (!refreshToken) {
        return res.status(401).json({
          error: 'Session expired',
          loginUrl: '/auth/login'
        });
      }

      try {
        // Refresh tokens
        const result = await scalekit.refreshAccessToken(refreshToken);

        // Update cookies
        res.cookie('accessToken', result.accessToken, {
          ...cookieConfig,
          maxAge: result.expiresIn * 1000
        });

        if (result.refreshToken) {
          res.cookie('refreshToken', result.refreshToken, {
            ...cookieConfig,
            maxAge: 30 * 24 * 60 * 60 * 1000 // 30 days
          });
        }

        // Validate new token
        const claims = await scalekit.validateAccessToken(result.accessToken);
        req.user = claims;
        next();
      } catch (refreshError) {
        // Refresh failed, clear cookies and require re-login
        res.clearCookie('accessToken');
        res.clearCookie('refreshToken');
        res.clearCookie('idToken');
        res.clearCookie('user');

        return res.status(401).json({
          error: 'Session expired',
          loginUrl: '/auth/login'
        });
      }
    }
  } catch (error) {
    console.error('Auth middleware error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

/**
 * Optional middleware for routes that redirect to login
 * instead of returning 401
 */
export function requireAuthWithRedirect(req, res, next) {
  const accessToken = req.cookies.accessToken;

  if (!accessToken) {
    return res.redirect('/auth/login');
  }

  authMiddleware(req, res, next);
}
```

## File 5: app.js

```javascript
import express from 'express';
import cookieParser from 'cookie-parser';
import { scalekit, CALLBACK_URL, POST_LOGOUT_URL, cookieConfig } from './lib/scalekit.js';
import { authMiddleware, requireAuthWithRedirect } from './middleware/auth.js';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cookieParser());
app.use(express.static('public')); // For serving static files

// ============================================================================
// Public Routes
// ============================================================================

// Home page
app.get('/', (req, res) => {
  const isAuthenticated = !!req.cookies.accessToken;
  const user = req.cookies.user ? JSON.parse(req.cookies.user) : null;

  res.send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Scalekit Auth Demo</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
          }
          .button {
            background: #0070f3;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
          }
          .button:hover {
            background: #0051cc;
          }
          .user-info {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
          }
        </style>
      </head>
      <body>
        <h1>Scalekit Authentication Demo</h1>
        ${isAuthenticated ? `
          <div class="user-info">
            <h2>Welcome, ${user?.email || 'User'}!</h2>
            <p><strong>User ID:</strong> ${user?.sub || 'N/A'}</p>
            <p><strong>Email:</strong> ${user?.email || 'N/A'}</p>
            <p><strong>Email Verified:</strong> ${user?.email_verified ? 'Yes' : 'No'}</p>
          </div>
          <a href="/dashboard" class="button">Go to Dashboard</a>
          <a href="/auth/logout" class="button">Logout</a>
        ` : `
          <p>You are not logged in.</p>
          <a href="/auth/login" class="button">Sign In</a>
        `}
      </body>
    </html>
  `);
});

// ============================================================================
// Authentication Routes
// ============================================================================

// Initiate login
app.get('/auth/login', (req, res) => {
  try {
    const authorizationUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
      scopes: ['openid', 'profile', 'email', 'offline_access']
    });

    res.redirect(authorizationUrl);
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).send('Failed to initiate login');
  }
});

// Handle OAuth callback
app.get('/auth/callback', async (req, res) => {
  try {
    const { code, error, error_description } = req.query;

    // Handle OAuth errors
    if (error) {
      console.error('OAuth error:', error, error_description);
      return res.redirect('/?error=' + encodeURIComponent(error_description || error));
    }

    if (!code) {
      return res.status(400).send('Authorization code missing');
    }

    // Exchange code for tokens
    const result = await scalekit.authenticateWithCode(code, CALLBACK_URL);

    // Extract tokens and user info
    const { accessToken, refreshToken, idToken, user, expiresIn } = result;

    // Set access token cookie
    res.cookie('accessToken', accessToken, {
      ...cookieConfig,
      maxAge: expiresIn * 1000
    });

    // Set refresh token cookie
    res.cookie('refreshToken', refreshToken, {
      ...cookieConfig,
      maxAge: 30 * 24 * 60 * 60 * 1000 // 30 days
    });

    // Set ID token cookie
    res.cookie('idToken', idToken, {
      ...cookieConfig,
      maxAge: expiresIn * 1000
    });

    // Set user info cookie (not httpOnly so frontend can access)
    res.cookie('user', JSON.stringify(user), {
      maxAge: expiresIn * 1000,
      secure: cookieConfig.secure,
      sameSite: cookieConfig.sameSite
    });

    console.log('User authenticated:', user.email);

    // Redirect to dashboard
    res.redirect('/dashboard');
  } catch (error) {
    console.error('Authentication error:', error);
    res.redirect('/?error=' + encodeURIComponent('Authentication failed'));
  }
});

// Logout
app.get('/auth/logout', (req, res) => {
  try {
    const idToken = req.cookies.idToken;

    // Clear all auth cookies
    res.clearCookie('accessToken');
    res.clearCookie('refreshToken');
    res.clearCookie('idToken');
    res.clearCookie('user');

    // Generate Scalekit logout URL
    const logoutUrl = scalekit.getLogoutUrl(idToken, POST_LOGOUT_URL);

    res.redirect(logoutUrl);
  } catch (error) {
    console.error('Logout error:', error);
    res.redirect('/');
  }
});

// ============================================================================
// Protected Routes (HTML pages)
// ============================================================================

app.get('/dashboard', requireAuthWithRedirect, (req, res) => {
  const user = req.cookies.user ? JSON.parse(req.cookies.user) : {};

  res.send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Dashboard - Scalekit Auth</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
          }
          .button {
            background: #0070f3;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
          }
          .card {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
          }
          pre {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
          }
        </style>
      </head>
      <body>
        <h1>Dashboard</h1>

        <div class="card">
          <h2>User Information</h2>
          <pre>${JSON.stringify(user, null, 2)}</pre>
        </div>

        <div class="card">
          <h2>Token Claims</h2>
          <pre>${JSON.stringify(req.user, null, 2)}</pre>
        </div>

        <a href="/" class="button">Home</a>
        <a href="/auth/logout" class="button">Logout</a>
      </body>
    </html>
  `);
});

// ============================================================================
// Protected API Routes
// ============================================================================

// Get current user
app.get('/api/me', authMiddleware, (req, res) => {
  const user = req.cookies.user ? JSON.parse(req.cookies.user) : {};
  res.json({
    user,
    claims: req.user
  });
});

// Example protected API endpoint
app.get('/api/profile', authMiddleware, (req, res) => {
  res.json({
    message: 'This is a protected endpoint',
    user: req.user
  });
});

// Example API endpoint that requires specific scope
app.get('/api/admin', authMiddleware, (req, res) => {
  // Check for admin scope or role
  const roles = req.user.roles || [];

  if (!roles.includes('admin')) {
    return res.status(403).json({
      error: 'Forbidden',
      message: 'Admin role required'
    });
  }

  res.json({
    message: 'Admin endpoint accessed successfully',
    user: req.user
  });
});

// ============================================================================
// Error Handling
// ============================================================================

app.use((err, req, res, next) => {
  console.error('Application error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// ============================================================================
// Start Server
// ============================================================================

app.listen(PORT, () => {
  console.log(`
🚀 Server running on http://localhost:${PORT}

Routes:
  Home:      http://localhost:${PORT}/
  Login:     http://localhost:${PORT}/auth/login
  Dashboard: http://localhost:${PORT}/dashboard (protected)
  API:       http://localhost:${PORT}/api/me (protected)

Environment:
  Scalekit URL: ${process.env.SCALEKIT_ENVIRONMENT_URL}
  Callback URL: ${CALLBACK_URL}
  `);
});
```

## Usage

### 1. Set up environment

Create `.env` file with your Scalekit credentials.

### 2. Install dependencies

```bash
npm install
```

### 3. Start the server

```bash
npm start

# Or with auto-reload in development:
npm run dev
```

### 4. Test the flow

1. Visit http://localhost:3000
2. Click "Sign In"
3. Complete authentication
4. You'll be redirected to the dashboard
5. Test protected routes
6. Click "Logout"

## API Endpoints

### Public Endpoints

- `GET /` - Home page
- `GET /auth/login` - Initiates login flow
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout

### Protected Endpoints

- `GET /dashboard` - User dashboard (redirects to login if not authenticated)
- `GET /api/me` - Get current user info (returns 401 if not authenticated)
- `GET /api/profile` - Protected API example
- `GET /api/admin` - Role-protected endpoint example

## Customization

### Add CORS for Frontend Apps

```javascript
import cors from 'cors';

app.use(cors({
  origin: 'http://localhost:3001', // Your frontend URL
  credentials: true
}));
```

### Add Request Logging

```javascript
import morgan from 'morgan';

app.use(morgan('combined'));
```

### Add Rate Limiting

```javascript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});

app.use('/api', limiter);
```

### Add Helmet for Security

```javascript
import helmet from 'helmet';

app.use(helmet());
```

## Production Deployment

### Environment Variables

Update `.env` for production:

```bash
SCALEKIT_ENVIRONMENT_URL=https://prod-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_prod_...
SCALEKIT_CLIENT_SECRET=prod_...

APP_URL=https://yourapp.com
CALLBACK_URL=https://yourapp.com/auth/callback
POST_LOGOUT_URL=https://yourapp.com

COOKIE_SECURE=true
NODE_ENV=production
```

### Register Production URLs

In Scalekit Dashboard → Settings → Redirect URIs:
- Add `https://yourapp.com/auth/callback`

### Deploy Checklist

- [ ] Set `COOKIE_SECURE=true`
- [ ] Use HTTPS
- [ ] Set `NODE_ENV=production`
- [ ] Register production callback URLs
- [ ] Add error monitoring (e.g., Sentry)
- [ ] Add logging (e.g., Winston)
- [ ] Configure CORS properly
- [ ] Add rate limiting
- [ ] Enable helmet security headers

## Testing

```bash
# Test environment variables
python ../../../scripts/validate_env.py

# Test Scalekit connection
curl http://localhost:3000/api/me
# Should return 401

# After logging in:
curl http://localhost:3000/api/me --cookie "accessToken=..."
# Should return user data
```

## Next Steps

- Add React/Vue frontend
- Implement role-based access control
- Add user management UI
- Enable social login in Scalekit Dashboard
- Add enterprise SSO for B2B customers
- Customize login UI in Scalekit Dashboard
