# Next.js Template (App Router)

Complete authentication implementation for Next.js applications using the App Router.

## Quick Setup

```bash
# 1. Create Next.js app
npx create-next-app@latest my-app --typescript --app --use-npm

# 2. Install dependencies
cd my-app
npm install @scalekit-sdk/node

# 3. Create the files below
# 4. Set up .env.local file
# 5. Run: npm run dev
```

## Project Structure

```
my-app/
├── .env.local
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── dashboard/
│   │   └── page.tsx
│   ├── auth/
│   │   ├── login/
│   │   │   └── route.ts
│   │   ├── callback/
│   │   │   └── route.ts
│   │   └── logout/
│   │       └── route.ts
│   └── api/
│       └── me/
│           └── route.ts
├── lib/
│   ├── scalekit.ts
│   └── auth.ts
└── middleware.ts
```

## File 1: .env.local

```bash
# Scalekit credentials (from Dashboard → Settings)
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_12345...
SCALEKIT_CLIENT_SECRET=test_12345...

# Application URLs
NEXT_PUBLIC_APP_URL=http://localhost:3000
CALLBACK_URL=http://localhost:3000/auth/callback
POST_LOGOUT_URL=http://localhost:3000

# Cookie settings
COOKIE_SECURE=false  # Set to true in production
```

## File 2: lib/scalekit.ts

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

// Initialize Scalekit client
export const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

// Application URLs
export const CALLBACK_URL = process.env.CALLBACK_URL!;
export const POST_LOGOUT_URL = process.env.POST_LOGOUT_URL!;

// Cookie configuration
export const cookieConfig = {
  httpOnly: true,
  secure: process.env.COOKIE_SECURE === 'true',
  sameSite: 'strict' as const,
  path: '/',
};
```

## File 3: lib/auth.ts

```typescript
import { cookies } from 'next/headers';
import { scalekit, cookieConfig } from './scalekit';
import { redirect } from 'next/navigation';

export interface User {
  sub: string;
  email: string;
  email_verified?: boolean;
  name?: string;
  given_name?: string;
  family_name?: string;
}

/**
 * Get the current user from cookies
 * Returns null if not authenticated
 */
export async function getCurrentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  const userCookie = cookieStore.get('user');

  if (!userCookie) {
    return null;
  }

  try {
    return JSON.parse(userCookie.value) as User;
  } catch {
    return null;
  }
}

/**
 * Validate access token and return claims
 * Throws error if token is invalid or expired
 */
export async function validateAccessToken() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get('accessToken')?.value;

  if (!accessToken) {
    throw new Error('No access token found');
  }

  try {
    const claims = await scalekit.validateAccessToken(accessToken);
    return claims;
  } catch (error) {
    throw new Error('Invalid or expired access token');
  }
}

/**
 * Require authentication for server components/actions
 * Redirects to login if not authenticated
 */
export async function requireAuth() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get('accessToken')?.value;

  if (!accessToken) {
    redirect('/auth/login');
  }

  try {
    const claims = await scalekit.validateAccessToken(accessToken);
    return claims;
  } catch (error) {
    // Token invalid or expired, try to refresh
    const refreshToken = cookieStore.get('refreshToken')?.value;

    if (!refreshToken) {
      redirect('/auth/login');
    }

    try {
      const result = await scalekit.refreshAccessToken(refreshToken);

      // Update cookies
      cookieStore.set('accessToken', result.accessToken, {
        ...cookieConfig,
        maxAge: result.expiresIn,
      });

      if (result.refreshToken) {
        cookieStore.set('refreshToken', result.refreshToken, {
          ...cookieConfig,
          maxAge: 30 * 24 * 60 * 60, // 30 days
        });
      }

      const claims = await scalekit.validateAccessToken(result.accessToken);
      return claims;
    } catch {
      redirect('/auth/login');
    }
  }
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get('accessToken')?.value;

  if (!accessToken) {
    return false;
  }

  try {
    await scalekit.validateAccessToken(accessToken);
    return true;
  } catch {
    return false;
  }
}
```

## File 4: app/auth/login/route.ts

```typescript
import { NextRequest } from 'next/server';
import { scalekit, CALLBACK_URL } from '@/lib/scalekit';

