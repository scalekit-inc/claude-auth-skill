# Node.js + Express Modular SSO Template

Complete implementation for adding Enterprise SSO to your existing Express application.

## Quick Setup

```bash
# Install Scalekit SDK (only addition needed)
npm install @scalekit-sdk/node

# Your existing dependencies remain unchanged
# express, your session middleware, database, etc.
```

## Project Structure

```
your-existing-app/
├── lib/
│   ├── scalekit.js          # NEW: Scalekit client
│   ├── db.js                # Your existing database
│   └── auth.js              # Your existing auth logic
├── routes/
│   ├── auth.js              # Your existing auth routes
│   └── sso.js               # NEW: SSO routes
└── app.js                   # Your existing Express app
```

## File 1: lib/scalekit.js (NEW)

```javascript
import { Scalekit } from '@scalekit-sdk/node';
import dotenv from 'dotenv';

dotenv.config();

// Initialize Scalekit for SSO only
export const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

export const SSO_CALLBACK_URL = process.env.SCALEKIT_SSO_CALLBACK_URL;
```

## File 2: routes/sso.js (NEW)

```javascript
import express from 'express';
import { scalekit, SSO_CALLBACK_URL } from '../lib/scalekit.js';
import { findOrCreateUser } from '../lib/db.js';

const router = express.Router();

// SSO Login - Initiate SSO flow
router.get('/login', async (req, res) => {
  try {
    const { org_id, email } = req.query;

    if (!org_id && !email) {
      return res.redirect('/login?error=missing_org_or_email');
    }

    // Generate SSO authorization URL
    let authUrl;

    if (org_id) {
      // Route by organization ID
      authUrl = scalekit.getAuthorizationUrl(SSO_CALLBACK_URL, {
        organizationId: org_id
      });
    } else {
      // Route by email domain
      authUrl = scalekit.getAuthorizationUrl(SSO_CALLBACK_URL, {
        loginHint: email
      });
    }

    res.redirect(authUrl);
  } catch (error) {
    console.error('SSO login error:', error);
    res.redirect('/login?error=sso_failed');
  }
});

// SSO Callback - Handle SSO response
router.get('/callback', async (req, res) => {
  try {
    const { code, error, error_description, idp_initiated_login } = req.query;

    // Handle IdP-initiated login
    if (idp_initiated_login) {
      const claims = await scalekit.getIdpInitiatedLoginClaims(idp_initiated_login);

      const authUrl = scalekit.getAuthorizationUrl(SSO_CALLBACK_URL, {
        connectionId: claims.connection_id,
        organizationId: claims.organization_id
      });

      return res.redirect(authUrl);
    }

    // Handle OAuth errors
    if (error) {
      console.error('SSO callback error:', error, error_description);
      return res.redirect('/login?error=' + encodeURIComponent(error_description || error));
    }

    if (!code) {
      return res.redirect('/login?error=missing_code');
    }

    // Exchange code for user profile
    const result = await scalekit.authenticateWithCode(code, SSO_CALLBACK_URL);
    const { user } = result;

    console.log('SSO user authenticated:', {
      email: user.email,
      org_id: result.organization_id
    });

    // Find or create user in YOUR database
    const appUser = await findOrCreateUser({
      email: user.email,
      name: user.name || `${user.given_name} ${user.family_name}`,
      sso_enabled: true,
      organization_id: result.organization_id,
      sso_connection_id: result.connection_id
    });

    // Create YOUR session (not Scalekit's)
    req.session.regenerate((err) => {
      if (err) {
        console.error('Session regeneration error:', err);
        return res.redirect('/login?error=session_failed');
      }

      req.session.userId = appUser.id;
      req.session.email = appUser.email;
      req.session.authMethod = 'sso';
      req.session.save();

      console.log('User session created:', {
        userId: appUser.id,
        email: appUser.email
      });

      // Redirect to your app
      res.redirect('/dashboard');
    });
  } catch (error) {
    console.error('SSO callback error:', error);
    res.redirect('/login?error=authentication_failed');
  }
});

// Check if SSO is available for email domain
router.post('/check', async (req, res) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email required' });
    }

    const domain = email.split('@')[1];

    // Check if domain has SSO configured
    const connections = await scalekit.connections.listConnectionsByDomain({
      domain: domain
    });

    if (connections.length > 0) {
      res.json({
        sso_available: true,
        connection_id: connections[0].id,
        organization_id: connections[0].organization_id
      });
    } else {
      res.json({
        sso_available: false
      });
    }
  } catch (error) {
    console.error('SSO check error:', error);
    res.status(500).json({ error: 'Failed to check SSO availability' });
  }
});

export default router;
```

## File 3: lib/db.js (UPDATE - Add SSO fields)

