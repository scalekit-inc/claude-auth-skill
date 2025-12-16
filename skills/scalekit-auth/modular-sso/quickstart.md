# Modular SSO Quickstart

## Overview

Modular SSO allows you to add Enterprise SSO (SAML/OIDC) to your existing application **without migrating your authentication system**. Your users, sessions, and authentication logic stay exactly as they are - Scalekit just handles the complex SSO protocols.

**Use this when:**
- You already have working authentication (passwords, sessions, etc.)
- Enterprise customers require SSO via SAML or OIDC
- You want to keep your existing user database and auth logic
- You need to add SSO without a complete auth system rewrite

**Time to implement:** 1-2 hours

## How It Works

```
Enterprise User                Your App              Scalekit              IdP (Okta/Azure AD)
     |                            |                      |                         |
     |---(1) Visit app.com------->|                      |                         |
     |                            |                      |                         |
     |<--(2) Redirect to---------|                      |                         |
     |     Scalekit SSO          |                      |                         |
     |                            |                      |                         |
     |---(3) SSO Login Request------------------->|                         |
     |                            |                      |                         |
     |                            |                      |---(4) SAML/OIDC------->|
     |                            |                      |     Authentication      |
     |                            |                      |                         |
     |                            |                      |<---(5) User Info-------|
     |                            |                      |                         |
     |<--(6) Redirect with code------------------|                         |
     |                            |                      |                         |
     |---(7) Send code----------->|                      |                         |
     |                            |                      |                         |
     |                            |---(8) Exchange code------------->|
     |                            |                      |                         |
     |                            |<---(9) User profile-------------|
     |                            |                      |                         |
     |                            | (10) Create/update  |                         |
     |                            |      user in your DB|                         |
     |                            |                      |                         |
     |<--(11) Set YOUR session---|                      |                         |
     |      cookies/tokens        |                      |                         |
```

**Key Point:** Scalekit handles steps 3-9 (SSO complexity). You handle steps 1-2, 10-11 (your existing auth).

## Step-by-Step Implementation

### Step 1: Disable Full-Stack Auth

In your Scalekit Dashboard:

1. Go to **Dashboard → Authentication → General**
2. **Disable** "Full-Stack Authentication"
3. This ensures Scalekit only handles SSO, not all authentication

### Step 2: Install SDK

**Node.js:**
```bash
npm install @scalekit-sdk/node
```

**Python:**
```bash
pip install scalekit-sdk-python
```

### Step 3: Initialize Scalekit Client

**Node.js:**
```javascript
import { Scalekit } from '@scalekit-sdk/node';

const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

const CALLBACK_URL = process.env.SCALEKIT_SSO_CALLBACK_URL; // e.g., /auth/sso/callback
```

**Python:**
```python
from scalekit import ScalekitClient

scalekit = ScalekitClient(
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET")
)

CALLBACK_URL = os.getenv("SCALEKIT_SSO_CALLBACK_URL")
```

### Step 4: Generate SSO Authorization URL

You need to identify which SSO connection to use. Three options (in order of precedence):

**Option A: Connection ID (Direct)**
```javascript
// If you know the specific SSO connection
const authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
  connectionId: 'conn_1234567890'
});
```

**Option B: Organization ID**
```javascript
// Route by organization
const authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
  organizationId: 'org_1234567890'
});
```

**Option C: Domain Hint (Email-based)**
```javascript
// Extract domain from email and route automatically
const userEmail = 'john@megacorp.com';
const authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
  loginHint: userEmail  // or use domainHint: 'megacorp.com'
});
```

### Step 5: Implement SSO Login Endpoint

**Node.js:**
```javascript
app.get('/auth/sso/login', async (req, res) => {
  // Get organization or email from query/session
  const { org_id, email } = req.query;

  try {
    let authUrl;

    if (org_id) {
      // Route by organization
      authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
        organizationId: org_id
      });
    } else if (email) {
      // Route by email domain
      authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
        loginHint: email
      });
    } else {
      return res.status(400).send('Organization or email required');
    }

    res.redirect(authUrl);
  } catch (error) {
    console.error('SSO login error:', error);
    res.status(500).send('SSO login failed');
  }
});
```