export async function GET(request: NextRequest) {
  try {
    const authorizationUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
      scopes: ['openid', 'profile', 'email', 'offline_access'],
    });

    return Response.redirect(authorizationUrl);
  } catch (error) {
    console.error('Login error:', error);
    return new Response('Failed to initiate login', { status: 500 });
  }
}
```

## File 5: app/auth/callback/route.ts

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { scalekit, CALLBACK_URL, cookieConfig } from '@/lib/scalekit';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');
  const error = searchParams.get('error');
  const errorDescription = searchParams.get('error_description');

  // Handle OAuth errors
  if (error) {
    console.error('OAuth error:', error, errorDescription);
    return NextResponse.redirect(
      new URL(`/?error=${encodeURIComponent(errorDescription || error)}`, request.url)
    );
  }

  if (!code) {
    return new Response('Authorization code missing', { status: 400 });
  }

  try {
    // Exchange code for tokens
    const result = await scalekit.authenticateWithCode(code, CALLBACK_URL);

    const { accessToken, refreshToken, idToken, user, expiresIn } = result;

    // Create redirect response
    const response = NextResponse.redirect(new URL('/dashboard', request.url));

    // Set cookies
    response.cookies.set('accessToken', accessToken, {
      ...cookieConfig,
      maxAge: expiresIn,
    });

    response.cookies.set('refreshToken', refreshToken, {
      ...cookieConfig,
      maxAge: 30 * 24 * 60 * 60, // 30 days
    });

    response.cookies.set('idToken', idToken, {
      ...cookieConfig,
      maxAge: expiresIn,
    });

    // Store user info (not httpOnly so frontend can access)
    response.cookies.set('user', JSON.stringify(user), {
      maxAge: expiresIn,
      secure: cookieConfig.secure,
      sameSite: cookieConfig.sameSite,
      path: '/',
    });

    console.log('User authenticated:', user.email);

    return response;
  } catch (error) {
    console.error('Authentication error:', error);
    return NextResponse.redirect(
      new URL('/?error=Authentication%20failed', request.url)
    );
  }
}
```

## File 6: app/auth/logout/route.ts

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { scalekit, POST_LOGOUT_URL } from '@/lib/scalekit';
import { cookies } from 'next/headers';

export async function GET(request: NextRequest) {
  try {
    const cookieStore = await cookies();
    const idToken = cookieStore.get('idToken')?.value;

    // Generate Scalekit logout URL
    const logoutUrl = scalekit.getLogoutUrl(idToken, POST_LOGOUT_URL);

    // Create redirect response
    const response = NextResponse.redirect(logoutUrl);

    // Clear all auth cookies
    response.cookies.delete('accessToken');
    response.cookies.delete('refreshToken');
    response.cookies.delete('idToken');
    response.cookies.delete('user');

    return response;
  } catch (error) {
    console.error('Logout error:', error);
    return NextResponse.redirect(new URL('/', request.url));
  }
}
```

## File 7: app/api/me/route.ts

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/auth';
import { cookies } from 'next/headers';

export async function GET(request: NextRequest) {
  try {
    const claims = await requireAuth();
    const cookieStore = await cookies();
    const userCookie = cookieStore.get('user')?.value;

    const user = userCookie ? JSON.parse(userCookie) : null;

    return NextResponse.json({
      user,
      claims,
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Not authenticated' },
      { status: 401 }
    );
  }
}
```

## File 8: app/page.tsx

```typescript
import Link from 'next/link';
import { getCurrentUser, isAuthenticated } from '@/lib/auth';

export default async function Home() {
  const user = await getCurrentUser();
  const authenticated = await isAuthenticated();

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Scalekit Authentication Demo</h1>

      {authenticated && user ? (
        <div className="space-y-6">
          <div className="bg-gray-100 p-6 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">Welcome, {user.email}!</h2>
            <div className="space-y-2">
              <p><strong>User ID:</strong> {user.sub}</p>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Email Verified:</strong> {user.email_verified ? 'Yes' : 'No'}</p>
              {user.name && <p><strong>Name:</strong> {user.name}</p>}
            </div>
          </div>

          <div className="flex gap-4">
            <Link
              href="/dashboard"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
            >
              Go to Dashboard
            </Link>
            <Link
              href="/auth/logout"
              className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700"
            >
              Logout
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <p className="text-lg">You are not logged in.</p>
          <Link
            href="/auth/login"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Sign In
          </Link>
        </div>
      )}
    </main>
  );
}
```

## File 9: app/dashboard/page.tsx

```typescript
import { requireAuth, getCurrentUser } from '@/lib/auth';
import Link from 'next/link';

export default async function Dashboard() {
  const claims = await requireAuth();
  const user = await getCurrentUser();

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Dashboard</h1>

      <div className="space-y-6">
        <div className="bg-gray-100 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-4">User Information</h2>
          <pre className="bg-gray-800 text-gray-100 p-4 rounded overflow-x-auto">
            {JSON.stringify(user, null, 2)}
          </pre>
        </div>

        <div className="bg-gray-100 p-6 rounded-lg">
          <h2 className="text-2xl font-semibold mb-4">Token Claims</h2>
          <pre className="bg-gray-800 text-gray-100 p-4 rounded overflow-x-auto">
            {JSON.stringify(claims, null, 2)}
          </pre>
        </div>

        <div className="flex gap-4">
          <Link
            href="/"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            Home
          </Link>
          <Link
            href="/auth/logout"
            className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700"
          >
            Logout
          </Link>
        </div>
      </div>
    </main>
  );
}
```

