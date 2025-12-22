# Scalekit Next.js Authentication Demo

This is a complete working example of Scalekit authentication implemented in a Next.js application using the App Router. **All code is based ONLY on the Scalekit Authentication Claude Skill templates.**

## Purpose

This project tests whether the Scalekit Authentication Claude Skill provides accurate and complete implementation guidance. It uses the exact code patterns from the skill's Next.js template.

## Project Structure

```
scalekit-nextjs-demo/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page with login/logout
│   ├── globals.css             # Tailwind styles
│   ├── dashboard/
│   │   └── page.tsx            # Protected dashboard (shows user data)
│   ├── auth/
│   │   ├── login/
│   │   │   └── route.ts        # Login endpoint (redirects to Scalekit)
│   │   ├── callback/
│   │   │   └── route.ts        # OAuth callback handler
│   │   └── logout/
│   │       └── route.ts        # Logout endpoint
│   └── api/
│       └── me/
│           └── route.ts        # Get current user API
├── lib/
│   ├── scalekit.ts             # Scalekit SDK initialization
│   └── auth.ts                 # Auth helper functions (using validateToken)
├── .env.local.example          # Environment variable template
├── package.json
└── README.md                   # This file
```

## Key Implementation Details

### ✅ Uses Fixed Token Validation Pattern

This implementation uses the FIXED `validateToken()` method with options:

```typescript
// lib/auth.ts - Uses the fixed pattern from the skill
const claims = await scalekit.validateToken(accessToken, {
  issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
  audience: process.env.SCALEKIT_CLIENT_ID
});
```

**NOT** the broken `validateAccessToken()` which returns boolean.

### Features Implemented

- ✅ Login flow with Scalekit OAuth
- ✅ Callback handling and token exchange
- ✅ Logout with Scalekit session termination
- ✅ Protected routes (Dashboard)
- ✅ Token validation with proper claims extraction
- ✅ User session management
- ✅ Token refresh logic
- ✅ Cookie-based authentication
- ✅ Error handling

## Prerequisites

Before running this project, you need:

1. **Scalekit Account**
   - Sign up at <https://scalekit.com>
   - Create a new application

2. **Scalekit Credentials**
   - Environment URL (from Dashboard → Settings)
   - Client ID (from Dashboard → Settings)
   - Client Secret (from Dashboard → Settings)

3. **Redirect URLs Registration**
   - In Scalekit Dashboard → Settings → Redirect URLs
   - Add these URLs:
     - **Callback URL:** `http://localhost:3000/auth/callback`
     - **Post Logout URL:** `http://localhost:3000`

   **CRITICAL:** Both URLs must be registered or authentication/logout will fail

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd scalekit-nextjs-demo
npm install
```

### Step 2: Configure Environment Variables

Copy the example environment file:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your Scalekit credentials:

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

### Step 3: Run the Development Server

```bash
npm run dev
```

Open <http://localhost:3000> in your browser.

## Testing the Authentication Flow

### Test 1: Login Flow

1. Navigate to <http://localhost:3000>
2. You should see "You are not logged in"
3. Click "Sign In" button
4. You'll be redirected to Scalekit login page
5. Enter credentials or use social login
6. After successful login, you'll be redirected back to `/dashboard`
7. Dashboard should show:
   - Your user information (email, sub, name, etc.)
   - Token claims object with all JWT claims

**Expected:** Dashboard displays complete user data and claims

### Test 2: Token Validation

1. After logging in, open Developer Tools → Application → Cookies
2. You should see these cookies:
   - `accessToken` (HttpOnly)
   - `refreshToken` (HttpOnly)
   - `idToken` (HttpOnly)
   - `user` (readable by client)

3. Visit <http://localhost:3000/api/me>
4. You should see JSON response with:

   ```json
   {
     "user": { "sub": "...", "email": "...", ... },
     "claims": { "sub": "...", "email": "...", "iat": ..., "exp": ... }
   }
   ```

**Expected:** Claims object contains actual JWT data (sub, email, org_id, etc.), NOT just `true/false`

### Test 3: Protected Routes

1. Log out by clicking "Logout" button
2. Try to visit <http://localhost:3000/dashboard> directly
3. You should be redirected to `/auth/login`

**Expected:** Protected routes redirect unauthenticated users to login

### Test 4: Logout Flow

1. Log in again
2. Click "Logout" button
3. The logout flow should:
   - Clear all local cookies (accessToken, refreshToken, idToken, user)
   - Redirect to Scalekit's logout endpoint
   - Terminate the Scalekit session
   - Terminate the identity provider session (if using SSO)
   - Redirect back to POST_LOGOUT_URL (home page)

4. After logout:
   - Visit <http://localhost:3000/auth/login>
   - You should be prompted for credentials again (not auto-logged back in)
   - Visit <http://localhost:3000/dashboard>
   - You should be redirected to login (not see previous user data)

**Expected:** Complete logout from application, Scalekit, AND identity provider

**Important:**

- If you're auto-logged back in without credentials, the logout flow is incomplete
- This means `getLogoutUrl()` is not being called or POST_LOGOUT_URL is not registered
- Proper logout requires both local cookie clearing AND Scalekit session termination

## Verification Checklist

Use this checklist to verify the implementation works correctly:

- [ ] Login redirects to Scalekit
- [ ] After login, redirect to `/dashboard` works
- [ ] Dashboard shows complete user object (not `true`)
- [ ] Dashboard shows complete claims object (not `true`)
- [ ] `/api/me` returns user and claims (not booleans)
- [ ] Protected routes redirect when not authenticated
- [ ] Token refresh works when access token expires
- [ ] Logout clears all cookies
- [ ] Logout redirects to Scalekit logout endpoint
- [ ] Logout redirects back to home page (POST_LOGOUT_URL)
- [ ] After logout, login requires credentials again (not auto-login)
- [ ] After logout, visiting /dashboard redirects to login

## What This Tests

This project specifically tests:

### ✅ Issue #1 Fix: validateToken() Usage

The skill was updated to use `validateToken(token, {issuer, audience})` instead of the broken `validateAccessToken()` method.

**Testing:**

- Check `lib/auth.ts` - uses `validateToken()` with options
- Check Dashboard page - should display complete claims object
- Check `/api/me` - should return full JWT claims

**Expected Behavior:**

- `claims` is an object with properties like `{sub, email, org_id, iat, exp}`
- **NOT** a boolean `true/false`

### ✅ Issue #2 Fix: SDK Property Name

All organization methods use `scalekit.organization` (singular) not `scalekit.organizations` (plural).

**Testing:**

- This demo doesn't use organization methods, but the pattern is correct in the skill

### ✅ Proper Logout Implementation

The logout flow uses `scalekit.getLogoutUrl()` to properly terminate sessions on Scalekit AND the identity provider.

**Implementation in `app/auth/logout/route.ts`:**

```typescript
const idToken = cookieStore.get('idToken')?.value;
const logoutUrl = scalekit.getLogoutUrl(idToken, POST_LOGOUT_URL);

