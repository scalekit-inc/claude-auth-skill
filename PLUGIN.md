# Scalekit Authentication Plugin

A comprehensive Claude Code plugin for implementing Scalekit authentication across web applications, APIs, and MCP servers.

## What is This Plugin?

This plugin enhances Claude Code with expert knowledge for implementing Scalekit authentication. It provides:

- **Agent Skill** - Claude automatically uses Scalekit-specific implementation patterns
- **Custom Commands** - Quick access to implementation paths and validation
- **Complete Templates** - Copy-paste-ready code for Express, Next.js, FastAPI
- **Validation Scripts** - Test your Scalekit configuration before deploying

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
# Clone the repository
git clone https://github.com/scalekit-inc/claude-auth-skill.git
cd claude-auth-skill

# Install as a plugin
claude plugin marketplace add .
claude plugin install scalekit-auth@scalekit-marketplace
```

### Option 2: Install from Local Marketplace

If you have this plugin in a local directory:

```bash
# Navigate to the plugin directory
cd /path/to/scalekit-auth-skill

# Add as marketplace and install
claude plugin marketplace add .
claude plugin install scalekit-auth@scalekit-marketplace
```

### Verify Installation

```bash
# Check plugin is installed
claude plugin list

# Try the help command
claude
> /scalekit
```

## Available Commands

### `/scalekit` - Get Help

Shows implementation paths and helps you choose the right approach:
- Full-Stack Authentication
- Modular SSO
- MCP Server Authentication

### `/scalekit-init` - Initialize Project

Interactive setup wizard that:
1. Asks about your framework and needs
2. Creates environment configuration
3. Provides complete working code
4. Sets up validation scripts

### `/scalekit-validate` - Validate Setup

Runs validation scripts to check:
- Environment variables configured correctly
- Scalekit API connectivity
- Credentials validity

## How It Works

### Agent Skill (Automatic)

When you ask Claude about Scalekit authentication, the plugin's skill automatically activates:

```
You: "Help me add Scalekit auth to my Express app"

Claude: [Uses the scalekit-auth skill automatically]
        I'll help you implement Scalekit authentication in Express...
        [Provides complete, Scalekit-specific code]
```

The skill contains:
- Complete implementation templates for 3 frameworks
- Security best practices
- Token management patterns
- Production deployment checklists

### Commands (Manual)

Use commands for quick access to specific workflows:

```bash
# Get help choosing implementation path
/scalekit

# Initialize a new project
/scalekit-init

# Validate configuration
/scalekit-validate
```

## Implementation Paths

### 1. Full-Stack Authentication

**Use when:** Building a new app or replacing existing auth

**What you get:**
- Complete login/signup/logout flows
- Session management with tokens
- Social login (Google, GitHub, Microsoft)
- Enterprise SSO (SAML/OIDC)

**Frameworks:** Express, Next.js, FastAPI

**Quick start:**
```
You: "I need full-stack authentication for my Next.js app"
Claude: [Provides complete Next.js implementation]
```

### 2. Modular SSO

**Use when:** Adding Enterprise SSO to existing authentication

**What you get:**
- SAML/OIDC protocol handling
- Integration with Auth0, Firebase, AWS Cognito
- Keep existing sessions and user database
- Self-service customer portal

**Frameworks:** Express, Next.js

**Quick start:**
```
You: "Add SAML SSO to my existing Express auth"
Claude: [Provides Modular SSO integration]
```

### 3. MCP Server Authentication

**Use when:** Building MCP servers for Claude Desktop, Cursor, VS Code

**What you get:**
- OAuth 2.1 implementation
- Token validation middleware
- Scope-based permissions
- Discovery endpoints

**Frameworks:** Express, Next.js, FastAPI, Go

**Quick start:**
```
You: "Secure my MCP server with OAuth 2.1"
Claude: [Provides MCP authentication implementation]
```

## Plugin Structure

```
scalekit-auth-plugin/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata
│   └── marketplace.json     # Marketplace configuration
├── commands/
│   ├── scalekit.md          # Help command
│   ├── scalekit-init.md     # Init wizard
│   └── scalekit-validate.md # Validation command
└── skills/
    └── scalekit-auth/
        ├── SKILL.md         # Main skill entry point
        ├── full-stack-auth/ # Full-Stack templates
        ├── modular-sso/     # Modular SSO templates
        ├── mcp-auth/        # MCP authentication
        ├── reference/       # Reference docs
        └── scripts/         # Validation scripts
