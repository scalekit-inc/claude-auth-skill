# Scalekit SDK Versions

This document tracks the Scalekit SDK versions used across all skill templates.

## Current SDK Versions

### Node.js SDK
- **Package:** `@scalekit-sdk/node`
- **Version:** `^2.1.6`
- **Released:** December 2025
- **Installation:** `npm install @scalekit-sdk/node@^2.1.6`
- **Documentation:** https://github.com/scalekit-inc/scalekit-sdk-node

### Python SDK
- **Package:** `scalekit-sdk-python`
- **Version:** `>=2.4.13`
- **Released:** December 2025
- **Installation:** `pip install scalekit-sdk-python>=2.4.13`
- **Documentation:** https://github.com/scalekit-inc/scalekit-sdk-python

### Java SDK
- **Status:** Not yet implemented in skill templates
- **Latest Version:** 2.0.7
- **When available:** Will be added to Full-Stack and Modular SSO paths

### Go SDK
- **Status:** Not yet implemented in skill templates
- **Latest Version:** 2.0.8
- **When available:** Will be added to Full-Stack and Modular SSO paths

## Templates Using SDKs

### Node.js SDK (v2.1.6)
- `full-stack-auth/templates/nodejs-express.md`
- `full-stack-auth/templates/nextjs.md`
- `modular-sso/templates/nodejs-express-sso.md`
- `modular-sso/templates/nextjs-sso.md`
- `mcp-auth/oauth-quickstart.md`
- `mcp-auth/custom-auth-integration.md`
- Demo app: `scalekit-nextjs-demo/`

### Python SDK (v2.4.13)
- `full-stack-auth/templates/python-fastapi.md`
- `mcp-auth/oauth-quickstart.md` (example)
- Validation scripts: `scripts/test_auth_flow.py`, `scripts/test_connection.py`

## Version Update History

### December 22, 2025
- **Node.js SDK:** Updated from 1.0.0 to 2.1.6
- **Python SDK:** Updated from 1.0.0 to 2.4.13
- **Reason:** Latest stable releases with bug fixes and improvements

## Breaking Changes

### Node.js SDK 2.x (from 1.x)

**Major changes in v2.0.0:**
- Added user CRUD methods and refresh token handling
- Added issuer, audience, and scope validation in tokens (v2.0.1)

**Breaking change in v2.1.0:**
- Renamed `sendActivationEmail` → `sendInvitationEmail`
- Added new `resendInvite` method
- **Impact on skill:** None (we don't use these methods)

**v2.1.6 (November 19, 2025):**
- Added `given_name` and `family_name` to user object schema
- **Impact on skill:** Backward compatible, no changes needed

**Conclusion:** No breaking changes affect the skill templates. All existing code patterns remain fully compatible.

### Python SDK 2.x
**Status:** Changelog not yet reviewed. Based on testing, no breaking changes affect skill templates. All existing code patterns remain compatible.

## Compatibility Notes

### Node.js SDK Requirements
- Node.js >= 16.0.0
- TypeScript >= 4.5.0 (if using TypeScript)

### Python SDK Requirements
- Python >= 3.8
- FastAPI >= 0.100.0 (for FastAPI templates)

## When to Update SDK Versions

Update SDK versions in the skill when:
1. **Security fixes** are released
2. **Critical bug fixes** are available
3. **New features** are needed by templates
4. **Breaking changes** require code updates

### Update Process
1. Check SDK release notes for breaking changes
2. Update version in all template files
3. Test demo applications
4. Update this document
5. Update CLAUDE.md if architecture changes
6. Update DEMO_APP_LEARNINGS.md if bugs are found

## SDK Documentation Links

- **Node.js:** https://docs.scalekit.com/sdk/node
- **Python:** https://docs.scalekit.com/sdk/python
- **Java:** https://docs.scalekit.com/sdk/java (when templates are added)
- **Go:** https://docs.scalekit.com/sdk/go (when templates are added)

## Future SDK Support

### Planned Additions
- **Java SDK** (v2.0.7+) - Spring Boot templates
- **Go SDK** (v2.0.8+) - Gin/Echo framework templates
- **Ruby SDK** - Rails templates (when SDK is released)
- **PHP SDK** - Laravel templates (when SDK is released)

### Template Priorities
1. Java + Spring Boot (high demand from enterprise customers)
2. Go + Gin (growing MCP server usage)
3. Ruby + Rails (community requests)
4. PHP + Laravel (community requests)

## Maintenance Notes

- SDK versions are specified using semantic versioning
- Node.js uses caret (^) ranges: `^2.1.6` allows 2.1.x and 2.x.x (but not 3.x.x)
- Python uses >= for flexibility: `>=2.4.13` allows any version 2.4.13 or higher
- Always test with exact versions before publishing updates
- Demo apps use exact versions for reproducibility

## Reporting SDK Issues

If you encounter SDK issues:
1. Check SDK GitHub issues
2. Verify skill templates are using correct API patterns
3. Test with demo applications
4. Report to Scalekit support with reproduction steps
5. Update skill templates if API patterns need correction
