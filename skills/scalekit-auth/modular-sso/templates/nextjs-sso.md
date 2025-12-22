# Next.js Modular SSO Template (App Router)

Complete implementation for adding Enterprise SSO to your existing Next.js application.

## Quick Setup

```bash
# Install Scalekit SDK (only addition needed)
npm install @scalekit-sdk/node

# Your existing dependencies remain unchanged
# next, your auth library, database, etc.
```

## Project Structure

```
your-existing-app/
├── .env.local
├── app/
│   ├── auth/
│   │   └── sso/
│   │       ├── login/
│   │       │   └── route.ts      # NEW: SSO login initiation
│   │       └── callback/
│   │           └── route.ts      # NEW: SSO callback handler
│   ├── api/
│   │   └── sso/
│   │       └── check/
│   │           └── route.ts      # NEW: SSO detection endpoint
├── lib/
│   ├── scalekit.ts               # NEW: Scalekit client
│   ├── db.ts                     # Your existing database
│   └── auth.ts                   # Your existing auth logic
└── components/
    └── login-form.tsx            # UPDATE: Add SSO detection
```

## File 1: .env.local (UPDATE)

```bash
# Your existing environment variables
DATABASE_URL=...
AUTH_SECRET=...

# NEW: Scalekit SSO configuration
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_...
SCALEKIT_CLIENT_SECRET=test_...
SCALEKIT_SSO_CALLBACK_URL=http://localhost:3000/auth/sso/callback
```

## File 2: lib/scalekit.ts (NEW)

```typescript
import { Scalekit } from '@scalekit-sdk/node';

if (!process.env.SCALEKIT_ENVIRONMENT_URL) {
  throw new Error('SCALEKIT_ENVIRONMENT_URL is not defined');
}

if (!process.env.SCALEKIT_CLIENT_ID) {
  throw new Error('SCALEKIT_CLIENT_ID is not defined');
}

if (!process.env.SCALEKIT_CLIENT_SECRET) {
  throw new Error('SCALEKIT_CLIENT_SECRET is not defined');
}

// Initialize Scalekit for SSO only
export const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

export const SSO_CALLBACK_URL = process.env.SCALEKIT_SSO_CALLBACK_URL!;
```

## File 3: lib/db.ts (UPDATE - Add SSO fields)

```typescript
// Your existing database module - just add SSO fields

export interface User {
  id: string;
  email: string;
  name?: string;
  // Your existing fields...

  // NEW: SSO fields
  ssoEnabled?: boolean;
  organizationId?: string;
  ssoConnectionId?: string;
  lastLogin?: Date;
}

export async function findOrCreateUser(userData: {
  email: string;
  name?: string;
  ssoEnabled?: boolean;
  organizationId?: string;
  ssoConnectionId?: string;
}): Promise<User> {
  const { email, name, ssoEnabled, organizationId, ssoConnectionId } = userData;

  // Find existing user
  let user = await db.user.findUnique({
    where: { email: email.toLowerCase() },
  });

  if (user) {
    // Update existing user with SSO info
    user = await db.user.update({
      where: { id: user.id },
      data: {
        lastLogin: new Date(),
        ssoEnabled: ssoEnabled,
        organizationId: organizationId,
        ssoConnectionId: ssoConnectionId,
        updatedAt: new Date(),
      },
    });

    return user;
  }

  // Create new user
  user = await db.user.create({
    data: {
      email: email.toLowerCase(),
      name: name,
      ssoEnabled: ssoEnabled || false,
      organizationId: organizationId,
      ssoConnectionId: ssoConnectionId,
      createdAt: new Date(),
      lastLogin: new Date(),
    },
  });

  return user;
}
```

