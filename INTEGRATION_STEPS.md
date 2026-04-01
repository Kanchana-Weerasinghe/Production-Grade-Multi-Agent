# Integration Steps - Action-Level Authentication

This guide provides step-by-step instructions to integrate the authentication system into your Travo Agent Solution.

## Step 1: Install Dependencies

Add required packages to your `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "bcrypt==4.0.1",
    "pydantic-settings>=2.0.0",
]
```

Or install via pip:
```bash
pip install python-jose passlib bcrypt pydantic-settings
```

## Step 2: Review Security Module Structure

The security module has been created with the following structure:

```
app/security/
├── __init__.py                    # Module exports
├── models.py                      # Data models (UserRole, Action, etc.)
├── authentication.py              # JWT and user management
├── authorization.py               # Permission checking
├── middleware.py                  # FastAPI middleware
├── orchestration_hooks.py          # Auth integration with LangGraph
```

## Step 3: Configure Settings

Update `app/config/settings.py` - this has already been done! Verify these settings are present:

```python
AUTH_SECRET_KEY: str = "your-secret-key-change-in-production"
TOKEN_EXPIRATION_HOURS: int = 24
RATE_LIMITING_ENABLED: bool = False
AUTH_ENABLED: bool = True
```

## Step 4: Update Main Application File

Update your `app/main.py` to include authentication:

```python
from fastapi import FastAPI
from app.security.middleware import AuthenticationMiddleware
from app.api.auth_gateway import router as auth_router
from app.config.settings import settings

app = FastAPI(title="Travo Agent Solution")

# Add authentication middleware
if settings.AUTH_ENABLED:
    app.add_middleware(
        AuthenticationMiddleware,
        excluded_paths=[
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    )

# Include authentication routes
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])

# Include your other routers...
# app.include_router(agent_router, prefix="/api/v1", tags=["agents"])
```

## Step 5: Integrate with Orchestrator

### Option A: Use Enhanced Delegator (Recommended)

Update your graph to use the authenticated delegator:

```python
from app.orchestrator.nodes.delegator_auth import delegate_task_with_auth
from app.security.orchestration_hooks import orchestration_auth_hooks

# In your graph setup:
graph.add_node("delegator", delegate_task_with_auth)

# When executing the graph:
from app.security.authentication import auth_service

# Simulate a user login (in real app, this comes from API)
user_info = auth_service.users_db["user"][0]
token_payload = auth_service.verify_token(auth_service.create_token(user_info))

# Inject auth context into state
state = orchestration_auth_hooks.inject_auth_context(
    initial_state,
    token_payload
)

result = graph.invoke(state)
```

### Option B: Manual Authorization Checks

Add authorization checks in your nodes:

```python
from app.security.orchestration_hooks import orchestration_auth_hooks

def my_node(state):
    # Check authorization before executing
    token_payload = get_token_from_somewhere(state)
    
    if not orchestration_auth_hooks.before_agent_execution(
        token_payload,
        "ResearchAgent",
        state
    ):
        return orchestration_auth_hooks.on_authorization_failure(
            token_payload,
            "Execute ResearchAgent",
            "User lacks RESEARCH permission",
            state
        )
    
    # Continue with node logic...
    return state
```

## Step 6: Protect Your API Endpoints

### Example 1: Simple User Authentication

```python
from fastapi import Depends
from app.security.middleware import get_current_user

@app.get("/api/v1/agents")
async def list_agents(current_user = Depends(get_current_user)):
    # Only authenticated users can access
    return {"agents": [...], "user": current_user.username}
```

### Example 2: Action-Level Authorization

```python
from app.security import Action, check_action_authorization

@app.post("/api/v1/agents/research")
async def research(
    query: str,
    current_user = Depends(get_current_user),
    auth = Depends(lambda req: check_action_authorization(req, Action.RESEARCH))
):
    # Only users with RESEARCH permission can access
    return {"status": "researching", "query": query}
```

### Example 3: Agent-Based Authorization

```python
from app.security.authorization import auth_service

@app.post("/api/v1/agents/{agent_name}/execute")
async def execute_agent(
    agent_name: str,
    current_user = Depends(get_current_user)
):
    # Check if user can access this agent
    result = auth_service.check_agent_access(current_user, agent_name)
    
    if not result.authorized:
        raise HTTPException(
            status_code=403,
            detail=result.reason
        )
    
    return {"status": "executing", "agent": agent_name}
```

## Step 7: Customize for Your Application

### Add Custom Roles

Edit `app/security/models.py`:

```python
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"
    SCIENTIST = "scientist"  # NEW
    ANALYST = "analyst"       # NEW
```

Then update `app/security/authorization.py`:

```python
self.role_permissions[UserRole.SCIENTIST] = [
    Action.RESEARCH,
    Action.PLAN,
]
```

### Add Custom Actions

