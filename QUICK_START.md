# Quick Start Guide - Testing the Scalekit Skill

This guide will get you testing the skill in under 10 minutes.

## Prerequisites

- Python 3.7+ installed
- Anthropic API key (for workspace installation) OR Claude Code installed (for local)
- 10 minutes of time

---

## Option 1: Install to Claude Workspace (Recommended for Team Testing)

### Step 1: Install Dependencies

```bash
cd scalekit-auth-skill
pip install anthropic python-dotenv
```

### Step 2: Set API Key

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

### Step 3: Install Skill

```bash
python install_skill.py
```

**Expected output:**
```
============================================================
Scalekit Authentication Skill Installer
============================================================

Validating skill structure...
  ✅ SKILL.md
  ✅ full-stack-auth/quickstart.md
  ✅ full-stack-auth/templates/nodejs-express.md
  ... (more files)

Uploading skill to your workspace...

============================================================
✅ Skill installed successfully!
============================================================

Skill ID: skill_abc123...
```

### Step 4: Test with Claude

Open Claude (web or API) and try:

```
Help me implement Scalekit authentication in Express
```

**You should see:** Claude uses the skill and provides Scalekit-specific code with the SDK.

---

## Option 2: Install Locally for Claude Code

### Step 1: Install to Claude Code

```bash
cd scalekit-auth-skill
./install_local.sh
```

Choose:
- **Option 1** for global (all projects): `~/.claude/skills/`
- **Option 2** for project-specific: `.claude/skills/`

**Expected output:**
```
============================================================
Scalekit Authentication Skill - Local Installation
============================================================

✅ Skill directory validated
ℹ️  Found global skills directory: /Users/you/.claude/skills

Installing skill to: /Users/you/.claude/skills/scalekit-auth

  ✅ SKILL.md
  ✅ full-stack-auth/
  ... (more files)

============================================================
✅ Skill installed successfully!
============================================================
```

### Step 2: Test with Claude Code

```bash
claude
```

Then type:
```
Help me implement Scalekit authentication in Express
```

**You should see:** Claude references the skill and provides Scalekit-specific implementation.

---

## Quick Test: 5-Minute Validation

Once installed, run these 3 quick tests:

### Test 1: Basic Activation (1 min)

**Prompt:**
```
Help me implement Scalekit authentication
```

**✅ Pass if:** Claude mentions Scalekit SDK and asks about framework

**❌ Fail if:** Claude gives generic OAuth advice without mentioning Scalekit

---

### Test 2: Framework Detection (2 min)

**Prompt:**
```
Add Scalekit auth to my Express.js app
```

**✅ Pass if:**
- Provides Express-specific code
- Includes `@scalekit-sdk/node` package
- Shows `app.get()` routes
- Uses Express middleware pattern

**❌ Fail if:**
- Generic Node.js code
- No Express-specific patterns
- Just links to docs

---

### Test 3: Code Completeness (2 min)

**Prompt:**
```
Show me complete working code for Scalekit authentication in Express
```

**✅ Pass if:** You can copy-paste the code and it has:
- All imports
- Client initialization
- Login route
- Callback route
- Logout route
- Auth middleware
- Protected route example

**❌ Fail if:**
- Just code snippets
- Missing imports
- Incomplete examples

---

## Full Test Suite (30 minutes)

See [TEST_SCENARIOS.md](TEST_SCENARIOS.md) for comprehensive testing.

### Quick Command Reference

```bash
# Install for workspace
python install_skill.py

# Install locally
./install_local.sh

# Run validation tests
python scripts/validate_env.py
python scripts/test_connection.py

# View test scenarios
cat TEST_SCENARIOS.md

# View comprehensive testing guide
cat TESTING.md
```

---

## Test Results Checklist

After testing, verify:

**Installation:**
- [ ] Skill installed without errors
- [ ] Files present in correct location
- [ ] Scripts are executable

**Activation:**
- [ ] Activates on "Scalekit" mentions
- [ ] Activates on "authentication" + framework
- [ ] Doesn't activate on unrelated queries

**Code Quality:**
- [ ] Complete, working code provided
- [ ] Framework-specific patterns used
- [ ] Security best practices included
- [ ] Can copy-paste and run