```javascript
// Your existing database module - just add SSO fields

export async function findOrCreateUser(userData) {
  const { email, name, sso_enabled, organization_id, sso_connection_id } = userData;

  // Find existing user
  let user = await db.users.findOne({ email: email.toLowerCase() });

  if (user) {
    // Update existing user with SSO info
    await db.users.update(user.id, {
      last_login: new Date(),
      sso_enabled: sso_enabled,
      organization_id: organization_id,
      sso_connection_id: sso_connection_id,
      updated_at: new Date()
    });

    return await db.users.findById(user.id);
  }

  // Create new user
  user = await db.users.create({
    email: email.toLowerCase(),
    name: name,
    sso_enabled: sso_enabled || false,
    organization_id: organization_id,
    sso_connection_id: sso_connection_id,
    created_at: new Date(),
    last_login: new Date()
  });

  return user;
}
```

## File 4: app.js (UPDATE - Add SSO routes)

```javascript
import express from 'express';
import session from 'express-session';
import dotenv from 'dotenv';

// Your existing routes
import authRoutes from './routes/auth.js';

// NEW: SSO routes
import ssoRoutes from './routes/sso.js';

dotenv.config();

const app = express();

// Your existing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Your existing session middleware
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Your existing routes
app.use('/auth', authRoutes);

// NEW: SSO routes
app.use('/auth/sso', ssoRoutes);

// Your existing application code...

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});
```

## File 5: .env (UPDATE - Add Scalekit config)

```bash
# Your existing environment variables
DATABASE_URL=...
SESSION_SECRET=...

# NEW: Scalekit SSO configuration
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_...
SCALEKIT_CLIENT_SECRET=test_...
SCALEKIT_SSO_CALLBACK_URL=http://localhost:3000/auth/sso/callback
```

## Enhanced Login Page with SSO Detection

```javascript
// routes/auth.js - UPDATE your existing login page

router.get('/login', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Login</title>
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
            margin: 8px 0;
          }
          button:hover {
            background: #0051cc;
          }
          .divider {
            text-align: center;
            margin: 20px 0;
            color: #666;
          }
          #password-container {
            display: none;
          }
          .sso-info {
            background: #e3f2fd;
            padding: 12px;
            border-radius: 4px;
            margin: 12px 0;
            display: none;
          }
        </style>
      </head>
      <body>
        <h1>Sign In</h1>

        <form id="login-form">
          <input
            type="email"
            id="email"
            name="email"
            placeholder="Email"
            required
          />

          <div id="sso-container" style="display: none;">
            <div class="sso-info">
              ✓ SSO is available for your organization
            </div>
            <button type="button" id="sso-button">
              Continue with SSO
            </button>
            <div class="divider">or</div>
          </div>

          <div id="password-container">
            <input
              type="password"
              id="password"
              name="password"
              placeholder="Password"
            />
            <button type="submit">Sign In with Password</button>
          </div>
        </form>

        <script>
          const emailInput = document.getElementById('email');
          const ssoContainer = document.getElementById('sso-container');
          const passwordContainer = document.getElementById('password-container');
          const ssoButton = document.getElementById('sso-button');
          let ssoAvailable = false;

          // Check for SSO when email changes
          emailInput.addEventListener('blur', async () => {
            const email = emailInput.value.trim();
            if (!email || !email.includes('@')) return;

            try {
              const response = await fetch('/auth/sso/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
              });

              const data = await response.json();

              if (data.sso_available) {
                ssoAvailable = true;
                ssoContainer.style.display = 'block';
                passwordContainer.style.display = 'block';
              } else {
                ssoAvailable = false;
                ssoContainer.style.display = 'none';
                passwordContainer.style.display = 'block';
              }
            } catch (error) {
              console.error('SSO check failed:', error);
              passwordContainer.style.display = 'block';
            }
          });

          // Handle SSO button click
          ssoButton.addEventListener('click', () => {
            const email = emailInput.value.trim();
            window.location.href = '/auth/sso/login?email=' + encodeURIComponent(email);
          });

          // Handle password form submission
          document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = emailInput.value.trim();
            const password = document.getElementById('password').value;

            // Your existing password authentication
            const response = await fetch('/auth/login/password', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email, password })
            });

            if (response.ok) {
              window.location.href = '/dashboard';
            } else {
              alert('Login failed');
            }
          });
        </script>
      </body>
    </html>
  `);
});
```

## Admin Portal for Customer SSO Setup

```javascript
// routes/admin.js - NEW

import express from 'express';
import { scalekit } from '../lib/scalekit.js';
import { requireAdmin } from '../middleware/auth.js';

const router = express.Router();

