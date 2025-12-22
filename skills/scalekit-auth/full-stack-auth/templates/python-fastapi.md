# Python + FastAPI Template

Complete authentication implementation for FastAPI applications.

## Quick Setup

```bash
# 1. Create project directory
mkdir my-fastapi-app
cd my-fastapi-app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install fastapi uvicorn scalekit-sdk-python python-dotenv python-multipart

# 4. Create the files below
# 5. Set up .env file
# 6. Run: uvicorn app:app --reload
```

## Project Structure

```
my-fastapi-app/
├── .env
├── app.py
├── lib/
│   ├── __init__.py
│   └── scalekit.py
├── middleware/
│   ├── __init__.py
│   └── auth.py
└── requirements.txt
```

## File 1: requirements.txt

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
scalekit-sdk-python>=2.4.13
python-dotenv==1.0.0
python-multipart==0.0.6
jinja2==3.1.3
```

## File 2: .env

```bash
# Scalekit credentials (from Dashboard → Settings)
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_12345...
SCALEKIT_CLIENT_SECRET=test_12345...

# Application URLs
APP_URL=http://localhost:8000
CALLBACK_URL=http://localhost:8000/auth/callback
POST_LOGOUT_URL=http://localhost:8000

# Cookie settings
COOKIE_SECURE=false  # Set to true in production with HTTPS
```

## File 3: lib/scalekit.py

```python
from scalekit import ScalekitClient
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Scalekit client
scalekit = ScalekitClient(
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET")
)

# Application URLs
CALLBACK_URL = os.getenv("CALLBACK_URL")
POST_LOGOUT_URL = os.getenv("POST_LOGOUT_URL")

# Cookie configuration
COOKIE_CONFIG = {
    "httponly": True,
    "secure": os.getenv("COOKIE_SECURE", "false").lower() == "true",
    "samesite": "strict",
    "path": "/"
}
```

## File 4: middleware/auth.py

```python
from fastapi import Request, HTTPException, Response
from lib.scalekit import scalekit, COOKIE_CONFIG
from scalekit.common.scalekit import TokenValidationOptions
from typing import Optional
import json

async def get_current_user(request: Request, response: Response) -> dict:
    """
    Get current authenticated user with automatic token refresh.
    Raises HTTPException if user is not authenticated.
    """
    access_token = request.cookies.get("accessToken")

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Validate access token
        claims = scalekit.validate_access_token(access_token)
        return claims
    except Exception as validation_error:
        # Token expired or invalid, try to refresh
        refresh_token = request.cookies.get("refreshToken")

        if not refresh_token:
            raise HTTPException(
                status_code=401,
                detail="Session expired",
                headers={"WWW-Authenticate": "Bearer"}
            )

        try:
            # Refresh tokens
            result = scalekit.refresh_access_token(refresh_token)

            # Update cookies
            response.set_cookie(
                key="accessToken",
                value=result.access_token,
                max_age=result.expires_in,
                **COOKIE_CONFIG
            )

            if result.refresh_token:
                response.set_cookie(
                    key="refreshToken",
                    value=result.refresh_token,
                    max_age=30 * 24 * 60 * 60,  # 30 days
                    **COOKIE_CONFIG
                )

            # Validate new token
            claims = scalekit.validate_access_token(result.access_token)
            return claims
        except Exception as refresh_error:
            # Clear cookies
            response.delete_cookie("accessToken")
            response.delete_cookie("refreshToken")
            response.delete_cookie("idToken")
            response.delete_cookie("user")

            raise HTTPException(
                status_code=401,
                detail="Session expired",
                headers={"WWW-Authenticate": "Bearer"}
            )


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Get current user if authenticated, return None otherwise.
    Does not raise exceptions.
    """
    access_token = request.cookies.get("accessToken")

    if not access_token:
        return None

    try:
        claims = scalekit.validate_access_token(access_token)
        return claims
    except:
        return None


def require_role(required_role: str):
    """
    Dependency that requires a specific role.
    """
    async def check_role(request: Request, response: Response):
        user = await get_current_user(request, response)
        roles = user.get("roles", [])

        if required_role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Required role: {required_role}"
            )

        return user

    return check_role
```

## File 5: app.py

```python
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from lib.scalekit import scalekit, CALLBACK_URL, POST_LOGOUT_URL, COOKIE_CONFIG
from middleware.auth import get_current_user, get_current_user_optional, require_role
import json
import os

app = FastAPI(title="Scalekit Auth Demo")

# ============================================================================
# HTML Templates (for demo purposes)
# ============================================================================

HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Scalekit Auth Demo</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }}
        .button {{
            background: #0070f3;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
        }}
        .button:hover {{
            background: #0051cc;
        }}
        .user-info {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>Scalekit Authentication Demo</h1>
    {content}
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Scalekit Auth</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }}
        .button {{
            background: #0070f3;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
        }}
        .card {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        pre {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <h1>Dashboard</h1>
    {content}
    <a href="/" class="button">Home</a>
    <a href="/auth/logout" class="button">Logout</a>
</body>
</html>
"""

