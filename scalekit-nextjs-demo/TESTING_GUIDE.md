# Testing Guide - Scalekit Authentication Demo

This guide provides step-by-step instructions to test the authentication implementation and verify the Scalekit Claude Skill accuracy.

## Critical Test: Verify validateToken() Fix

**Most Important:** Verify that token validation returns claims object (not boolean).

### Expected Result

When you log in and visit the Dashboard:

```json
// ✅ CORRECT - Claims should be an object
{
  "sub": "usr_123abc...",
  "email": "user@example.com",
  "email_verified": true,
  "org_id": "org_456def...",
  "iat": 1703001234,
  "exp": 1703004834,
  "iss": "https://env_url.scalekit.com",
  "aud": "skc_12345..."
}
```

```javascript
// ❌ WRONG - Would indicate old validateAccessToken() is used
true  // or false
```

## Setup Steps

### 1. Get Scalekit Credentials

1. Go to <https://scalekit.com>
2. Sign up / Log in
3. Create a new application
4. Go to Dashboard → Settings
5. Copy these values:
   - **Environment URL** (e.g., `https://your-env.scalekit.com`)
   - **Client ID** (starts with `skc_`)
   - **Client Secret** (starts with `test_` or `live_`)

### 2. Register Callback URL

1. In Scalekit Dashboard → Settings → Redirect URLs
2. Add: `http://localhost:3000/auth/callback`
3. Save

### 3. Configure Environment

```bash
cd scalekit-nextjs-demo
cp .env.local.example .env.local
```

Edit `.env.local`:

```bash
SCALEKIT_ENVIRONMENT_URL=https://your-actual-env.scalekit.com  # ← Change this
SCALEKIT_CLIENT_ID=skc_your_actual_client_id                   # ← Change this
SCALEKIT_CLIENT_SECRET=test_your_actual_secret                 # ← Change this

NEXT_PUBLIC_APP_URL=http://localhost:3000
CALLBACK_URL=http://localhost:3000/auth/callback
POST_LOGOUT_URL=http://localhost:3000
COOKIE_SECURE=false
```

### 4. Install and Run

```bash
npm install
npm run dev
```

Open <http://localhost:3000>

---

## Test 1: Login Flow ✅

**Purpose:** Verify complete OAuth login flow works

### Steps

1. Navigate to <http://localhost:3000>
2. You should see:
   - "You are not logged in"
   - "Sign In" button

3. Click "Sign In" button
4. You'll be redirected to Scalekit login page
5. Enter your email/password or use social login
6. After login, you should be redirected to <http://localhost:3000/dashboard>

### Expected Results

- ✅ Redirect to Scalekit login works
- ✅ Login succeeds
- ✅ Redirect back to `/dashboard` works
- ✅ No errors in browser console

### If It Fails

**Error: "SCALEKIT_ENVIRONMENT_URL is not defined"**

- Check `.env.local` file exists
- Restart dev server: `npm run dev`

**Error: "Authorization code missing"**

- Check callback URL in Scalekit Dashboard matches exactly: `http://localhost:3000/auth/callback`

---

## Test 2: Token Validation (Critical!) 🔴

**Purpose:** Verify `validateToken()` returns claims object, not boolean

### Steps

1. After logging in (Test 1), you should be on `/dashboard`

2. Look at "User Information" section
   - Should show complete JSON object
   - Must have `sub`, `email`, `org_id`, etc.
   - Should NOT be just `true` or `false`

3. Look at "Token Claims" section
   - Should show complete JWT claims
   - Must have `iat`, `exp`, `iss`, `aud`, etc.
   - Should NOT be just `true` or `false`

4. Open <http://localhost:3000/api/me> in new tab
   - Should show JSON with `user` and `claims` objects
   - Both should be detailed objects, not booleans

### Expected Results

**User Information:**

```json
{
  "sub": "usr_123...",
  "email": "your@email.com",
  "email_verified": true,
  "name": "Your Name"
}
```

**Token Claims:**

```json
{
  "sub": "usr_123...",
  "email": "your@email.com",
  "email_verified": true,
  "org_id": "org_456...",
  "iat": 1703001234,
  "exp": 1703004834,
  "iss": "https://auth.scalekit.com",
  "aud": "skc_12345..."
}
```

**API Response (/api/me):**

```json
{
  "user": { "sub": "...", "email": "...", ... },
  "claims": { "sub": "...", "iat": ..., "exp": ..., ... }
}
```

### ❌ Failure Indicators

If you see ANY of these, the skill template is broken:

```json
// User Information showing:
true

// Token Claims showing:
true

// /api/me showing:
{
  "user": true,
  "claims": true
}
```

This would mean `validateAccessToken()` is being used instead of `validateToken()`.

---

## Test 3: Cookies Inspection 🍪

**Purpose:** Verify secure cookie configuration

### Steps

1. Open Developer Tools (F12)
2. Go to Application tab → Cookies
3. Look at cookies for `http://localhost:3000`

### Expected Results

You should see 4 cookies:

