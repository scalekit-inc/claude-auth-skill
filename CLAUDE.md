# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Scalekit Authentication Skill** - a comprehensive Claude skill that provides complete guidance for implementing Scalekit authentication across web applications, APIs, and MCP servers. This is NOT application code; it's a documentation repository that serves as a knowledge base for Claude when helping developers implement Scalekit authentication.

## Architecture & Structure

### Core Concept: Three Implementation Paths

The skill is organized around three distinct authentication implementation paths, each targeting different use cases:

1. **Full-Stack Authentication** (`full-stack-auth/`)
   - Complete authentication system where Scalekit handles ALL authentication
   - Scalekit manages user database, sessions, tokens
   - Includes login, signup, logout, social login, enterprise SSO
   - Templates: Express, Next.js, FastAPI

2. **Modular SSO** (`modular-sso/`)
   - Add Enterprise SSO (SAML/OIDC) to existing authentication systems
   - Customer keeps their existing auth, sessions, and user database
   - Scalekit handles only SSO protocol complexity
   - Templates: Express, Next.js

3. **MCP Server Authentication** (`mcp-auth/`)
   - OAuth 2.1 implementation for Model Context Protocol servers
   - Two approaches: Scalekit-managed OAuth or custom auth integration
   - For Claude Desktop, Cursor, VS Code MCP clients

### Directory Structure Philosophy

```
skill-root/
├── SKILL.md                    # Entry point - Claude reads this first
│                               # Contains path selection logic and decision helper
│
├── {path-name}/                # Each implementation path is self-contained
│   ├── quickstart.md           # Step-by-step implementation guide
│   └── templates/              # Framework-specific complete implementations
│       └── {framework}.md      # Working code with all imports, configs, patterns
│
├── reference/                  # Cross-cutting concerns (sessions, security)
└── scripts/                    # Validation utilities (Python)
```

**Key Design Pattern:** Each template file is a complete, copy-paste-ready implementation. Templates include ALL necessary code: imports, environment setup, route handlers, middleware, database models, and production deployment instructions.

## Template File Structure Pattern

Every template follows this structure:
1. **Quick Setup** - Commands to get started
2. **Project Structure** - File tree showing what files to create
3. **File-by-file implementation** - Complete code for each file with explanations
4. **Usage instructions** - How to test and run
5. **Production deployment** - Checklist and environment configuration
6. **Advanced features** - RBAC, organization access, etc.
7. **Troubleshooting** - Common issues and solutions

## When Adding New Framework Templates

### Required Template Sections
1. Quick Setup (dependencies, initial commands)
2. Project Structure (visual file tree)
3. Environment Configuration (.env file)
4. SDK Initialization (Scalekit client setup)
5. Route Handlers (login, callback, logout for Full-Stack/Modular SSO)
6. Session Management (how tokens are stored and validated)
7. Protected Route Example
8. Production Deployment Checklist
9. Testing Instructions
10. Troubleshooting Section

### Template Checklist
- [ ] Includes ALL imports and dependencies
- [ ] Shows complete file structure
- [ ] Has working environment variable configuration
- [ ] Includes security best practices (HttpOnly cookies, token validation)
- [ ] Provides production deployment instructions
- [ ] Includes error handling patterns
- [ ] Shows integration with framework-specific patterns (e.g., Next.js App Router, FastAPI routers)
- [ ] Has troubleshooting section for common issues

### Framework-Specific Patterns to Follow

**Next.js (App Router):**
- Use Route Handlers (`route.ts` files)
- Server Components for auth checks (`requireAuth()`)
- `cookies()` from `next/headers` for token storage
- Middleware for route protection

**Express:**
- Router modules for auth routes
- Express middleware for token validation
- Session middleware integration
- Standard error handling patterns

**FastAPI:**
- APIRouter for auth endpoints
- Dependency injection for auth validation
- HTTPOnly cookie responses
- Pydantic models for configuration

## Common Development Tasks

### Adding a New Framework Template

1. **Choose the implementation path** (Full-Stack, Modular SSO, or MCP)
2. **Read existing templates** in that path to understand patterns
3. **Create template file** at `{path}/templates/{framework-name}.md`
4. **Follow the template structure pattern** (see above)
5. **Update README.md** in three places:
   - Implementation path "Frameworks:" section (around line 72-75 for Modular SSO)
   - Framework Support Matrix (around line 342-349)
   - Directory Structure section (add file to tree around line 180)
   - Version History section if applicable (around line 362)

### Testing a Template

Use the validation scripts in `scripts/`:
```bash
# Validate environment configuration
python scripts/validate_env.py

# Test Scalekit API connectivity
python scripts/test_connection.py

# Interactive authentication flow test
python scripts/test_auth_flow.py
```

For comprehensive testing guidance, see `TESTING.md` which contains 20+ test scenarios.

## Installation Methods

This skill has TWO installation paths:

### 1. API/Workspace Installation (`install_skill.py`)
- Uploads skill to Anthropic API workspace
- Available to all workspace members
- Requires `ANTHROPIC_API_KEY`
- Uses `anthropic.beta.skills.create()`
- Command: `python install_skill.py`