Edit `app/security/models.py`:

```python
class Action(str, Enum):
    # ... existing ...
    DATA_IMPORT = "data_import"
    DATA_EXPORT = "data_export"
    MODEL_TRAIN = "model_train"
```

Then register agents for these actions in `app/security/authorization.py`:

```python
self.agent_actions["TrainerAgent"] = Action.MODEL_TRAIN
self.action_rate_limits[Action.MODEL_TRAIN] = 10
```

## Step 8: Test the Implementation

### Test 1: Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "user123"}'
```

### Test 2: Access Protected Endpoint
```bash
# Get token first (from login response)
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Use token to access protected endpoint
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Test 3: Check Permissions
```bash
curl -X GET http://localhost:8000/api/v1/auth/permissions \
  -H "Authorization: Bearer $TOKEN"
```

### Test 4: Check Agent Access
```bash
curl -X POST http://localhost:8000/api/v1/auth/check-agent/ResearchAgent \
  -H "Authorization: Bearer $TOKEN"
```

## Step 9: Production Setup

### Update Environment Variables

Create `.env.secrets` with production values:

```bash
AUTH_SECRET_KEY=<generate-strong-random-key-here>
TOKEN_EXPIRATION_HOURS=24
AUTH_ENABLED=true
RATE_LIMITING_ENABLED=true
```

Generate secure key:
```python
import secrets
key = secrets.token_urlsafe(32)
print(key)  # Use this for AUTH_SECRET_KEY
```

### Replace In-Memory User Store

The current implementation uses an in-memory user store (demo only). For production:

1. **PostgreSQL Example:**
```python
from sqlalchemy import Column, String, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True)
    password_hash = Column(String)
    roles = Column(JSON)
    permissions = Column(JSON)
    is_active = Column(Boolean, default=True)
```

2. **MongoDB Example:**
```python
from pymongo import MongoClient

class Users:
    def __init__(self, db_url):
        self.client = MongoClient(db_url)
        self.db = self.client.travo
        self.collection = self.db.users
    
    def find_by_username(self, username):
        return self.collection.find_one({"username": username})
```

3. **Update AuthenticationService:**
```python
class AuthenticationService:
    def __init__(self, user_repository):
        self.users = user_repository  # Use injected repository
        # ... rest of code
```

### Enable Rate Limiting

When `RATE_LIMITING_ENABLED=true`, implement rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/agents/research")
@limiter.limit("100/hour")
async def research(...):
    pass
```

### Enable HTTPS

Update `app/main.py` or deployment configuration:
- Use SSL certificates
- Set `force_https=True` in production
- Use secure cookies for tokens

## Step 10: Database Migrations (Optional)

If using database for users:

1. Create migration:
```bash
alembic init migrations
```

2. Create migration for users table:
```bash
alembic revision --autogenerate -m "Create users table"
```

3. Apply migration:
```bash
alembic upgrade head
```

## Verification Checklist

- [ ] Security module installed and importable
- [ ] Settings updated with AUTH configuration
- [ ] main.py includes authentication middleware
- [ ] auth_gateway routes included in FastAPI app
- [ ] Delegator updated with authorization checks
- [ ] Test users can login
- [ ] Token validation working
- [ ] Protected endpoints return 401 without token
- [ ] Protected endpoints return 403 with unauthorized user
- [ ] Orchestration receives auth context
- [ ] Logs show auth events
- [ ] Custom roles/actions registered (if added)
- [ ] Production environment variables set
- [ ] HTTPS enabled in production
- [ ] User store migrated to database (if applicable)

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'jose'"
```bash
pip install python-jose[cryptography]
```

### Issue: "ModuleNotFoundError: No module named 'app.security'"
- Ensure `app/security/` directory exists
- Ensure `app/security/__init__.py` exists
- Run from project root directory

### Issue: "Invalid authentication credentials"
- Check AUTH_SECRET_KEY is consistent
- Verify token hasn't expired
- Ensure token format is correct: `Authorization: Bearer <token>`

### Issue: "User not found"
- Check username spelling
- For demo, use: admin, user, or guest
- Check user is_active=True in database

### Issue: "Permission denied"
- Check user's roles have necessary permissions
- Use /auth/permissions endpoint to verify
- Admin can grant permissions via /admin/grant-permission

## Next Steps

1. Run through verification checklist
2. Test with provided test users
3. Customize roles/permissions for your use case
4. Migrate to database user store
5. Enable rate limiting
6. Deploy with HTTPS
7. Monitor authentication logs
8. Set up alerts for failed auth attempts

## Support & References

- Models: `app/security/models.py`
- Complete Guide: `ACTION_LEVEL_AUTH_GUIDE.md`
- Quick Reference: `QUICK_AUTH_REFERENCE.md`
- Examples: `app/examples/auth_workflow_example.py`
- Full Setup: `app/main_auth_setup.py`