**Python:**
```python
@app.get("/auth/sso/login")
async def sso_login(org_id: str = None, email: str = None):
    if not org_id and not email:
        raise HTTPException(status_code=400, detail="Organization or email required")

    try:
        if org_id:
            auth_url = scalekit.get_authorization_url(
                redirect_uri=CALLBACK_URL,
                options={"organization_id": org_id}
            )
        else:
            auth_url = scalekit.get_authorization_url(
                redirect_uri=CALLBACK_URL,
                options={"login_hint": email}
            )

        return RedirectResponse(url=auth_url)
    except Exception as error:
        raise HTTPException(status_code=500, detail="SSO login failed")
```

### Step 6: Handle IdP-Initiated Login (Optional but Recommended)

When users start from their IdP portal (e.g., Okta dashboard), Scalekit provides a special token.

**Node.js:**
```javascript
app.get('/auth/sso/callback', async (req, res) => {
  const { idp_initiated_login } = req.query;

  // Handle IdP-initiated login
  if (idp_initiated_login) {
    try {
      const claims = await scalekit.getIdpInitiatedLoginClaims(idp_initiated_login);

      // Generate new SP-initiated URL
      const authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
        connectionId: claims.connection_id,
        organizationId: claims.organization_id
      });

      return res.redirect(authUrl);
    } catch (error) {
      console.error('IdP-initiated login error:', error);
      return res.status(500).send('Login failed');
    }
  }

  // Continue with normal callback handling...
});
```

**Python:**
```python
@app.get("/auth/sso/callback")
async def sso_callback(idp_initiated_login: str = None, code: str = None):
    # Handle IdP-initiated login
    if idp_initiated_login:
        try:
            claims = scalekit.get_idp_initiated_login_claims(idp_initiated_login)

            auth_url = scalekit.get_authorization_url(
                redirect_uri=CALLBACK_URL,
                options={
                    "connection_id": claims.connection_id,
                    "organization_id": claims.organization_id
                }
            )

            return RedirectResponse(url=auth_url)
        except Exception as error:
            raise HTTPException(status_code=500, detail="Login failed")

    # Continue with normal callback handling...
```

### Step 7: Handle SSO Callback

Exchange the authorization code for user information and create/update user in YOUR database.

**Node.js:**
```javascript
app.get('/auth/sso/callback', async (req, res) => {
  const { code, error, error_description } = req.query;

  // Handle errors
  if (error) {
    console.error('SSO error:', error, error_description);
    return res.redirect('/login?error=sso_failed');
  }

  if (!code) {
    return res.status(400).send('Authorization code missing');
  }

  try {
    // Exchange code for user profile
    const result = await scalekit.authenticateWithCode(code, CALLBACK_URL);

    const { user } = result;
    // user contains: email, given_name, family_name, username, etc.

    // Find or create user in YOUR database
    let appUser = await db.users.findOne({ email: user.email });

    if (!appUser) {
      // Create new user
      appUser = await db.users.create({
        email: user.email,
        name: `${user.given_name} ${user.family_name}`,
        sso_enabled: true,
        organization_id: result.organization_id, // from Scalekit
        created_at: new Date()
      });
    } else {
      // Update existing user
      await db.users.update(appUser.id, {
        last_login: new Date(),
        sso_enabled: true
      });
    }

    // Create YOUR application session (not Scalekit's)
    req.session.userId = appUser.id;
    req.session.email = appUser.email;
    req.session.save();

    // Redirect to your app
    res.redirect('/dashboard');
  } catch (error) {
    console.error('SSO callback error:', error);
    res.redirect('/login?error=authentication_failed');
  }
});
```