| Cookie | HttpOnly | Secure | SameSite | Contains |
|--------|----------|--------|----------|----------|
| `accessToken` | ✅ Yes | ❌ No (dev) | Strict | JWT token |
| `refreshToken` | ✅ Yes | ❌ No (dev) | Strict | JWT token |
| `idToken` | ✅ Yes | ❌ No (dev) | Strict | JWT token |
| `user` | ❌ No | ❌ No (dev) | Strict | User JSON |

**Notes:**

- `HttpOnly` = Yes means JavaScript cannot access (security feature)
- `Secure` = No in development (HTTP), should be Yes in production (HTTPS)
- `user` cookie is readable by JavaScript (intentional for frontend access)

---

## Test 4: Protected Routes 🔒

**Purpose:** Verify route protection works

### Steps

1. Make sure you're logged in
2. Click "Logout" button
3. You should be on home page (`/`)
4. Manually navigate to <http://localhost:3000/dashboard>
5. You should be immediately redirected to `/auth/login`

### Expected Results

- ✅ Logged out successfully
- ✅ Redirected to home page
- ✅ Accessing `/dashboard` without login redirects to `/auth/login`

---

## Test 5: Logout Flow 🚪

**Purpose:** Verify complete logout process

### Steps

1. Log in again (Test 1)
2. Go to Dashboard
3. Click "Logout" button

### Expected Results

- ✅ Redirected to Scalekit logout page
- ✅ Then redirected back to home page (`/`)
- ✅ All cookies cleared (check Developer Tools → Cookies)
- ✅ Home page shows "You are not logged in"
- ✅ Trying to access `/dashboard` redirects to login

### Verify Cookies Cleared

Open Developer Tools → Application → Cookies:

- ❌ No `accessToken`
- ❌ No `refreshToken`
- ❌ No `idToken`
- ❌ No `user`

---

## Test 6: Re-login After Logout 🔄

**Purpose:** Verify can log in again after logout

### Steps

1. After logging out (Test 5)
2. Click "Sign In" button
3. Complete login flow again

### Expected Results

- ✅ Can log in successfully again
- ✅ Dashboard shows user data correctly
- ✅ All functionality works as before

---

## Test 7: Token Refresh (Advanced) ⏱️

**Purpose:** Verify token refresh works when access token expires

**Note:** This test requires waiting for token expiration (usually 15-60 minutes)

### Steps

1. Log in
2. Go to Dashboard
3. Wait for access token to expire (check `exp` claim in Token Claims)
4. Refresh the page or navigate to a protected route

### Expected Results

- ✅ Token automatically refreshed using refresh token
- ✅ No redirect to login
- ✅ Dashboard still accessible
- ✅ New access token set in cookies

### Manual Testing (Don't Wait)

1. Log in and go to Dashboard
2. Open Developer Tools → Application → Cookies
3. Delete the `accessToken` cookie
4. Refresh the page

**Expected:**

- If refresh token is valid: Page loads with new access token
- If refresh token expired: Redirect to login

---

## Common Issues & Solutions

### Issue: "Module not found" errors

**Solution:**

```bash
rm -rf node_modules package-lock.json
npm install
```

### Issue: Port 3000 already in use

**Solution:**

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 npm run dev
```

Then update callback URL to `http://localhost:3001/auth/callback` in Scalekit Dashboard.

### Issue: Dashboard shows `true` instead of user object

**Diagnosis:** This is the critical bug we fixed!

**Root Cause:**

- The old skill used `validateAccessToken()` which returns boolean
- Should use `validateToken()` with options which returns claims object

**Solution:**
Check `lib/auth.ts` has:

```typescript
const claims = await scalekit.validateToken(token, {
  issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
  audience: process.env.SCALEKIT_CLIENT_ID
});
```

NOT:

```typescript
const claims = await scalekit.validateAccessToken(token);  // ❌ Wrong
```

### Issue: Redirect loop

**Diagnosis:** Cookie configuration issue

**Solution:**
Check `.env.local`:

```bash
COOKIE_SECURE=false  # Must be false for HTTP (localhost)
```

---

## Reporting Results

After completing all tests, please report:

### ✅ What Worked

- [ ] Login flow
- [ ] Dashboard displays user object (not boolean)
- [ ] Dashboard displays claims object (not boolean)
- [ ] /api/me returns proper objects
- [ ] Protected routes redirect correctly
- [ ] Logout flow clears cookies
- [ ] Can re-login after logout
- [ ] Token refresh works

### ❌ What Failed

For each failure, note:

- Which test failed
- Error message (if any)
- What was displayed vs. what was expected
- Browser console errors
- Network tab errors

### 📝 Skill Feedback

- Was the skill guidance clear?
- Were there missing instructions?
- Were there confusing parts?
- What could be improved?

---

## Success Criteria

The implementation is successful if:

1. ✅ All login/logout flows work
2. ✅ Dashboard shows **objects** not **booleans**
3. ✅ Token validation returns **claims** not **true/false**
4. ✅ Protected routes work correctly
5. ✅ Cookies are configured securely
6. ✅ No critical errors in console

If all tests pass, the Scalekit Claude Skill provides accurate, production-ready implementation guidance! 🎉

---

**Testing Estimated Time:** 15-20 minutes
**Critical Tests:** Test 2 (Token Validation)
**Optional Tests:** Test 7 (Token Refresh - requires waiting)
