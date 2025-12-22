# FastMCP + Scalekit OAuth Authentication

Complete guide for building a production-ready FastMCP server protected by Scalekit's OAuth 2.1 authentication with scope-based authorization.

## Overview

FastMCP is a Python framework for building Model Context Protocol (MCP) servers. This template shows how to integrate Scalekit's built-in OAuth authentication provider for FastMCP, enabling secure access control with scope-based permissions.

**Use this when:**
- Building a new MCP server in Python
- Need OAuth 2.1 compliance with minimal code
- Want automatic token validation and scope enforcement
- Building servers for Claude Desktop, Cursor, or VS Code

**Time to implement:** 30-45 minutes

**Key Features:**
- Built-in Scalekit OAuth provider for FastMCP
- Automatic token validation on every request
- Scope-based authorization for tools
- Dynamic Client Registration (DCR) support
- HttpOnly cookie session management

---

## Quick Setup

```bash
# Create project directory
mkdir fastmcp-scalekit-server
cd fastmcp-scalekit-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install "fastmcp>=2.13.0.2" python-dotenv
```

---

## Project Structure

```
fastmcp-scalekit-server/
├── .env                    # Environment configuration (DO NOT COMMIT)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── server.py               # Main FastMCP server with Scalekit auth
└── README.md              # Project documentation
```

---

## Step 1: Environment Configuration

### .env.example

Create this template file for sharing with your team:

```bash
# Server Configuration
PORT=3002

# Scalekit Configuration
SCALEKIT_ENVIRONMENT_URL=https://your-environment-url.scalekit.com
SCALEKIT_CLIENT_ID=skc_your_client_id
SCALEKIT_RESOURCE_ID=res_your_resource_id

# MCP Server URL (must match Scalekit Dashboard registration)
MCP_URL=http://localhost:3002/
```

### .env

Copy `.env.example` to `.env` and fill in your actual values:

```bash
cp .env.example .env
```

**Where to find these values:**

1. **SCALEKIT_ENVIRONMENT_URL** & **SCALEKIT_CLIENT_ID**:
   - Dashboard → Settings → API Credentials

2. **SCALEKIT_RESOURCE_ID**:
   - Dashboard → MCP Servers → Your Server → Resource ID (starts with `res_`)

3. **MCP_URL**:
   - Your server's public URL with trailing slash
   - Development: `http://localhost:3002/`
   - Production: `https://mcp.yourapp.com/`

**Security Warning:** Never commit `.env` to version control. Add it to `.gitignore`.

---

## Step 2: Register MCP Server in Scalekit Dashboard

Before implementing your server, register it in the Scalekit Dashboard:

1. **Navigate to:** Dashboard → MCP Servers → Add MCP Server

2. **Configure Server:**
   - **Name:** FastMCP Todo Server (or your server name)
   - **Server URL:** `http://localhost:3002/` (must include trailing slash)
   - ✅ Enable **Dynamic Client Registration (DCR)**
   - ✅ Enable **Client-Initiated Metadata Document (CIMD)**

3. **Configure Token Lifetime:**
   - **Access Token:** 300-3600 seconds (5-60 minutes recommended)
   - **Refresh Token:** Optional (enable for longer sessions)

4. **Define Scopes:**

   Add scopes for your server's operations:
   - `todo:read` - Read access to todo items
   - `todo:write` - Create, update, or delete todo items

   You can add more scopes based on your use case.

5. **Save and Copy:**
   - Copy the **Resource ID** (starts with `res_`)
   - Copy the **Metadata JSON** (optional, for manual client setup)

---

## Step 3: Dependencies

### requirements.txt

```
fastmcp>=2.13.0.2
python-dotenv>=1.0.0
```

**Install:**
```bash
pip install -r requirements.txt
```

**Version Notes:**
- FastMCP 2.13.0.2+ includes the `ScalekitProvider` for OAuth
- `python-dotenv` loads environment variables from `.env`

---