# ============================================================================
# Public Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    user_cookie = request.cookies.get("user")
    user = json.loads(user_cookie) if user_cookie else None

    if user:
        content = f"""
        <div class="user-info">
            <h2>Welcome, {user.get('email', 'User')}!</h2>
            <p><strong>User ID:</strong> {user.get('sub', 'N/A')}</p>
            <p><strong>Email:</strong> {user.get('email', 'N/A')}</p>
            <p><strong>Email Verified:</strong> {'Yes' if user.get('email_verified') else 'No'}</p>
        </div>
        <a href="/dashboard" class="button">Go to Dashboard</a>
        <a href="/auth/logout" class="button">Logout</a>
        """
    else:
        content = """
        <p>You are not logged in.</p>
        <a href="/auth/login" class="button">Sign In</a>
        """

    return HOME_TEMPLATE.format(content=content)

# ============================================================================
# Authentication Routes
# ============================================================================

@app.get("/auth/login")
async def login():
    """Initiate login flow"""
    try:
        authorization_url = scalekit.get_authorization_url(
            redirect_uri=CALLBACK_URL,
            options={
                "scopes": ["openid", "profile", "email", "offline_access"]
            }
        )
        return RedirectResponse(url=authorization_url)
    except Exception as error:
        print(f"Login error: {error}")
        return JSONResponse(
            content={"error": "Failed to initiate login"},
            status_code=500
        )


@app.get("/auth/callback")
async def callback(request: Request, code: str = None, error: str = None, error_description: str = None):
    """Handle OAuth callback"""
    # Handle OAuth errors
    if error:
        print(f"OAuth error: {error} - {error_description}")
        return RedirectResponse(
            url=f"/?error={error_description or error}"
        )

    if not code:
        return JSONResponse(
            content={"error": "Authorization code missing"},
            status_code=400
        )

    try:
        # Exchange code for tokens
        result = scalekit.authenticate_with_code(
            code=code,
            redirect_uri=CALLBACK_URL
        )

        # Extract tokens
        access_token = result.access_token
        refresh_token = result.refresh_token
        id_token = result.id_token
        user = result.user
        expires_in = result.expires_in

        # Create redirect response
        response = RedirectResponse(url="/dashboard", status_code=302)

        # Set cookies
        response.set_cookie(
            key="accessToken",
            value=access_token,
            max_age=expires_in,
            **COOKIE_CONFIG
        )

        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            max_age=30 * 24 * 60 * 60,  # 30 days
            **COOKIE_CONFIG
        )

        response.set_cookie(
            key="idToken",
            value=id_token,
            max_age=expires_in,
            **COOKIE_CONFIG
        )

        # Store user info (not httpOnly so frontend can access)
        response.set_cookie(
            key="user",
            value=json.dumps(user.__dict__),
            max_age=expires_in,
            secure=COOKIE_CONFIG["secure"],
            samesite=COOKIE_CONFIG["samesite"],
            path="/"
        )

        print(f"User authenticated: {user.email}")

        return response

    except Exception as error:
        print(f"Authentication error: {error}")
        return RedirectResponse(url="/?error=Authentication%20failed")


@app.get("/auth/logout")
async def logout(request: Request):
    """Logout user"""
    try:
        id_token = request.cookies.get("idToken")

        # Generate Scalekit logout URL
        logout_url = scalekit.get_logout_url(
            id_token_hint=id_token,
            post_logout_redirect_uri=POST_LOGOUT_URL
        )

        # Create redirect and clear cookies
        response = RedirectResponse(url=logout_url)
        response.delete_cookie("accessToken")
        response.delete_cookie("refreshToken")
        response.delete_cookie("idToken")
        response.delete_cookie("user")

        return response

    except Exception as error:
        print(f"Logout error: {error}")
        return RedirectResponse(url="/")

# ============================================================================
# Protected Routes (HTML)
# ============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, response: Response, user=Depends(get_current_user)):
    """Protected dashboard page"""
    user_cookie = request.cookies.get("user")
    user_data = json.loads(user_cookie) if user_cookie else {}

    content = f"""
    <div class="card">
        <h2>User Information</h2>
        <pre>{json.dumps(user_data, indent=2)}</pre>
    </div>
    <div class="card">
        <h2>Token Claims</h2>
        <pre>{json.dumps(user, indent=2, default=str)}</pre>
    </div>
    """

    return DASHBOARD_TEMPLATE.format(content=content)

# ============================================================================
# Protected API Routes
# ============================================================================