```

## Example Usage

### Example 1: Full-Stack Auth in Next.js

```bash
claude
> "I need to add authentication to my Next.js app using Scalekit"

# Claude will:
# 1. Detect you need Full-Stack Authentication
# 2. Provide complete Next.js App Router implementation
# 3. Include all files: routes, middleware, auth helpers
# 4. Give you environment setup and deployment checklist
```

### Example 2: Add SSO to Existing App

```bash
claude
> "I have password-based auth but enterprise customers need SAML"

# Claude will:
# 1. Suggest Modular SSO approach
# 2. Show how to integrate with your existing auth
# 3. Provide SSO routes that coexist with password auth
# 4. Include admin portal for customer SSO setup
```

### Example 3: Using Commands

```bash
claude
> /scalekit

# Shows implementation paths and decision helper

> /scalekit-init

# Interactive wizard:
# - What framework? → Next.js
# - What path? → Full-Stack Auth
# - Have credentials? → Yes
# → Generates complete setup
```

## Validation Scripts

The plugin includes Python validation scripts:

```bash
# Navigate to plugin skills directory
cd ~/.claude/plugins/scalekit-auth/skills/scalekit-auth

# Validate environment variables
python scripts/validate_env.py

# Test Scalekit API connectivity
python scripts/test_connection.py

# Interactive auth flow test
python scripts/test_auth_flow.py
```

**Requirements:**
```bash
pip install anthropic python-dotenv
```

## Framework Support

| Framework | Full-Stack | Modular SSO | MCP OAuth |
|-----------|-----------|-------------|-----------|
| Node.js + Express | ✅ | ✅ | ✅ |
| Next.js (App Router) | ✅ | ✅ | ✅ |
| Python + FastAPI | ✅ | 🚧 | ✅ |
| Django | 🚧 | 🚧 | 🚧 |
| Go | 🚧 | 🚧 | ✅ |

✅ Available | 🚧 Coming Soon

## Plugin Management

### Enable/Disable

```bash
# Disable plugin temporarily
claude plugin disable scalekit-auth@scalekit-marketplace

# Re-enable
claude plugin enable scalekit-auth@scalekit-marketplace
```

### Update Plugin

```bash
# Pull latest changes
cd /path/to/scalekit-auth-skill
git pull origin main

# Plugin will use latest version automatically
```

### Uninstall

```bash
claude plugin uninstall scalekit-auth@scalekit-marketplace
```

## Troubleshooting

### Plugin Not Found

```bash
# Ensure marketplace is added
claude plugin marketplace list

# Re-add marketplace
claude plugin marketplace add /path/to/scalekit-auth-skill
```

### Skill Not Activating

Try being more explicit:
```
# Instead of: "Help me with authentication"
# Try: "Help me implement Scalekit authentication in Express"
```

### Commands Not Working

```bash
# Check plugin is enabled
claude plugin list

# Verify plugin is installed
claude plugin install scalekit-auth@scalekit-marketplace
```

## Documentation

- **Plugin Guide**: This file
- **Comprehensive README**: [README.md](README.md)
- **Testing Guide**: [TESTING.md](TESTING.md)
- **Architecture**: [CLAUDE.md](CLAUDE.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)

## Support

- **GitHub**: https://github.com/scalekit-inc/claude-auth-skill
- **Issues**: https://github.com/scalekit-inc/claude-auth-skill/issues
- **Email**: support@scalekit.com
- **Docs**: https://docs.scalekit.com

## Contributing

To contribute to this plugin:

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test with Claude Code
5. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for architecture and development guidelines.

## License

MIT License - See repository for details

---

Built with ❤️ by Scalekit