## Step 4: Implement FastMCP Server with Scalekit Auth

### server.py

```python
"""Scalekit-authenticated FastMCP server with in-memory CRUD tools.

Demonstrates OAuth scope validation protecting all tool operations.
"""

import os
import uuid
from dataclasses import dataclass, asdict
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.scalekit import ScalekitProvider
from fastmcp.server.dependencies import AccessToken, get_access_token

# Load environment variables from .env
load_dotenv()

# Initialize FastMCP with Scalekit OAuth protection
mcp = FastMCP(
    "Todo Server",  # Server name shown in MCP clients
    stateless_http=True,  # Required for OAuth with MCP
    auth=ScalekitProvider(
        environment_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
        client_id=os.getenv("SCALEKIT_CLIENT_ID"),
        resource_id=os.getenv("SCALEKIT_RESOURCE_ID"),
        mcp_url=os.getenv("MCP_URL"),
    ),
)


@dataclass
class TodoItem:
    """Todo item data model."""
    id: str
    title: str
    description: Optional[str]
    completed: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# In-memory storage (replace with database for production)
_TODO_STORE: dict[str, TodoItem] = {}


def _require_scope(scope: str) -> Optional[str]:
    """Validate required scope in current request token.

    Args:
        scope: The required scope (e.g., 'todo:read')

    Returns:
        Error message if scope is missing, None if authorized
    """
    token: AccessToken = get_access_token()
    if scope not in token.scopes:
        return f"Insufficient permissions: `{scope}` scope required."
    return None


@mcp.tool
def create_todo(title: str, description: Optional[str] = None) -> dict:
    """Create a new todo item.

    Requires: todo:write scope

    Args:
        title: Todo title (required)
        description: Optional description

    Returns:
        Created todo item or error message
    """
    error = _require_scope("todo:write")
    if error:
        return {"error": error}

    todo = TodoItem(
        id=str(uuid.uuid4()),
        title=title,
        description=description
    )
    _TODO_STORE[todo.id] = todo
    return {"todo": todo.to_dict()}


@mcp.tool
def list_todos(completed: Optional[bool] = None) -> dict:
    """Retrieve all todos, optionally filtered by completion status.

    Requires: todo:read scope

    Args:
        completed: Filter by completion status (None = all todos)

    Returns:
        List of todo items or error message
    """
    error = _require_scope("todo:read")
    if error:
        return {"error": error}

    todos = [
        todo.to_dict()
        for todo in _TODO_STORE.values()
        if completed is None or todo.completed == completed
    ]
    return {"todos": todos}


@mcp.tool
def get_todo(todo_id: str) -> dict:
    """Retrieve a specific todo by ID.

    Requires: todo:read scope

    Args:
        todo_id: The todo item ID

    Returns:
        Todo item or error message
    """
    error = _require_scope("todo:read")
    if error:
        return {"error": error}

    todo = _TODO_STORE.get(todo_id)
    if todo is None:
        return {"error": f"Todo `{todo_id}` not found."}

    return {"todo": todo.to_dict()}


@mcp.tool
def update_todo(
    todo_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> dict:
    """Update todo properties or mark as complete/incomplete.

    Requires: todo:write scope

    Args:
        todo_id: The todo item ID
        title: New title (optional)
        description: New description (optional)
        completed: New completion status (optional)

    Returns:
        Updated todo item or error message
    """
    error = _require_scope("todo:write")
    if error:
        return {"error": error}

    todo = _TODO_STORE.get(todo_id)
    if todo is None:
        return {"error": f"Todo `{todo_id}` not found."}

    # Update only provided fields
    if title is not None:
        todo.title = title
    if description is not None:
        todo.description = description
    if completed is not None:
        todo.completed = completed

    return {"todo": todo.to_dict()}


@mcp.tool
def delete_todo(todo_id: str) -> dict:
    """Remove a todo item from the system.

    Requires: todo:write scope

    Args:
        todo_id: The todo item ID

    Returns:
        Deleted todo ID or error message
    """
    error = _require_scope("todo:write")
    if error:
        return {"error": error}

    todo = _TODO_STORE.pop(todo_id, None)
    if todo is None:
        return {"error": f"Todo `{todo_id}` not found."}

    return {"deleted": todo_id}


if __name__ == "__main__":
    # Run server with HTTP transport on configured port
    mcp.run(
        transport="http",
        port=int(os.getenv("PORT", "3002"))
    )
```

