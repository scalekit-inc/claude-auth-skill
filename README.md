# Scalekit Authentication Skill

A Claude skill for implementing Scalekit authentication in web applications. This skill helps developers quickly implement secure authentication with full-stack auth, session management, and token handling.

## Overview

This skill provides comprehensive guidance for implementing:

- **Full-Stack Authentication** - Complete user sign-up, login, logout, and session management
- Framework-specific templates for Node.js, Next.js, and Python
- Secure token storage and validation
- Automatic token refresh
- Production-ready security best practices

**Status:** Prototype - Full-stack authentication path

## Directory Structure

```
scalekit-auth-skill/
├── SKILL.md                              # Main skill entry point
├── README.md                             # This file
├── full-stack-auth/
│   ├── quickstart.md                     # Step-by-step implementation guide
│   └── templates/
│       ├── nodejs-express.md             # Complete Express.js template
│       ├── nextjs.md                     # Complete Next.js App Router template
│       └── python-fastapi.md             # Complete FastAPI template
├── reference/
│   ├── session-management.md             # Session & token management guide
│   └── security-best-practices.md        # Security implementation guide
└── scripts/
    ├── validate_env.py                   # Environment validation script
    ├── test_connection.py                # Scalekit connectivity test
    └── test_auth_flow.py                 # Interactive auth flow test
```

## Installation

### For Claude API (Workspace-Wide)

```python
import anthropic
from anthropic.lib import files_from_dir

client = anthropic.Anthropic()

skill = client.beta.skills.create(
    display_title="Scalekit Authentication",
    files=files_from_dir("./scalekit-auth-skill"),
    betas=["skills-2025-10-02"]
)

print(f"✅ Skill installed: {skill.id}")
```

### For Claude Code (Local)

```bash
# Copy skill to Claude Code skills directory
cp -r scalekit-auth-skill ~/.claude/skills/

# Or for project-specific installation
cp -r scalekit-auth-skill .claude/skills/
```

## Testing the Skill

### 1. Validate Environment Setup

Before using the skill, ensure you have Scalekit credentials:

```bash
cd scalekit-auth-skill

# Install Python dependencies for validation scripts
pip install scalekit-sdk-python python-dotenv

# Create .env file with your Scalekit credentials
cat > .env << EOF
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_...
SCALEKIT_CLIENT_SECRET=test_...
CALLBACK_URL=http://localhost:3000/auth/callback
POST_LOGOUT_URL=http://localhost:3000
COOKIE_SECURE=false
EOF

# Run validation
python scripts/validate_env.py
```

Expected output:
```
============================================================
Scalekit Environment Validation
============================================================

Required Scalekit Credentials:
----------------------------------------
✅ SCALEKIT_ENVIRONMENT_URL: https://your-env.scalekit.com
✅ SCALEKIT_CLIENT_ID: skc_12345...
✅ SCALEKIT_CLIENT_SECRET: test_123...

Application URLs:
----------------------------------------
✅ CALLBACK_URL: http://localhost:3000/auth/callback
✅ POST_LOGOUT_URL: http://localhost:3000

============================================================
✅ All required environment variables are set correctly!
============================================================
```

### 2. Test Scalekit Connectivity

```bash
python scripts/test_connection.py
```

Expected output:
```
============================================================
Scalekit Connection Test
============================================================

Environment Configuration:
----------------------------------------
Environment URL: https://your-env.scalekit.com
Client ID: skc_12345...
Client Secret: test_123...

Initializing Scalekit client...
✅ Client initialized successfully

Testing authorization URL generation...
✅ Authorization URL generated successfully

Testing logout URL generation...
✅ Logout URL generated successfully

============================================================
✅ Connection test completed successfully!
============================================================
```

### 3. Test with Claude

Create a test conversation with Claude:

```
User: Help me implement Scalekit authentication in my Express.js app

Claude: I'll help you implement Scalekit authentication in your Express.js application.
[Skill activates and provides step-by-step guidance using the templates]
```

### 4. Test Interactive Auth Flow

For end-to-end testing:

```bash
python scripts/test_auth_flow.py
```

This script will:
1. Generate an authorization URL
2. Prompt you to complete authentication in browser
3. Exchange the code for tokens
4. Validate the tokens
5. Test token refresh

## Usage Examples

### Example 1: Implementing Full-Stack Auth in Express

```
User: I need to add authentication to my Express app using Scalekit

Claude: I'll help you implement full-stack authentication with Scalekit in your Express application.

Let me guide you through the setup:

1. First, install the required dependencies:
   npm install express @scalekit-sdk/node cookie-parser dotenv

2. Let's create the necessary files...
[Skill provides complete implementation from templates/nodejs-express.md]
```

### Example 2: Next.js Implementation

```
User: Add Scalekit auth to my Next.js 14 app with App Router

Claude: I'll help you implement Scalekit authentication in your Next.js App Router application.

Here's the implementation structure we'll create:
[Skill provides Next.js App Router implementation from templates/nextjs.md]
```

### Example 3: Python/FastAPI Implementation

```
User: Implement Scalekit authentication in FastAPI

Claude: I'll guide you through implementing Scalekit authentication in your FastAPI application.
[Skill provides FastAPI implementation from templates/python-fastapi.md]
```

## Skill Capabilities

### Framework Detection