// Redirect to Scalekit logout
const response = NextResponse.redirect(logoutUrl);

// Clear all cookies using .set() with maxAge: 0
const cookieOptions = { path: '/', maxAge: 0 };
response.cookies.set('accessToken', '', cookieOptions);
response.cookies.set('refreshToken', '', cookieOptions);
response.cookies.set('idToken', '', cookieOptions);
response.cookies.set('user', '', cookieOptions);
```

**Testing:**

- Check `app/auth/logout/route.ts` - uses `getLogoutUrl()`
- After logout, logging in should require credentials (not auto-login)
- Cookies should be properly cleared (not persisting)

**Expected Behavior:**

- Logout redirects to Scalekit logout URL
- Scalekit terminates its session
- Identity provider session is terminated
- User redirected back to POST_LOGOUT_URL
- All local cookies cleared

## Troubleshooting

### Error: "SCALEKIT_ENVIRONMENT_URL is not defined"

- Make sure you created `.env.local` file
- Check that all environment variables are set
- Restart the dev server after adding env vars

### Error: "Authorization code missing"

- Make sure callback URL is registered in Scalekit Dashboard
- URL must be exactly: `http://localhost:3000/auth/callback`

### Error: "Failed to initiate login"

- Check that your Scalekit credentials are correct
- Verify the environment URL format (should be `https://your-env.scalekit.com`)

### Dashboard shows `true` instead of user data

- This means the old `validateAccessToken()` is being used
- Check `lib/auth.ts` - should use `validateToken()` with options
- This would indicate the skill template is outdated

### Logout auto-logs me back in

- This means the Scalekit session is not being terminated
- Verify `POST_LOGOUT_URL` is registered in Scalekit Dashboard
- Check `app/auth/logout/route.ts` - should call `scalekit.getLogoutUrl()`
- Ensure logout redirects to Scalekit logout endpoint (not directly to home)

### Cookies persist after logout

- This is a known Next.js issue with `.delete()` method
- Check `app/auth/logout/route.ts` - should use `.set(name, '', { maxAge: 0 })`
- NOT using `response.cookies.delete()`
- Clear browser cookies manually if still seeing old data

## Implementation Source

All code in this project comes from:

- **Skill File:** `skills/scalekit-auth/full-stack-auth/templates/nextjs.md`
- **Claude Skill:** Scalekit Authentication Skill v1.1.0

**No external documentation or resources were used** - only the skill content.

## What to Report

After testing, please report:

1. **What worked correctly:**
   - Which authentication flows succeeded
   - What data was displayed correctly

2. **What didn't work:**
   - Specific errors encountered
   - Missing functionality
   - Incorrect behavior

3. **Skill improvements needed:**
   - Missing instructions
   - Unclear guidance
   - Additional features needed

## Next Steps

If authentication works correctly, this validates:

- The skill provides complete implementation guidance
- The token validation fixes (validateToken) work correctly
- The templates are production-ready

If issues are found, update the skill templates to improve developer experience.

---

**Built with:** Next.js 15, TypeScript, Tailwind CSS, @scalekit-sdk/node
**Source:** Scalekit Authentication Claude Skill
**Purpose:** Validate skill accuracy and completeness