## File 4: app/auth/sso/login/route.ts (NEW)

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { scalekit, SSO_CALLBACK_URL } from '@/lib/scalekit';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const orgId = searchParams.get('org_id');
    const email = searchParams.get('email');

    if (!orgId && !email) {
      return NextResponse.redirect(
        new URL('/login?error=missing_org_or_email', request.url)
      );
    }

    // Generate SSO authorization URL
    let authUrl: string;

    if (orgId) {
      // Route by organization ID
      authUrl = scalekit.getAuthorizationUrl(SSO_CALLBACK_URL, {
        organizationId: orgId,
      });
    } else {
      // Route by email domain
      authUrl = scalekit.getAuthorizationUrl(SSO_CALLBACK_URL, {
        loginHint: email!,
      });
    }

    return NextResponse.redirect(authUrl);
  } catch (error) {
    console.error('SSO login error:', error);
    return NextResponse.redirect(
      new URL('/login?error=sso_failed', request.url)
    );
  }
}
```

## File 5: app/auth/sso/callback/route.ts (NEW)

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { scalekit, SSO_CALLBACK_URL } from '@/lib/scalekit';
import { findOrCreateUser } from '@/lib/db';
import { createSession } from '@/lib/auth'; // Your existing session creation

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get('code');
    const error = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');
    const idpInitiatedLogin = searchParams.get('idp_initiated_login');

    // Handle IdP-initiated login
    if (idpInitiatedLogin) {
      const claims = await scalekit.getIdpInitiatedLoginClaims(idpInitiatedLogin);

      const authUrl = scalekit.getAuthorizationUrl(SSO_CALLBACK_URL, {
        connectionId: claims.connection_id,
        organizationId: claims.organization_id,
      });

      return NextResponse.redirect(authUrl);
    }

    // Handle OAuth errors
    if (error) {
      console.error('SSO callback error:', error, errorDescription);
      return NextResponse.redirect(
        new URL(`/login?error=${encodeURIComponent(errorDescription || error)}`, request.url)
      );
    }

    if (!code) {
      return NextResponse.redirect(
        new URL('/login?error=missing_code', request.url)
      );
    }

    // Exchange code for user profile
    const result = await scalekit.authenticateWithCode(code, SSO_CALLBACK_URL);
    const { user } = result;

    console.log('SSO user authenticated:', {
      email: user.email,
      org_id: result.organization_id,
    });

    // Find or create user in YOUR database
    const appUser = await findOrCreateUser({
      email: user.email,
      name: user.name || `${user.given_name || ''} ${user.family_name || ''}`.trim(),
      ssoEnabled: true,
      organizationId: result.organization_id,
      ssoConnectionId: result.connection_id,
    });

    // Create YOUR session (not Scalekit's)
    // This uses your existing authentication system
    const response = NextResponse.redirect(new URL('/dashboard', request.url));
    await createSession(response, {
      userId: appUser.id,
      email: appUser.email,
      authMethod: 'sso',
    });

    console.log('User session created:', {
      userId: appUser.id,
      email: appUser.email,
    });

    return response;
  } catch (error) {
    console.error('SSO callback error:', error);
    return NextResponse.redirect(
      new URL('/login?error=authentication_failed', request.url)
    );
  }
}
```

## File 6: app/api/sso/check/route.ts (NEW)

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { scalekit } from '@/lib/scalekit';

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();

    if (!email) {
      return NextResponse.json(
        { error: 'Email required' },
        { status: 400 }
      );
    }

    const domain = email.split('@')[1];

    // Check if domain has SSO configured
    const connections = await scalekit.connections.listConnectionsByDomain({
      domain: domain,
    });

    if (connections.length > 0) {
      return NextResponse.json({
        ssoAvailable: true,
        connectionId: connections[0].id,
        organizationId: connections[0].organization_id,
      });
    } else {
      return NextResponse.json({
        ssoAvailable: false,
      });
    }
  } catch (error) {
    console.error('SSO check error:', error);
    return NextResponse.json(
      { error: 'Failed to check SSO availability' },
      { status: 500 }
    );
  }
}
```

## File 7: lib/auth.ts (UPDATE - Add SSO session creation)

```typescript
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
// Or use your existing session library (iron-session, next-auth, etc.)