The skill automatically detects your framework from context:

```
User: I'm using Express 4.x, help me add auth

Claude: [Uses nodejs-express.md template]

User: This is a Next.js project with App Router

Claude: [Uses nextjs.md template]

User: I have a FastAPI backend

Claude: [Uses python-fastapi.md template]
```

### Progressive Disclosure

The skill provides information progressively:

1. **Quick Start**: Framework selection and basic setup
2. **Implementation**: Step-by-step code with explanations
3. **Reference**: Links to detailed guides when needed
4. **Validation**: Scripts to verify implementation

### Validation Scripts

The skill includes three validation scripts:

**validate_env.py**
- Checks environment variables
- Validates URL formats
- Provides setup guidance

**test_connection.py**
- Tests Scalekit connectivity
- Validates SDK initialization
- Tests URL generation

**test_auth_flow.py**
- Interactive authentication test
- Token exchange validation
- Token refresh verification

## What's Included

### ✅ Implemented (Prototype)

- Full-stack authentication quickstart
- Node.js + Express template
- Next.js App Router template
- Python + FastAPI template
- Session management guide
- Security best practices guide
- Environment validation scripts
- Connection testing scripts
- Interactive auth flow testing

### 🚧 Planned (Future Versions)

- Modular SSO implementation guide
- MCP Server OAuth 2.1 implementation
- MCP Server custom auth integration
- Additional framework templates:
  - React SPA
  - Vue.js
  - Django
  - Ruby on Rails
  - Go
- Enterprise SSO setup guides
- Social login configuration
- Role-based access control (RBAC)
- Organization management
- Advanced token management

## Development & Testing Workflow

### 1. Create Test Application

```bash
# Node.js/Express
mkdir test-express-auth
cd test-express-auth
npm init -y
npm install express @scalekit-sdk/node cookie-parser dotenv
```

### 2. Use Claude with Skill

```
User: Create an Express app with Scalekit authentication

Claude: [Provides complete implementation using skill]
```

### 3. Validate Implementation

```bash
# Copy environment file
cp ../scalekit-auth-skill/.env .

# Run validation
python ../scalekit-auth-skill/scripts/validate_env.py

# Test connection
python ../scalekit-auth-skill/scripts/test_connection.py
```

### 4. Run Application

```bash
node app.js
```

### 5. Test Authentication Flow

1. Visit http://localhost:3000
2. Click "Sign In"
3. Complete authentication
4. Verify redirect to dashboard
5. Test protected routes
6. Test logout

## Troubleshooting

### Skill Not Activating

**Symptoms:** Claude doesn't use the skill when asking about authentication

**Solutions:**
1. Use specific keywords: "Scalekit", "authentication", "login", "sign-up"
2. Mention framework explicitly: "Express", "Next.js", "FastAPI"
3. Ask directly: "Use the Scalekit skill to help me implement authentication"

### Environment Validation Fails

**Symptoms:** `validate_env.py` shows errors

**Solutions:**
1. Ensure .env file exists in current directory
2. Check environment variable names match exactly
3. Verify Scalekit URLs don't have trailing slashes
4. Confirm credentials are from correct environment (dev/prod)

### Connection Test Fails

**Symptoms:** `test_connection.py` can't connect to Scalekit

**Solutions:**
1. Check internet connectivity
2. Verify SCALEKIT_ENVIRONMENT_URL is correct
3. Confirm credentials haven't expired
4. Check for firewall/proxy issues

### Templates Don't Work

**Symptoms:** Code from templates has errors

**Solutions:**
1. Ensure all dependencies are installed
2. Check Node.js/Python version compatibility
3. Verify callback URL is registered in Scalekit Dashboard
4. Check environment variables are loaded correctly

## Contributing

This is a prototype skill for Scalekit. To contribute:

1. Test the skill with different frameworks
2. Report issues or unclear guidance
3. Suggest additional framework templates
4. Provide feedback on documentation clarity

## Version History

### v0.1.0 - Prototype (Current)
- Full-stack authentication implementation
- Node.js/Express template
- Next.js App Router template
- Python/FastAPI template
- Validation scripts
- Reference documentation

### Future Roadmap

**v0.2.0 - Modular SSO**
- Modular SSO quickstart
- Integration with Auth0/Firebase/Cognito
- Enterprise onboarding guides

**v0.3.0 - MCP Authentication**
- MCP Server OAuth 2.1 implementation
- MCP Server custom auth integration
- Testing with Claude Desktop/Cursor

**v1.0.0 - Complete Suite**
- All authentication paths
- Additional framework templates
- Advanced features (RBAC, multi-tenancy)
- Production deployment guides

## Support

For Scalekit-related questions:
- Documentation: https://docs.scalekit.com
- Support: support@scalekit.com

For skill-related questions:
- Review skill documentation in SKILL.md
- Check reference guides in reference/
- Run validation scripts for diagnostics

## License

This skill is provided as-is for use with Scalekit authentication services.

## Next Steps

1. **Install the skill** using instructions above
2. **Validate your environment** with scripts/validate_env.py
3. **Test connectivity** with scripts/test_connection.py
4. **Start implementing** by asking Claude for help with your framework
5. **Review security** using reference/security-best-practices.md
6. **Deploy to production** following the guides in your framework template

---

Built with ❤️ for the Scalekit community