**Documentation:**
- [ ] References skill guides
- [ ] Mentions validation scripts
- [ ] Provides next steps

---

## Common Issues & Solutions

### Issue: Skill not activating

**Symptoms:** Claude gives generic auth advice, doesn't mention Scalekit

**Solutions:**
1. Be more explicit: "Use Scalekit SDK to add authentication"
2. Check installation location
3. Verify SKILL.md exists and has correct metadata

---

### Issue: Wrong code provided

**Symptoms:** Code doesn't match framework or isn't Scalekit-specific

**Solutions:**
1. Mention framework explicitly in prompt
2. Check if skill templates have correct code
3. Try: "Use the Scalekit authentication skill for Express"

---

### Issue: Installation failed

**Symptoms:** Script errors during installation

**Solutions:**
1. Check Python version: `python --version` (need 3.7+)
2. Install dependencies: `pip install anthropic`
3. Check API key is valid
4. Verify file permissions

---

## Next Steps

### If Tests Pass ✅

1. **Run full test suite:** See [TEST_SCENARIOS.md](TEST_SCENARIOS.md)
2. **Test all frameworks:** Express, Next.js, FastAPI
3. **Try edge cases:** Error handling, token refresh, etc.
4. **Document results:** Use template in TESTING.md

### If Tests Fail ❌

1. **Document the failure:** Exact prompt, expected vs actual behavior
2. **Check installation:** Verify all files present
3. **Review skill content:** Check SKILL.md and templates
4. **Report issue:** Use format in TESTING.md

### If Tests Partially Pass ⚠️

1. **Identify what works:** Which scenarios pass?
2. **Identify what doesn't:** Which fail? Why?
3. **Prioritize fixes:** Critical issues first
4. **Re-test after fixes**

---

## Getting Help

**For installation issues:**
- Check README.md installation section
- Verify prerequisites met
- Check file permissions

**For testing issues:**
- See TESTING.md troubleshooting section
- Review TEST_SCENARIOS.md for expected behavior
- Check if prompt is explicit enough

**For skill content issues:**
- Review template files in full-stack-auth/templates/
- Check SKILL.md metadata and description
- Verify reference guides are complete

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ Scalekit Skill Quick Reference                          │
├─────────────────────────────────────────────────────────┤
│ Install (Workspace):                                    │
│   python install_skill.py                               │
│                                                          │
│ Install (Local):                                        │
│   ./install_local.sh                                    │
│                                                          │
│ Test Activation:                                        │
│   "Help me implement Scalekit authentication"           │
│                                                          │
│ Test Express:                                           │
│   "Add Scalekit auth to my Express app"                 │
│                                                          │
│ Test Next.js:                                           │
│   "Implement Scalekit in Next.js 14 App Router"         │
│                                                          │
│ Test FastAPI:                                           │
│   "Add Scalekit authentication to FastAPI"              │
│                                                          │
│ Validate Environment:                                   │
│   python scripts/validate_env.py                        │
│                                                          │
│ Test Connection:                                        │
│   python scripts/test_connection.py                     │
└─────────────────────────────────────────────────────────┘
```

---

## Success Criteria

**Minimum (5 min test):**
- ✅ Installs without errors
- ✅ Activates on explicit prompts
- ✅ Provides framework-specific code

**Good (30 min test):**
- ✅ All basic tests pass
- ✅ Code is complete and runnable
- ✅ Security practices included
- ✅ Multiple frameworks work

**Excellent (full test suite):**
- ✅ 95%+ test scenarios pass
- ✅ Edge cases handled
- ✅ Documentation clear
- ✅ Ready for customer use

---

## Time Investment

- **Quick validation:** 5-10 minutes
- **Framework testing:** 30 minutes
- **Full test suite:** 2-3 hours
- **Real-world simulation:** 30 minutes

**Recommended:** Start with quick validation, then expand based on results.

---

## Ready to Test?

1. Choose installation method (workspace or local)
2. Run installation script
3. Do 5-minute quick test
4. If passes, run full test suite
5. Document results
6. Report findings

**Let's go! 🚀**