---

## Step 5: Run the Server

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run server
python server.py
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3002 (Press CTRL+C to quit)
```

Your server is now listening at `http://localhost:3002/` and ready to validate Scalekit OAuth tokens.

---

## Step 6: Testing with MCP Inspector

The MCP Inspector is the easiest way to test your server's authentication flow.

### Install and Run

```bash
npx @modelcontextprotocol/inspector@latest
```

### Connect to Your Server

1. **Server URL:** `http://localhost:3002/mcp`
2. **Authentication:** Leave empty (DCR handles this automatically)
3. Click **Connect**

The Inspector will:
- Discover OAuth metadata from your server
- Register a client via Dynamic Client Registration
- Complete the OAuth flow in your browser
- Connect with a valid access token

### Test Scope Enforcement

**Test 1: Read Operations (requires `todo:read`)**

1. Call `list_todos` tool
2. Should succeed if you have `todo:read` scope
3. Should fail with "Insufficient permissions" if scope is missing

**Test 2: Write Operations (requires `todo:write`)**

1. Call `create_todo` tool with title: "Test Task"
2. Should succeed if you have `todo:write` scope
3. Should fail if you only have `todo:read` scope

**Test 3: Scope Isolation**

1. Revoke `todo:write` scope in Scalekit Dashboard
2. Try `create_todo` again
3. Should return error: "Insufficient permissions: `todo:write` scope required"

---

## Authentication Flow Explained

```
MCP Client (Inspector)      FastMCP Server              Scalekit OAuth
      |                           |                            |
      |--- (1) Connect to /mcp -->|                            |
      |                           |                            |
      |<-- (2) 401 + metadata ----|                            |
      |                           |                            |
      |--- (3) Register client (DCR) ----------------------->  |
      |<-- (4) Client credentials --------------------------|  |
      |                           |                            |
      |--- (5) Start OAuth flow ----------------------------->  |
      |                           |                            |
      |                           |      (6) User authenticates |
      |                           |                            |
      |<-- (7) Authorization code -----------------------------|
      |                           |                            |
      |--- (8) Exchange code ----------------------------------→|
      |<-- (9) Access token + refresh token ------------------|  |
      |                           |                            |
      |--- (10) Call tool + Bearer token -->                   |
      |                           |                            |
      |                           |--- (11) Validate token --->|
      |                           |<-- (12) Token valid -------|
      |                           |                            |
      |                           | (13) Check scope           |
      |                           |                            |
      |<-- (14) Tool result ------|                            |
```

**Key Points:**
- **Step 2:** Server returns OAuth metadata and WWW-Authenticate header
- **Step 3-4:** Dynamic Client Registration creates client on-the-fly
- **Step 11-12:** Every tool call validates the token with Scalekit
- **Step 13:** Scope enforcement happens in `_require_scope()` helper

---

## Production Deployment

### Deployment Checklist

- [ ] **Environment Variables:** Set all required vars in production environment
- [ ] **HTTPS Required:** MCP_URL must use HTTPS in production
- [ ] **Update Scalekit Dashboard:** Change Server URL to production domain
- [ ] **Database:** Replace in-memory `_TODO_STORE` with persistent storage
- [ ] **Logging:** Add structured logging for auth failures and tool calls
- [ ] **Rate Limiting:** Implement rate limits on tool endpoints
- [ ] **Monitoring:** Track token validation failures and scope denials
- [ ] **Secret Management:** Use secrets manager (AWS Secrets, GCP Secret Manager, etc.)