export interface SessionData {
  userId: string;
  email: string;
  authMethod: 'password' | 'sso';
}

/**
 * Create session after SSO authentication
 * Integrates with your existing session system
 */
export async function createSession(
  response: NextResponse,
  data: SessionData
): Promise<void> {
  // Option 1: Using cookies directly
  const cookieStore = await cookies();

  cookieStore.set('session', JSON.stringify(data), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: '/',
  });

  // Option 2: Using iron-session
  // const session = await getIronSession(request, response, sessionOptions);
  // session.userId = data.userId;
  // session.email = data.email;
  // session.authMethod = data.authMethod;
  // await session.save();

  // Option 3: Using next-auth
  // Use your existing next-auth signIn callback
}

/**
 * Get current session
 */
export async function getSession(): Promise<SessionData | null> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get('session');

  if (!sessionCookie) {
    return null;
  }

  try {
    return JSON.parse(sessionCookie.value) as SessionData;
  } catch {
    return null;
  }
}

/**
 * Require authentication (works with both password and SSO)
 */
export async function requireAuth() {
  const session = await getSession();

  if (!session) {
    redirect('/login');
  }

  return session;
}
```

## File 8: components/login-form.tsx (NEW - Enhanced with SSO Detection)

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [ssoAvailable, setSsoAvailable] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  // Check for SSO when email changes
  const handleEmailBlur = async () => {
    if (!email || !email.includes('@')) return;

    try {
      const response = await fetch('/api/sso/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (data.ssoAvailable) {
        setSsoAvailable(true);
        setShowPassword(true);
      } else {
        setSsoAvailable(false);
        setShowPassword(true);
      }
    } catch (error) {
      console.error('SSO check failed:', error);
      setShowPassword(true);
    }
  };

  // Handle SSO login
  const handleSsoLogin = () => {
    setLoading(true);
    window.location.href = `/auth/sso/login?email=${encodeURIComponent(email)}`;
  };

  // Handle password login (your existing implementation)
  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Your existing password authentication
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        router.push('/dashboard');
      } else {
        alert('Login failed');
        setLoading(false);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Sign In</h1>

      <form onSubmit={handlePasswordLogin}>
        <div className="mb-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={handleEmailBlur}
            placeholder="Email"
            className="w-full px-4 py-2 border rounded-lg"
            required
          />
        </div>

        {ssoAvailable && (
          <div className="mb-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-800">
                ✓ SSO is available for your organization
              </p>
            </div>
            <button
              type="button"
              onClick={handleSsoLogin}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Continue with SSO
            </button>
            <div className="text-center text-gray-500 my-4">or</div>
          </div>
        )}

        {showPassword && (
          <>
            <div className="mb-4">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full px-4 py-2 border rounded-lg"
                required={!ssoAvailable}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gray-800 text-white py-2 px-4 rounded-lg hover:bg-gray-900 disabled:opacity-50"
            >
              Sign In with Password
            </button>
          </>
        )}
      </form>
    </div>
  );
}
```

## File 9: app/login/page.tsx (UPDATE - Use new login form)

```typescript
import { LoginForm } from '@/components/login-form';
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function LoginPage() {
  // Redirect if already authenticated
  const session = await getSession();
  if (session) {
    redirect('/dashboard');
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <LoginForm />
    </main>
  );
}
```

## Admin Portal for Customer SSO Setup

### File 10: app/api/admin/organizations/[orgId]/sso-portal/route.ts (NEW)

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { scalekit } from '@/lib/scalekit';
import { requireAuth } from '@/lib/auth';