@app.get("/api/me")
async def get_me(request: Request, response: Response, claims=Depends(get_current_user)):
    """Get current user info"""
    user_cookie = request.cookies.get("user")
    user = json.loads(user_cookie) if user_cookie else None

    return {
        "user": user,
        "claims": claims
    }


@app.get("/api/profile")
async def get_profile(request: Request, response: Response, user=Depends(get_current_user)):
    """Example protected API endpoint"""
    return {
        "message": "This is a protected endpoint",
        "user": user
    }


@app.get("/api/admin")
async def admin_endpoint(user=Depends(require_role("admin"))):
    """Admin-only endpoint"""
    return {
        "message": "Admin endpoint accessed successfully",
        "user": user
    }

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print(f"""
🚀 Server starting...

Routes:
  Home:      http://localhost:8000/
  Login:     http://localhost:8000/auth/login
  Dashboard: http://localhost:8000/dashboard (protected)
  API:       http://localhost:8000/api/me (protected)
  Docs:      http://localhost:8000/docs

Environment:
  Scalekit URL: {os.getenv('SCALEKIT_ENVIRONMENT_URL')}
  Callback URL: {CALLBACK_URL}
    """)

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )
```

## Usage

### 1. Set up environment

Create `.env` file with your Scalekit credentials.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the server

```bash
uvicorn app:app --reload
```

Or for production:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 4. Test the flow

1. Visit http://localhost:8000
2. Click "Sign In"
3. Complete authentication
4. You'll be redirected to the dashboard
5. Test protected routes
6. Click "Logout"

## API Documentation

FastAPI provides automatic API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Using with Frontend Frameworks

### CORS Configuration

For React, Vue, or other frontend apps:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Example Frontend Request

```javascript
// Fetch user data
fetch('http://localhost:8000/api/me', {
  credentials: 'include'  // Important: include cookies
})
  .then(res => res.json())
  .then(data => console.log(data.user));
```

## Advanced Features

### Custom User Model

```python
from pydantic import BaseModel

class User(BaseModel):
    sub: str
    email: str
    email_verified: bool
    name: Optional[str] = None
    roles: list[str] = []

async def get_typed_user(request: Request, response: Response) -> User:
    claims = await get_current_user(request, response)
    return User(**claims)
```

### Scope-Based Authorization

```python
def require_scope(required_scope: str):
    """Dependency that requires a specific scope"""
    async def check_scope(request: Request, response: Response):
        user = await get_current_user(request, response)
        scopes = user.get("scope", "").split()

        if required_scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Required scope: {required_scope}"
            )

        return user

    return check_scope

# Usage
@app.get("/api/write")
async def write_data(user=Depends(require_scope("write"))):
    return {"message": "Write access granted"}
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def send_welcome_email(email: str):
    print(f"Sending welcome email to {email}")
    # Email sending logic here

@app.get("/auth/callback")
async def callback(background_tasks: BackgroundTasks, ...):
    # ... authentication logic ...

    # Add background task
    background_tasks.add_task(send_welcome_email, user.email)

    return response
```

## Production Deployment

### Environment Variables

```bash
SCALEKIT_ENVIRONMENT_URL=https://prod-env.scalekit.com
SCALEKIT_CLIENT_ID=skc_prod_...
SCALEKIT_CLIENT_SECRET=prod_...

APP_URL=https://yourapp.com
CALLBACK_URL=https://yourapp.com/auth/callback
POST_LOGOUT_URL=https://yourapp.com

COOKIE_SECURE=true
```

### Using Gunicorn

```bash
pip install gunicorn

# Run with multiple workers
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
docker build -t scalekit-auth .
docker run -p 8000:8000 --env-file .env scalekit-auth
```

### Deploy Checklist

- [ ] Set `COOKIE_SECURE=true`
- [ ] Use HTTPS
- [ ] Register production callback URLs in Scalekit Dashboard
- [ ] Configure CORS for production domains
- [ ] Set up error monitoring (Sentry)
- [ ] Add logging middleware
- [ ] Use Gunicorn with multiple workers
- [ ] Set up health checks
- [ ] Configure rate limiting

## Testing

```bash
# Test environment
python -c "from lib.scalekit import scalekit; print('✅ Scalekit configured')"

# Test API endpoints
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

curl http://localhost:8000/api/me
# Should return: 401 Unauthorized

# After logging in, test with cookies:
curl http://localhost:8000/api/me --cookie "accessToken=..."
# Should return user data
```

## Next Steps

- Add SQLAlchemy for user data persistence
- Implement role-based access control
- Add Celery for background tasks
- Enable social login in Scalekit Dashboard
- Add organization management
- Implement API key authentication for M2M
- Set up logging with structlog
- Add rate limiting with slowapi