### Production Environment Variables

```bash
# Production .env
PORT=443
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_prod_...
SCALEKIT_RESOURCE_ID=res_prod_...
MCP_URL=https://mcp.yourapp.com/

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Logging
LOG_LEVEL=INFO
```

### Recommended Hosting

**Deployment Options:**
- **Railway:** Easiest Python deployment with auto-HTTPS
- **Heroku:** Built-in HTTPS, simple git push deployment
- **Google Cloud Run:** Serverless Python containers
- **AWS Lambda + API Gateway:** Serverless with custom domain
- **DigitalOcean App Platform:** Simple container deployment

**HTTPS Requirement:**
- OAuth 2.1 requires HTTPS in production
- All hosting options above provide automatic HTTPS
- Update `MCP_URL` in `.env` and Scalekit Dashboard after deployment

### Database Integration

Replace the in-memory store with a database:

**PostgreSQL with SQLAlchemy:**

```python
from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class TodoItem(Base):
    __tablename__ = "todos"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(engine)

# In your tools, use:
# session = Session()
# todo = session.query(TodoItem).filter_by(id=todo_id).first()
```

---

## Advanced Features

### Custom Scopes for Different Operations

Define granular scopes for fine-grained access control:

```python
# In Scalekit Dashboard, create scopes:
# - todo:read
# - todo:write
# - todo:delete
# - todo:admin (for bulk operations)

@mcp.tool
def bulk_delete_todos() -> dict:
    """Delete all completed todos. Requires admin scope."""
    error = _require_scope("todo:admin")
    if error:
        return {"error": error}

    deleted_ids = [
        todo_id for todo_id, todo in _TODO_STORE.items()
        if todo.completed
    ]

    for todo_id in deleted_ids:
        del _TODO_STORE[todo_id]

    return {"deleted_count": len(deleted_ids)}
```

### Multi-Scope Requirements

Require multiple scopes for a single operation:

```python
def _require_scopes(*scopes: str) -> Optional[str]:
    """Validate multiple required scopes."""
    token: AccessToken = get_access_token()
    missing = [s for s in scopes if s not in token.scopes]

    if missing:
        return f"Missing scopes: {', '.join(missing)}"
    return None

@mcp.tool
def export_all_todos() -> dict:
    """Export all todos (requires both read and admin scopes)."""
    error = _require_scopes("todo:read", "todo:admin")
    if error:
        return {"error": error}

    # Export logic here...
    return {"todos": [t.to_dict() for t in _TODO_STORE.values()]}
```

### Token Introspection

Access token claims for logging or authorization:

```python
@mcp.tool
def get_user_info() -> dict:
    """Get current user information from token."""
    token: AccessToken = get_access_token()

    return {
        "user_id": token.sub,  # Subject (user ID)
        "scopes": token.scopes,
        "expires_at": token.exp,
        "client_id": token.client_id
    }
```

---

## Security Best Practices

### 1. Always Validate Scopes

```python
# ✅ GOOD: Validate before every operation
@mcp.tool
def sensitive_operation() -> dict:
    error = _require_scope("admin:write")
    if error:
        return {"error": error}
    # ... safe to proceed

# ❌ BAD: Assuming token presence means authorization
@mcp.tool
def sensitive_operation() -> dict:
    # Anyone with ANY valid token can call this!
    return {"data": "sensitive"}
```

### 2. Principle of Least Privilege

Define narrow scopes for specific operations:

```python
# ✅ GOOD: Granular scopes
# todo:read, todo:write, todo:delete, todo:share

# ❌ BAD: Single "admin" scope for everything
```

### 3. Never Log Tokens

```python
# ✅ GOOD: Log actions without token
logging.info(f"User {token.sub} created todo {todo_id}")

# ❌ BAD: Logging sensitive data
logging.info(f"Token: {request.headers['Authorization']}")
```

### 4. Validate Token on Every Request

