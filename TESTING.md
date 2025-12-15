# Scalekit Authentication Skill - Testing Guide

This guide provides comprehensive test scenarios to validate that the Scalekit authentication skill works correctly with Claude Code.

## Table of Contents

1. [Pre-Testing Setup](#pre-testing-setup)
2. [Skill Activation Tests](#skill-activation-tests)
3. [Framework-Specific Tests](#framework-specific-tests)
4. [Code Quality Tests](#code-quality-tests)
5. [Validation Scripts Tests](#validation-scripts-tests)
6. [Edge Cases & Error Handling](#edge-cases--error-handling)
7. [Success Criteria](#success-criteria)

---

## Pre-Testing Setup

### 1. Install the Skill

**For API/Workspace testing:**
```bash
cd scalekit-auth-skill
python install_skill.py
```

**For local Claude Code testing:**
```bash
cd scalekit-auth-skill
chmod +x install_local.sh
./install_local.sh
```

### 2. Prepare Test Environment

```bash
# Create a test directory
mkdir ~/test-scalekit-skill
cd ~/test-scalekit-skill

# Set up test Scalekit credentials
cat > .env << EOF
SCALEKIT_ENVIRONMENT_URL=https://test-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_test_123
SCALEKIT_CLIENT_SECRET=test_secret_456
CALLBACK_URL=http://localhost:3000/auth/callback
POST_LOGOUT_URL=http://localhost:3000
COOKIE_SECURE=false
EOF
```

### 3. Verify Skill Installation

```bash
# For API installation
# Check via Anthropic API that skill exists

# For local installation
ls ~/.claude/skills/scalekit-auth/SKILL.md
# or
ls .claude/skills/scalekit-auth/SKILL.md
```

---

## Skill Activation Tests

These tests verify that Claude correctly identifies when to use the skill.

### Test 1.1: Direct Scalekit Mention

**Prompt:**
```
Help me implement Scalekit authentication in my application
```

**Expected Behavior:**
- ✅ Skill activates automatically
- ✅ Claude asks about framework preference
- ✅ Offers to guide through implementation
- ✅ Mentions validation scripts

**What to Look For:**
- Claude should reference the skill's content (e.g., "I see you want to implement Scalekit authentication...")
- Should NOT just provide generic OAuth/authentication advice
- Should mention specific Scalekit SDK installation

**Validation:**
```
Look for phrases like:
- "Scalekit SDK"
- "full-stack-auth/quickstart.md" or reference to quickstart
- "@scalekit-sdk/node" or "scalekit-sdk-python"
```

---

### Test 1.2: Framework-Specific Request

**Prompt:**
```
Add Scalekit authentication to my Express.js app
```

**Expected Behavior:**
- ✅ Skill activates
- ✅ Claude identifies Express as the framework
- ✅ Provides Express-specific implementation
- ✅ References nodejs-express.md template

**What to Look For:**
- Should provide Express middleware patterns
- Should mention `cookie-parser`, `express` dependencies
- Should include complete working code
- Should NOT provide generic Node.js code

---

### Test 1.3: Implicit Authentication Request

**Prompt:**
```
I need to add login and user sessions to my Next.js 14 application
```

**Expected Behavior:**
- ⚠️ May or may not activate (less explicit)
- If activates: Should mention Scalekit as an option
- If doesn't activate: Should still provide auth guidance (generic)

**Note:** This tests whether the skill description is broad enough. Less explicit requests may not trigger the skill consistently.

---

### Test 1.4: Wrong Context (Should NOT Activate)

**Prompt:**
```
What's the weather like today?
```

**Expected Behavior:**
- ❌ Skill should NOT activate
- Claude provides normal response

---

## Framework-Specific Tests

### Test 2.1: Node.js + Express Implementation

**Prompt:**
```
I have an Express application. Help me implement Scalekit authentication with full session management, token refresh, and logout functionality.
```

**Expected Output Should Include:**

1. **Dependencies:**
   ```bash
   npm install express @scalekit-sdk/node cookie-parser dotenv
   ```

2. **File Structure:**
   - `lib/scalekit.js` - Client initialization
   - `middleware/auth.js` - Auth middleware
   - `app.js` - Main application

3. **Key Code Components:**
   - Scalekit client initialization
   - `/auth/login` route
   - `/auth/callback` route with token exchange
   - `/auth/logout` route
   - Auth middleware with token refresh
   - Protected route example

4. **Security Features:**
   - HttpOnly cookies
   - CSRF protection (sameSite: 'strict')
   - Token validation
   - Automatic refresh handling

**Validation Checklist:**
- [ ] Complete working code (not just snippets)
- [ ] All imports/requires present
- [ ] Environment variable references
- [ ] Cookie configuration with security flags
- [ ] Error handling included
- [ ] Comments explaining key parts

**Manual Test:**
```bash
# Copy the generated code
cd ~/test-scalekit-skill
mkdir express-test && cd express-test

# Create files as Claude suggested
# ...

# Install dependencies
npm install

# Try to run
node app.js

# Should start without errors (even if missing valid Scalekit creds)
```

---

### Test 2.2: Next.js App Router Implementation

**Prompt:**
```
I'm building a Next.js 14 application with the App Router. Help me add Scalekit authentication with server components and server actions.
```

**Expected Output Should Include:**

1. **Dependencies:**
   ```bash
   npm install @scalekit-sdk/node
   ```

2. **File Structure:**
   - `lib/scalekit.ts`
   - `lib/auth.ts` (with `requireAuth`, `getCurrentUser`)
   - `app/auth/login/route.ts`
   - `app/auth/callback/route.ts`
   - `app/auth/logout/route.ts`
   - `app/dashboard/page.tsx` (protected example)
   - `middleware.ts` (optional)

3. **Key Code Components:**
   - TypeScript types
   - Server-side cookie handling with `cookies()` from `next/headers`
   - Route handlers for auth endpoints
   - Protected page component using `requireAuth`
   - Proper Next.js 14 patterns (async server components)

**Validation Checklist:**
- [ ] TypeScript syntax
- [ ] Uses Next.js 14 App Router patterns
- [ ] Server components (async functions)
- [ ] Cookie handling with `next/headers`
- [ ] `redirect()` for unauthorized access
- [ ] Example protected page

**Manual Test:**
```bash
cd ~/test-scalekit-skill
npx create-next-app@latest nextjs-test --typescript --app --use-npm

# Add Claude's code
# Try to build
npm run build

# Should compile successfully (TypeScript validation)
```

---

### Test 2.3: Python + FastAPI Implementation

**Prompt:**
```
Implement Scalekit authentication in my FastAPI application with automatic token refresh and protected routes.
```

**Expected Output Should Include:**

1. **Dependencies:**
   ```bash
   pip install fastapi uvicorn scalekit-sdk-python python-dotenv
   ```

2. **File Structure:**
   - `lib/scalekit.py`
   - `middleware/auth.py`
   - `app.py`

3. **Key Code Components:**
   - ScalekitClient initialization
   - `get_current_user` dependency
   - Auth routes (`/auth/login`, `/auth/callback`, `/auth/logout`)
   - Protected route with `Depends(get_current_user)`
   - Cookie handling with FastAPI Response

**Validation Checklist:**
- [ ] Python 3.7+ syntax
- [ ] FastAPI dependency injection patterns
- [ ] Type hints present
- [ ] Async/await where appropriate
- [ ] Response cookie setting/deletion
- [ ] Exception handling

**Manual Test:**
```bash
cd ~/test-scalekit-skill
mkdir fastapi-test && cd fastapi-test

# Create files as Claude suggested
# Install dependencies
pip install -r requirements.txt

# Try to run
python -m uvicorn app:app --reload

# Should start without errors
```

---

## Code Quality Tests

### Test 3.1: Security Best Practices

**Prompt:**
```
Show me how to implement Scalekit authentication securely in Express
```

**Expected Behavior:**
- ✅ HttpOnly cookies mentioned and used
- ✅ `secure: true` for production
- ✅ `sameSite: 'strict'` for CSRF protection
- ✅ No tokens in localStorage
- ✅ Token validation on every request
- ✅ Error messages don't leak sensitive info

**Validation:**
Look for:
```javascript
{
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'strict'
}
```

---

### Test 3.2: Error Handling

**Prompt:**
```
Add proper error handling to the Scalekit authentication callback
```

**Expected Output Should Include:**
- Try-catch blocks
- OAuth error parameter handling
- User-friendly error messages
- Logging (console.error or similar)
- Redirect to error page or login

**Validation:**
```javascript
if (error) {
  console.error('OAuth error:', error, error_description);
  return res.redirect('/?error=' + encodeURIComponent(error_description));
}
```

---

### Test 3.3: Token Refresh Logic

**Prompt:**
```
Implement automatic token refresh in the authentication middleware
```

**Expected Output Should Include:**
- Validate access token first
- Catch validation error
- Attempt refresh with refresh token
- Update cookies with new tokens
- Clear cookies if refresh fails
- Redirect to login if session expired

**Validation:**
```javascript
try {
  await scalekit.validateAccessToken(accessToken);
} catch (validationError) {
  // Refresh logic here
  const result = await scalekit.refreshAccessToken(refreshToken);
  // Update cookies
}
```

---

## Validation Scripts Tests

### Test 4.1: Environment Validation Script

**Prompt:**
```
My Scalekit environment isn't working. Help me validate my setup.
```

**Expected Behavior:**
- ✅ Claude mentions or provides the validation script
- ✅ Explains how to run it
- ✅ Explains what it checks

**Expected Guidance:**
```bash
python scripts/validate_env.py
```

**Manual Test:**
```bash
cd ~/.claude/skills/scalekit-auth  # or workspace path
python scripts/validate_env.py

# Should check environment variables and provide feedback
```

---

### Test 4.2: Connection Testing

**Prompt:**
```
How do I test if my Scalekit credentials are working?
```

**Expected Behavior:**
- ✅ References `test_connection.py` script
- ✅ Explains what the script does
- ✅ Shows how to run it

**Manual Test:**
```bash
cd ~/.claude/skills/scalekit-auth
python scripts/test_connection.py

# Should test SDK initialization and URL generation
```

---

## Edge Cases & Error Handling

### Test 5.1: Missing Environment Variables

**Prompt:**
```
I'm getting an error about missing SCALEKIT_CLIENT_SECRET. What should I do?
```

**Expected Behavior:**
- ✅ References environment setup
- ✅ Mentions .env file
- ✅ Suggests running validate_env.py
- ✅ Shows example .env structure

---

### Test 5.2: Callback URL Mismatch

**Prompt:**
```
I'm getting "redirect_uri_mismatch" error from Scalekit
```

**Expected Behavior:**
- ✅ Explains callback URL must match Dashboard exactly
- ✅ Mentions including protocol and port
- ✅ Suggests checking Scalekit Dashboard settings
- ✅ Shows example of correct URL format

---

### Test 5.3: Cookie Not Persisting

**Prompt:**
```
Users keep getting logged out. Sessions aren't persisting.
```

**Expected Behavior:**
- ✅ Checks cookie configuration
- ✅ Mentions secure flag (false for localhost)
- ✅ Mentions sameSite settings
- ✅ Suggests checking browser console
- ✅ References session-management.md guide

---

## Success Criteria

### Critical Requirements (Must Pass)

1. **Skill Activation**
   - [ ] Activates on "Scalekit" mentions
   - [ ] Activates on "authentication" + "Express/Next.js/FastAPI"
   - [ ] Doesn't activate on unrelated queries

2. **Code Completeness**
   - [ ] Provides complete, working code (not snippets)
   - [ ] Includes all necessary imports
   - [ ] Includes environment variable references
   - [ ] Code can be copied and run (with valid credentials)

3. **Framework Accuracy**
   - [ ] Express code uses Express patterns
   - [ ] Next.js code uses App Router correctly
   - [ ] FastAPI code uses FastAPI patterns
   - [ ] No framework mixing (e.g., Express code in Next.js response)

4. **Security**
   - [ ] HttpOnly cookies always used for tokens
   - [ ] Secure flag mentioned for production
   - [ ] sameSite attribute present
   - [ ] Token validation on every request
   - [ ] No tokens in localStorage/sessionStorage

5. **Error Handling**
   - [ ] Try-catch blocks present
   - [ ] OAuth error handling
   - [ ] Token refresh error handling
   - [ ] User-friendly error messages

### Nice-to-Have

1. **Documentation**
   - [ ] Comments explain key parts
   - [ ] References to SKILL.md guides
   - [ ] Mentions validation scripts

2. **Best Practices**
   - [ ] Rate limiting mentioned
   - [ ] CORS configuration for SPAs
   - [ ] Logging recommendations

3. **Testing Guidance**
   - [ ] How to test the implementation
   - [ ] What URLs to visit
   - [ ] Expected flow described

---

## Testing Workflow

### Phase 1: Quick Validation (15 minutes)

```bash
# 1. Install skill
./install_local.sh

# 2. Test basic activation
claude
> "Help me implement Scalekit in Express"

# 3. Verify code quality
# - Complete code provided?
# - Security features present?
# - Can copy-paste and run?

# 4. Test one framework fully
# - Create test project
# - Add generated code
# - Verify it runs
```

### Phase 2: Comprehensive Testing (1 hour)

```bash
# Run all Test 1.x (Skill Activation)
# Run all Test 2.x (Framework-Specific)
# Run all Test 3.x (Code Quality)
# Run all Test 4.x (Validation Scripts)
# Run all Test 5.x (Edge Cases)

# Document any failures
# Note unexpected behaviors
```

### Phase 3: Real-World Simulation (30 minutes)

```bash
# Act as a customer would
# 1. Fresh project setup
# 2. Ask Claude for help
# 3. Follow Claude's instructions exactly
# 4. Note where you get stuck
# 5. Note what's confusing
```

---

## Test Results Template

Use this template to record test results:

```markdown
## Test Session: [Date]

### Environment
- Claude Version: [e.g., Claude Code v1.0.0]
- Skill Version: [e.g., v0.1.0]
- Installation Method: [API / Local]

### Test Results

#### Test 1.1: Direct Scalekit Mention
- Status: [PASS / FAIL / PARTIAL]
- Notes: [Any observations]

#### Test 1.2: Framework-Specific Request
- Status: [PASS / FAIL / PARTIAL]
- Notes: [Any observations]

[Continue for all tests...]

### Summary
- Tests Passed: [X / Total]
- Critical Issues: [List]
- Minor Issues: [List]
- Recommendations: [What to improve]
```

---

## Troubleshooting Test Failures

### Skill Not Activating

**Possible Causes:**
1. Skill not installed correctly
2. SKILL.md description not broad enough
3. Prompt too vague

**Solutions:**
1. Verify installation path
2. Check SKILL.md `description` field includes relevant keywords
3. Try more explicit prompts

### Wrong Code Generated

**Possible Causes:**
1. Skill activated but used wrong template
2. Framework not detected correctly
3. Skill content has errors

**Solutions:**
1. Check prompt mentions framework explicitly
2. Review template files for accuracy
3. Fix template content if needed

### Incomplete Code

**Possible Causes:**
1. Template files are snippets, not complete code
2. Progressive disclosure working as intended (providing links)
3. Claude truncating long responses

**Solutions:**
1. Ensure templates have complete working code
2. Ask Claude to provide full implementation
3. Request specific files one at a time

---

## Next Steps After Testing

### If Tests Pass ✅
1. Document successful test scenarios
2. Create demo video showing skill in action
3. Prepare customer onboarding materials
4. Proceed with additional implementation paths

### If Tests Fail ❌
1. Document failure modes
2. Identify root causes:
   - Skill description issues?
   - Template content problems?
   - Framework detection failures?
3. Fix issues and re-test
4. Iterate until all critical tests pass

### If Tests Partially Pass ⚠️
1. Categorize: What works? What doesn't?
2. Prioritize critical failures
3. Note minor issues for future improvement
4. Decide if ready for customer beta testing

---

## Reporting Issues

When reporting skill issues, include:

1. **Exact prompt used**
2. **Expected behavior**
3. **Actual behavior**
4. **Claude's full response** (if possible)
5. **Skill version**
6. **Installation method**

Example:
```
Issue: Skill provides generic auth code instead of Scalekit-specific

Prompt: "Add authentication to my Express app"

Expected: Should mention Scalekit SDK and provide Scalekit-specific code

Actual: Provided generic Passport.js implementation

Skill Version: v0.1.0
Installation: Local (~/.claude/skills/)
```

---

## Success Metrics

Track these metrics across test sessions:

- **Activation Rate**: % of relevant prompts that activate skill
- **Code Accuracy**: % of generated code that runs without errors
- **Framework Detection**: % of framework-specific requests handled correctly
- **Security Compliance**: % of implementations using HttpOnly cookies, proper flags
- **Completeness**: % of responses providing full working code

**Target Metrics:**
- Activation Rate: >90% for explicit prompts
- Code Accuracy: >95% (should compile/run)
- Framework Detection: >95%
- Security Compliance: 100%
- Completeness: >90% (full working implementations)