export async function POST(
  request: NextRequest,
  { params }: { params: { orgId: string } }
) {
  try {
    // Verify admin access
    const session = await requireAuth();
    // Add your admin check here

    const { orgId } = params;

    const portalLink = await scalekit.organization.generatePortalLink(orgId);

    return NextResponse.json({
      portalUrl: portalLink,
      expiresIn: 3600, // 1 hour
    });
  } catch (error) {
    console.error('Portal generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate portal link' },
      { status: 500 }
    );
  }
}
```

### File 11: app/admin/organizations/[orgId]/sso-setup/page.tsx (NEW)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function SSOSetupPage() {
  const params = useParams();
  const orgId = params.orgId as string;
  const [portalUrl, setPortalUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/admin/organizations/${orgId}/sso-portal`, {
      method: 'POST',
    })
      .then((r) => r.json())
      .then((data) => {
        setPortalUrl(data.portalUrl);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to load portal:', error);
        setLoading(false);
      });
  }, [orgId]);

  if (loading) {
    return <div className="p-8">Loading SSO portal...</div>;
  }

  return (
    <div className="min-h-screen p-8">
      <h1 className="text-3xl font-bold mb-6">Configure SSO for Your Organization</h1>

      <div className="bg-white rounded-lg shadow-lg">
        {portalUrl ? (
          <iframe
            src={portalUrl}
            className="w-full h-[calc(100vh-200px)] border-0"
            title="SSO Configuration Portal"
          />
        ) : (
          <p className="p-8 text-red-600">Failed to load SSO portal</p>
        )}
      </div>
    </div>
  );
}
```

## Database Migration (Prisma Example)

```prisma
// schema.prisma - ADD these fields to your existing User model

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?

  // Your existing fields...

  // NEW: SSO fields
  ssoEnabled      Boolean?  @default(false)
  organizationId  String?
  ssoConnectionId String?
  lastLogin       DateTime?

  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@index([organizationId])
  @@index([ssoConnectionId])
}
```

Run migration:
```bash
npx prisma migrate dev --name add-sso-fields
```

## Testing

### 1. Test SSO Detection

```bash
curl -X POST http://localhost:3000/api/sso/check \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Should return:
# {"ssoAvailable":true,"connectionId":"conn_...","organizationId":"org_..."}
```

### 2. Test SSO Login Flow

1. Visit http://localhost:3000/login
2. Enter email: `test@example.com`
3. See SSO available message
4. Click "Continue with SSO"
5. Complete authentication at IdP Simulator
6. Verify redirect to `/dashboard`
7. Check user created in database with SSO fields

### 3. Test IdP-Initiated Login

Configure IdP with ACS URL:
```
https://your-env.scalekit.com/sso/v1/connections/{connection_id}/acs
```

Start from IdP portal → should redirect to your app

### 4. Test Admin Portal

1. Visit `/admin/organizations/{org_id}/sso-setup`
2. Verify Scalekit portal loads in iframe
3. Configure SAML/OIDC connection
4. Test SSO with configured connection

## Usage Patterns

### Pattern 1: Unified Login (Recommended)

Single login page that auto-detects SSO availability.

**Benefits:**
- Seamless user experience
- No separate SSO button needed
- Automatic fallback to password

**Implementation:** See `components/login-form.tsx` above

### Pattern 2: Separate SSO Entry Point

Different pages for password and SSO users.

```typescript
// app/login/page.tsx - Regular login
// app/login/sso/page.tsx - SSO-specific login
```

### Pattern 3: Organization-Based Routing

Users select their organization first:

```typescript
// app/login/org-select/page.tsx
export default function OrgSelectPage() {
  // Show organization picker
  // Each org has SSO enabled/disabled flag
}
```

## Security Considerations

### Email Domain Verification

```typescript
// Verify email domain matches expected organization
const result = await scalekit.authenticateWithCode(code, SSO_CALLBACK_URL);
const userDomain = result.user.email.split('@')[1];

const org = await db.organization.findUnique({
  where: { id: result.organization_id },
});