// Generate SSO setup portal link for customer
router.post('/organizations/:org_id/sso-portal', requireAdmin, async (req, res) => {
  try {
    const { org_id } = req.params;

    const portalLink = await scalekit.organization.generatePortalLink(org_id);

    res.json({
      portal_url: portalLink,
      expires_in: 3600 // 1 hour
    });
  } catch (error) {
    console.error('Portal generation error:', error);
    res.status(500).json({ error: 'Failed to generate portal link' });
  }
});

// Embed portal in iframe
router.get('/organizations/:org_id/sso-setup', requireAdmin, (req, res) => {
  const { org_id } = req.params;

  res.send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>SSO Setup</title>
        <style>
          body { margin: 0; padding: 20px; }
          iframe { width: 100%; height: calc(100vh - 100px); border: none; }
        </style>
      </head>
      <body>
        <h1>Configure SSO for Your Organization</h1>
        <iframe
          id="sso-portal"
          src="loading..."
        ></iframe>
        <script>
          fetch('/admin/organizations/${org_id}/sso-portal', {
            method: 'POST',
            credentials: 'include'
          })
          .then(r => r.json())
          .then(data => {
            document.getElementById('sso-portal').src = data.portal_url;
          });
        </script>
      </body>
    </html>
  `);
});

export default router;
```

## Database Migration (Example)

```sql
-- Add SSO fields to your existing users table

ALTER TABLE users
ADD COLUMN sso_enabled BOOLEAN DEFAULT false,
ADD COLUMN organization_id VARCHAR(255),
ADD COLUMN sso_connection_id VARCHAR(255),
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create index for faster lookups
CREATE INDEX idx_users_organization ON users(organization_id);
CREATE INDEX idx_users_sso_connection ON users(sso_connection_id);
```

## Testing

### 1. Test SSO Detection

```bash
curl -X POST http://localhost:3000/auth/sso/check \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Should return:
# {"sso_available":true,"connection_id":"conn_...","organization_id":"org_..."}
```

### 2. Test SSO Login Flow

1. Visit http://localhost:3000/login
2. Enter email: `test@example.com`
3. Click "Continue with SSO"
4. Complete authentication at IdP Simulator
5. Verify redirect to `/dashboard`
6. Check user created in database

### 3. Test IdP-Initiated Login

Configure IdP with ACS URL:
```
https://your-env.scalekit.com/sso/v1/connections/{connection_id}/acs
```

Start from IdP portal → should redirect to your app

## Usage Patterns

### Pattern 1: Unified Login (Recommended)

Single login page that auto-detects SSO availability.

**Benefits:**
- Seamless user experience
- No separate SSO button needed
- Automatic fallback to password

### Pattern 2: Separate SSO Entry Point

Different paths for password and SSO users.

```javascript
// Regular login
app.get('/login', ...)

// SSO-specific login
app.get('/login/sso', ...)
```

### Pattern 3: Organization-Based Routing

Users select their organization first:

```javascript
app.get('/login/org-select', (req, res) => {
  // Show organization picker
  // Each org has SSO enabled/disabled flag
});
```

## Security Considerations

### Email Verification

```javascript
// Verify email domain matches expected organization
const result = await scalekit.authenticateWithCode(code, callbackUrl);
const userDomain = result.user.email.split('@')[1];

const org = await db.organizations.findById(result.organization_id);

if (!org.domains.includes(userDomain)) {
  throw new Error('Email domain not authorized for this organization');
}
```

### Session Management

```javascript
// Always regenerate session after SSO
req.session.regenerate((err) => {
  if (err) return handleError(err);

  req.session.userId = user.id;
  req.session.authMethod = 'sso';
  req.session.save();
});
```

## Production Checklist

- [ ] Disable Full-Stack Auth in Scalekit Dashboard
- [ ] Register SSO callback URL in Dashboard
- [ ] Add SSO fields to database
- [ ] Update login page with SSO detection
- [ ] Test IdP-initiated login
- [ ] Configure customer admin portal
- [ ] Set up domain verification
- [ ] Add logging for SSO events
- [ ] Test with real IdP (Okta/Azure AD)
- [ ] Document SSO setup for customers

## Troubleshooting

**SSO button doesn't appear:**
- Check `/auth/sso/check` returns `sso_available: true`
- Verify domain is configured in Scalekit Dashboard
- Check browser console for errors

**Callback fails:**
- Verify callback URL matches exactly (including protocol, port)
- Check Scalekit Dashboard → Settings → Redirect URIs
- Ensure code hasn't been used already (single-use)

**User not created:**
- Check database connection
- Verify `findOrCreateUser` function
- Check for unique constraint errors on email

## Next Steps

- Enable domain verification for automatic routing
- Set up SCIM for user provisioning
- Add role mapping from IdP attributes
- Implement JIT (Just-In-Time) provisioning
- Add organization-specific customization