## File 10: middleware.ts (Optional - for additional route protection)

```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const accessToken = request.cookies.get('accessToken')?.value;
  const { pathname } = request.nextUrl;

  // List of protected routes
  const protectedRoutes = ['/dashboard', '/api/me'];

  // Check if current path is protected
  const isProtectedRoute = protectedRoutes.some(route =>
    pathname.startsWith(route)
  );

  // Redirect to login if accessing protected route without token
  if (isProtectedRoute && !accessToken) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
};
```

## Usage

### 1. Set up environment

Create `.env.local` file with your Scalekit credentials.

### 2. Install dependencies

```bash
npm install
```

### 3. Start the development server

```bash
npm run dev
```

### 4. Test the flow

1. Visit http://localhost:3000
2. Click "Sign In"
3. Complete authentication
4. You'll be redirected to the dashboard
5. Test protected routes
6. Click "Logout"

## Server Actions Example

For form-based authentication or logout:

**app/actions/auth.ts:**
```typescript
'use server';

import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { scalekit, POST_LOGOUT_URL } from '@/lib/scalekit';

export async function logout() {
  const cookieStore = await cookies();
  const idToken = cookieStore.get('idToken')?.value;

  // Clear cookies
  cookieStore.delete('accessToken');
  cookieStore.delete('refreshToken');
  cookieStore.delete('idToken');
  cookieStore.delete('user');

  // Generate logout URL
  const logoutUrl = scalekit.getLogoutUrl(idToken, POST_LOGOUT_URL);

  redirect(logoutUrl);
}
```

**Usage in component:**
```typescript
import { logout } from '@/app/actions/auth';

export function LogoutButton() {
  return (
    <form action={logout}>
      <button type="submit">Logout</button>
    </form>
  );
}
```

## Client Component Example

For client-side interactivity:

**components/user-menu.tsx:**
```typescript
'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface User {
  email: string;
  name?: string;
}

export function UserMenu() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Fetch user data
    fetch('/api/me')
      .then(res => res.json())
      .then(data => setUser(data.user))
      .catch(() => setUser(null));
  }, []);

  if (!user) {
    return (
      <button
        onClick={() => router.push('/auth/login')}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        Sign In
      </button>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <span>Welcome, {user.email}</span>
      <button
        onClick={() => router.push('/auth/logout')}
        className="bg-gray-600 text-white px-4 py-2 rounded"
      >
        Logout
      </button>
    </div>
  );
}
```

## Production Deployment

### Vercel

1. Push code to GitHub
2. Import to Vercel
3. Add environment variables in Vercel dashboard
4. Set `COOKIE_SECURE=true`
5. Register production callback URL in Scalekit Dashboard

### Environment Variables for Production

```bash
SCALEKIT_ENVIRONMENT_URL=https://prod-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_prod_...
SCALEKIT_CLIENT_SECRET=prod_...

NEXT_PUBLIC_APP_URL=https://yourapp.com
CALLBACK_URL=https://yourapp.com/auth/callback
POST_LOGOUT_URL=https://yourapp.com

COOKIE_SECURE=true
```

### Deploy Checklist

- [ ] Set `COOKIE_SECURE=true`
- [ ] Register production callback URL in Scalekit Dashboard
- [ ] Configure custom domain
- [ ] Test authentication flow in production
- [ ] Set up error monitoring (Sentry, Bugsnag)
- [ ] Configure CSP headers
- [ ] Test on mobile devices

## Advanced Features

### Role-Based Access Control

```typescript
// lib/auth.ts
export async function requireRole(role: string) {
  const claims = await requireAuth();
  const roles = claims.roles || [];

  if (!roles.includes(role)) {
    redirect('/unauthorized');
  }

  return claims;
}

// app/admin/page.tsx
export default async function AdminPage() {
  await requireRole('admin');

  return <div>Admin Dashboard</div>;
}
```

### Organization-Based Access

```typescript
export async function requireOrganization(orgId: string) {
  const claims = await requireAuth();

  if (claims.org_id !== orgId) {
    redirect('/unauthorized');
  }

  return claims;
}
```

## Next Steps

- Add user profile page
- Implement role-based access control
- Enable social login in Scalekit Dashboard
- Add organization management
- Customize login UI
- Set up enterprise SSO for B2B customers