if (org && !org.domains.includes(userDomain)) {
  throw new Error('Email domain not authorized for this organization');
}
```

### Session Security

```typescript
// Always use httpOnly cookies
const cookieStore = await cookies();
cookieStore.set('session', sessionData, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  maxAge: 60 * 60 * 24 * 7, // 7 days
});
```

## Integration Examples

### With NextAuth.js

```typescript
// app/auth/sso/callback/route.ts
import { signIn } from 'next-auth/react';

// After SSO authentication
const appUser = await findOrCreateUser({...});

// Create NextAuth session
await signIn('credentials', {
  userId: appUser.id,
  email: appUser.email,
  redirect: false,
});
```

### With iron-session

```typescript
import { getIronSession } from 'iron-session';

export async function createSession(response: NextResponse, data: SessionData) {
  const session = await getIronSession(request, response, {
    password: process.env.SESSION_SECRET!,
    cookieName: 'app_session',
  });

  session.userId = data.userId;
  session.email = data.email;
  session.authMethod = data.authMethod;

  await session.save();
}
```

### With Auth0 (Existing Auth + Scalekit SSO)

```typescript
// Keep Auth0 for password auth
// Use Scalekit only for enterprise SSO

// app/auth/sso/callback/route.ts
const appUser = await findOrCreateUser({...});

// Create Auth0 session using Management API
const auth0Session = await createAuth0Session(appUser);
```

## Production Deployment

### Vercel

1. Push code to GitHub
2. Import to Vercel
3. Add environment variables in Vercel dashboard
4. Register production callback URL in Scalekit Dashboard

### Environment Variables for Production

```bash
SCALEKIT_ENVIRONMENT_URL=https://prod-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_prod_...
SCALEKIT_CLIENT_SECRET=prod_...
SCALEKIT_SSO_CALLBACK_URL=https://yourapp.com/auth/sso/callback

# Your existing variables
DATABASE_URL=...
AUTH_SECRET=...
```

## Production Checklist

- [ ] Disable Full-Stack Auth in Scalekit Dashboard
- [ ] Register SSO callback URL in Scalekit Dashboard
- [ ] Add SSO fields to database schema
- [ ] Update login page with SSO detection
- [ ] Test IdP-initiated login
- [ ] Configure customer admin portal
- [ ] Set up domain verification
- [ ] Add logging for SSO events
- [ ] Test with real IdP (Okta/Azure AD/Google Workspace)
- [ ] Document SSO setup for customers
- [ ] Set up error monitoring
- [ ] Configure CSP headers
- [ ] Test on mobile devices

## Advanced Features

### Automatic Organization Assignment

```typescript
// Assign user to organization based on email domain
const domain = email.split('@')[1];
const org = await db.organization.findFirst({
  where: { domains: { has: domain } },
});

if (org) {
  await db.user.update({
    where: { id: user.id },
    data: { organizationId: org.id },
  });
}
```

### Role Mapping from IdP

```typescript
// Map IdP groups/roles to app roles
const result = await scalekit.authenticateWithCode(code, SSO_CALLBACK_URL);
const groups = result.user.groups || [];

const appRoles = groups.map(group => {
  // Map IdP groups to app roles
  if (group === 'admins') return 'admin';
  if (group === 'managers') return 'manager';
  return 'user';
});

await db.user.update({
  where: { email: result.user.email },
  data: { roles: appRoles },
});
```

### SCIM Provisioning

Enable automatic user provisioning from IdP:

```typescript
// Scalekit handles SCIM endpoints automatically
// Users are created/updated before SSO login
// Access via Scalekit Dashboard → Organizations → SCIM
```

## Troubleshooting

**SSO button doesn't appear:**
- Check `/api/sso/check` returns `ssoAvailable: true`
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

**Session not persisting:**
- Verify cookie settings (httpOnly, secure, sameSite)
- Check `createSession` implementation
- Ensure cookies are sent with requests

## Next Steps

- Enable domain verification for automatic routing
- Set up SCIM for user provisioning
- Add role mapping from IdP attributes
- Implement JIT (Just-In-Time) provisioning
- Add organization-specific customization
- Enable audit logs for compliance