The `ScalekitProvider` automatically validates tokens, but ensure you're checking scopes:

```python
# ✅ GOOD: Scope check in every tool
@mcp.tool
def every_tool():
    error = _require_scope("necessary:scope")
    if error:
        return {"error": error}

# ❌ BAD: Skipping validation
@mcp.tool
def unprotected_tool():
    return {"data": "anyone can access"}
```

### 5. Use HTTPS in Production

```bash
# ✅ GOOD: Production MCP_URL
MCP_URL=https://mcp.yourapp.com/

# ❌ BAD: HTTP in production
MCP_URL=http://mcp.yourapp.com/  # Tokens transmitted in plaintext!
```

---

## Troubleshooting

### Error: "401 Unauthorized" when connecting

**Cause:** Client cannot authenticate with Scalekit.

**Solutions:**
1. Verify `SCALEKIT_ENVIRONMENT_URL` matches Dashboard → Settings
2. Verify `SCALEKIT_CLIENT_ID` matches Dashboard → Settings
3. Ensure `SCALEKIT_RESOURCE_ID` matches the MCP Server registration
4. Check server URL in Dashboard matches `MCP_URL` exactly (including trailing slash)

### Error: "Insufficient permissions: `todo:write` scope required"

**Cause:** Token missing required scope.

**Solutions:**
1. Check scopes defined in Scalekit Dashboard → MCP Servers → Your Server
2. Verify scope names match exactly (case-sensitive)
3. Re-authenticate to get token with new scopes

### Error: "Module not found: ScalekitProvider"

**Cause:** FastMCP version too old.

**Solution:**
```bash
pip install --upgrade "fastmcp>=2.13.0.2"
```

### Server starts but MCP Inspector can't connect

**Cause:** Port conflict or network issue.

**Solutions:**
1. Check if port 3002 is already in use: `lsof -i :3002`
2. Change `PORT` in `.env` to different port (e.g., 3003)
3. Update MCP Inspector URL to match new port
4. Ensure no firewall blocking localhost connections

### Dynamic Client Registration fails

**Cause:** DCR not enabled in Scalekit Dashboard.

**Solutions:**
1. Go to Dashboard → MCP Servers → Your Server
2. Ensure ✅ **Dynamic Client Registration (DCR)** is checked
3. Save and retry connection

---

## Comparison with Other MCP Auth Methods

| Feature | FastMCP + Scalekit | Manual OAuth Implementation |
|---------|-------------------|---------------------------|
| **Setup Time** | 30 minutes | 4-6 hours |
| **Code Required** | ~100 lines | 400+ lines |
| **Token Validation** | Automatic | Manual |
| **Scope Enforcement** | Helper function | Custom middleware |
| **DCR Support** | Built-in | Must implement |
| **Token Refresh** | Automatic | Manual |
| **Production Ready** | Yes | Requires testing |

---

## Next Steps

1. **Add More Tools:** Extend with additional MCP tools for your use case
2. **Connect Database:** Replace in-memory storage with PostgreSQL/MongoDB
3. **Add Resources:** Expose resources (not just tools) via FastMCP
4. **Implement Prompts:** Add dynamic prompts for Claude to use
5. **Multi-tenancy:** Use token claims to isolate data per organization

---

## Reference Documentation

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Scalekit MCP OAuth Guide](https://docs.scalekit.com/authenticate/mcp/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [OAuth 2.1 Specification](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-09)

---

## Support

**Issues with this template:**
- Check [Troubleshooting](#troubleshooting) section above
- Review [Security Best Practices](#security-best-practices)
- Test with [MCP Inspector](#step-6-testing-with-mcp-inspector)

**Scalekit Dashboard:**
- [Dashboard Login](https://app.scalekit.com)
- [API Documentation](https://docs.scalekit.com)
- [Support](https://support.scalekit.com)

**FastMCP Issues:**
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Community Discord](https://discord.gg/modelcontextprotocol)