**Python:**
```python
@app.get("/auth/sso/callback")
async def sso_callback(request: Request, code: str = None, error: str = None):
    if error:
        return RedirectResponse(url="/login?error=sso_failed")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    try:
        # Exchange code for user profile
        result = scalekit.authenticate_with_code(
            code=code,
            redirect_uri=CALLBACK_URL
        )

        user = result.user

        # Find or create user in YOUR database
        app_user = await db.users.find_one({"email": user.email})

        if not app_user:
            # Create new user
            app_user = await db.users.create({
                "email": user.email,
                "name": f"{user.given_name} {user.family_name}",
                "sso_enabled": True,
                "organization_id": result.organization_id,
                "created_at": datetime.now()
            })
        else:
            # Update existing user
            await db.users.update(
                app_user.id,
                {"last_login": datetime.now(), "sso_enabled": True}
            )

        # Create YOUR application session
        request.session["user_id"] = app_user.id
        request.session["email"] = app_user.email

        return RedirectResponse(url="/dashboard")

    except Exception as error:
        return RedirectResponse(url="/login?error=authentication_failed")
```

### Step 8: Pre-check SSO Availability (Optional)

Before redirecting users to SSO, check if their domain has SSO configured:

**Node.js:**
```javascript
app.post('/check-sso', async (req, res) => {
  const { email } = req.body;
  const domain = email.split('@')[1];

  try {
    const connections = await scalekit.connections.listConnectionsByDomain({
      domain: domain
    });

    if (connections.length > 0) {
      // SSO available for this domain
      res.json({
        sso_available: true,
        connection_id: connections[0].id
      });
    } else {
      // No SSO, use regular password login
      res.json({
        sso_available: false
      });
    }
  } catch (error) {
    console.error('SSO check error:', error);
    res.status(500).json({ error: 'Failed to check SSO' });
  }
});
```

**Python:**
```python
@app.post("/check-sso")
async def check_sso(email: str):
    domain = email.split('@')[1]

    try:
        connections = scalekit.connections.list_connections_by_domain(
            domain=domain
        )

        if len(connections) > 0:
            return {
                "sso_available": True,
                "connection_id": connections[0].id
            }
        else:
            return {"sso_available": False}

    except Exception as error:
        raise HTTPException(status_code=500, detail="Failed to check SSO")
```

## Integration with Existing Auth Providers

### Auth0 Integration

See [templates/auth0-integration.md](templates/auth0-integration.md) for complete guide.

### Firebase Integration

See [templates/firebase-integration.md](templates/firebase-integration.md) for complete guide.

### AWS Cognito Integration

See [templates/cognito-integration.md](templates/cognito-integration.md) for complete guide.

## Enterprise Customer Onboarding

### Admin Portal for Self-Service

Generate shareable links for customers to configure their own SSO:

**Node.js:**
```javascript
app.get('/admin/sso/setup-link', async (req, res) => {
  const { organization_id } = req.query;

  try {
    const portalLink = await scalekit.organizations.generatePortalLink(
      organization_id
    );

    res.json({ portal_url: portalLink });
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate portal link' });
  }
});
```

**Python:**
```python
@app.get("/admin/sso/setup-link")
async def generate_setup_link(organization_id: str):
    try:
        portal_link = scalekit.organizations.generate_portal_link(
            organization_id
        )
        return {"portal_url": portal_link}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate portal link")
```

### Embed Admin Portal in Your App

```html
<iframe
  src="https://your-env.scalekit.com/organizations/{org_id}/portal"
  width="100%"
  height="600"
  frameborder="0"
></iframe>
```

### Domain Verification

Enable automatic routing by verifying customer domains:

1. Customer adds TXT record to their DNS
2. Scalekit verifies domain ownership
3. Users with that domain automatically route to correct SSO

## Testing

### Using Test Organization

Scalekit provides a pre-configured test organization:

- **Domains:** `@example.com`, `@example.org`
- **IdP:** IdP Simulator (built-in)
- **Access:** Available in all environments

**Test flow:**
```
1. Use email: test@example.com
2. Redirect to SSO: /auth/sso/login?email=test@example.com
3. Complete sign-in at IdP Simulator
4. Verify callback receives user info
5. Verify user created in your database
```

## Login Flow Variations

### Unified Login Page