### 2. Local Installation (`install_local.sh`)
- Copies skill to `~/.claude/skills/` or `.claude/skills/`
- For personal use with Claude Code CLI
- No API key required
- Command: `./install_local.sh`

**Important:** When updating templates, users need to reinstall the skill to get the latest version.

## Key Architectural Decisions

### Why Three Paths?

Different developers have different needs:
- **New apps** → Full-Stack (no existing auth to preserve)
- **Existing B2B SaaS** → Modular SSO (enterprise customers demand SAML/OIDC but you have working password auth)
- **MCP developers** → MCP Auth (OAuth 2.1 is required by MCP protocol)

### Why Separate Templates Per Framework?

Each framework has distinct patterns:
- Next.js App Router uses Server Components, Route Handlers, `cookies()`
- Express uses middleware chains, router modules
- FastAPI uses dependency injection, APIRouter

Combining them would create confusion. Separate templates ensure copy-paste-ready code.

### Why Complete Code in Templates?

Developers implementing auth need:
- ALL imports (not just main ones)
- Complete environment setup
- Working error handling
- Production deployment checklist

Partial code leads to "what am I missing?" questions.

## Framework Support Status

Current support matrix (as of v1.0.0):

| Framework | Full-Stack | Modular SSO | MCP OAuth | MCP Custom |
|-----------|-----------|-------------|-----------|------------|
| Node.js + Express | ✅ | ✅ | ✅ | ✅ |
| Next.js (App Router) | ✅ | ✅ | ✅ | ✅ |
| Python + FastAPI | ✅ | 🚧 | ✅ | ✅ |
| Django | 🚧 | 🚧 | 🚧 | 🚧 |
| Ruby on Rails | 🚧 | 🚧 | - | - |
| Go | 🚧 | 🚧 | ✅ | ✅ |

✅ = Available | 🚧 = Coming Soon | - = Not Applicable

When adding new framework support, update this matrix in both CLAUDE.md and README.md.

## Important Implementation Notes

### Security Patterns

All templates MUST follow these security patterns:
- **HttpOnly cookies** for access/refresh tokens
- **Token validation** on every protected request using `scalekit.validateAccessToken()`
- **Short token lifetimes** (5-60 minutes for access tokens)
- **No localStorage** for sensitive tokens
- **HTTPS in production** (`secure: true` for cookies)
- **CSRF protection** (`sameSite: 'strict'` or 'lax')

### Session Management Patterns

**Full-Stack Auth:**
- Scalekit manages sessions via tokens
- Store `accessToken`, `refreshToken`, `idToken` in HttpOnly cookies
- Refresh token when access token expires
- Validate tokens on server-side only

**Modular SSO:**
- Customer's existing session system remains unchanged
- SSO provides user profile data
- Create YOUR session after SSO callback
- No Scalekit tokens stored (one-time exchange for user info)

### Common Mistakes to Avoid

1. **Don't mix Full-Stack and Modular SSO patterns** - They have different token management approaches
2. **Don't store tokens in localStorage** - Always use HttpOnly cookies
3. **Don't skip token validation** - Always validate server-side with `validateAccessToken()`
4. **Don't forget callback URL registration** - Must match exactly in Scalekit Dashboard
5. **Don't use `secure: true` for localhost** - HTTP requires `secure: false`

## Validation Scripts

Three Python scripts in `scripts/` for testing:

**validate_env.py** - Checks environment variables are set correctly
**test_connection.py** - Tests Scalekit API connectivity
**test_auth_flow.py** - Interactive OAuth flow test

These are referenced in templates' testing sections. They require:
```bash
pip install anthropic python-dotenv
```

## File Naming Conventions

- Implementation paths: `kebab-case` (e.g., `full-stack-auth`, `modular-sso`)
- Templates: `framework-name.md` (e.g., `nodejs-express.md`, `nextjs.md`)
- For SSO variants: `framework-name-sso.md` (e.g., `nextjs-sso.md`)
- Reference docs: `kebab-case.md` (e.g., `session-management.md`)

## Version Control

When making changes that add new templates or features:
1. Update version in README.md "Version History" section
2. Update file count and line count estimates
3. Update Framework Support Matrix
4. Update Directory Structure if adding new files
5. Commit with descriptive message explaining what was added

## SKILL.md Entry Point

`SKILL.md` is the entry point that Claude reads first. It contains:
- Skill metadata (name, description)
- Decision helper to route users to correct path
- Prerequisites and validation scripts
- Common implementation steps
- Security best practices overview

**Never modify the decision helper logic** without understanding how it routes users to paths.

## Testing Philosophy

See `TESTING.md` for comprehensive testing guide. Key principle: Test that Claude **uses the skill content** rather than generic knowledge.

Validation checks:
- Does Claude mention Scalekit SDK specifically?
- Does Claude reference skill files (quickstart.md, templates)?
- Is code complete and working (not generic OAuth advice)?
- Are security best practices followed?

## Documentation Cross-References

Templates frequently reference:
- `reference/session-management.md` - Token refresh patterns, cookie configuration
- `reference/security-best-practices.md` - Production security checklist
- `scripts/validate_env.py` - Environment validation

Ensure these references remain valid when moving or renaming files.