```javascript
// Single login page that detects SSO
app.post('/login', async (req, res) => {
  const { email, password } = req.body;

  // Check if SSO is available
  const domain = email.split('@')[1];
  const connections = await scalekit.connections.listConnectionsByDomain({ domain });

  if (connections.length > 0) {
    // Redirect to SSO
    const authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
      loginHint: email
    });
    return res.redirect(authUrl);
  }

  // Fall back to password authentication
  const user = await authenticateWithPassword(email, password);
  // ... your existing password login
});
```

### Separate SSO Button

```html
<!-- Regular login form -->
<form action="/login/password" method="POST">
  <input type="email" name="email" placeholder="Email" />
  <input type="password" name="password" placeholder="Password" />
  <button type="submit">Log In</button>
</form>

<!-- SSO option -->
<a href="/login/sso" class="sso-button">
  Log in with SSO
</a>
```

## Common Patterns

### Pattern 1: Email-Based Routing

```javascript
// User enters email
// Check domain → redirect to SSO or show password field
app.post('/check-login-method', async (req, res) => {
  const { email } = req.body;
  const domain = email.split('@')[1];

  const connections = await scalekit.connections.listConnectionsByDomain({ domain });

  if (connections.length > 0) {
    res.json({ method: 'sso', redirect_url: `/auth/sso/login?email=${email}` });
  } else {
    res.json({ method: 'password' });
  }
});
```

### Pattern 2: Organization Selection

```javascript
// Show organization picker
app.get('/login', (req, res) => {
  const organizations = [
    { id: 'org_123', name: 'MegaCorp', sso_enabled: true },
    { id: 'org_456', name: 'StartupCo', sso_enabled: false }
  ];

  res.render('login', { organizations });
});

// Redirect based on selection
app.post('/login/select-org', (req, res) => {
  const { org_id } = req.body;

  const authUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
    organizationId: org_id
  });

  res.redirect(authUrl);
});
```

## Troubleshooting

### SSO Not Working for Domain

**Check:**
1. Domain is verified in Scalekit Dashboard
2. SSO connection is active
3. IdP configuration is correct (ACS URL, Entity ID)

### Users Can't Be Found After SSO

**Check:**
1. Email mapping is correct (IdP sends email in expected format)
2. Your database lookup is case-insensitive
3. Check for email verification requirements

### IdP-Initiated Login Fails

**Check:**
1. IdP has correct ACS URL configured
2. Your callback handles `idp_initiated_login` parameter
3. Connection ID extraction is correct

## Security Considerations

### Session Management

After SSO, create YOUR session - don't rely on Scalekit tokens:

```javascript
// ✅ Create your own session
req.session.userId = user.id;
req.session.regenerate(); // Prevent session fixation

// ❌ Don't use Scalekit tokens for your app sessions
// Scalekit tokens are for the SSO flow only
```

### User Verification

Always verify the user email from SSO matches expected domain:

```javascript
const { user } = await scalekit.authenticateWithCode(code, callbackUrl);

// Verify domain matches expected organization
const expectedDomain = organization.domain;
const userDomain = user.email.split('@')[1];

if (userDomain !== expectedDomain) {
  throw new Error('Domain mismatch');
}
```

## Production Checklist

- [ ] Full-Stack Auth disabled in Scalekit Dashboard
- [ ] SSO callback URL registered in Dashboard
- [ ] Domain verification completed for production domains
- [ ] IdP configuration tested (SAML metadata or OIDC settings)
- [ ] User creation/update logic tested
- [ ] Session management tested
- [ ] IdP-initiated login tested
- [ ] Error handling implemented
- [ ] Logging configured for SSO events
- [ ] Customer admin portal tested

## Next Steps

- Review [templates/](templates/) for framework-specific implementations
- See [Integration with Auth0/Firebase/Cognito](templates/) for existing auth integration
- Read [../reference/sso-best-practices.md](../reference/sso-best-practices.md) for enterprise SSO patterns

## Complete Examples

For fully working examples, see:
- [Node.js + Express template](templates/nodejs-express-sso.md)
- [Next.js SSO integration](templates/nextjs-sso.md)
- [Python + FastAPI SSO](templates/python-fastapi-sso.md)
