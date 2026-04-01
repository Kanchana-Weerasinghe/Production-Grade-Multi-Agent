# Action-Level Authentication Implementation Guide

## Overview

This guide explains how to implement and use the action-level authentication system in the Travo Agent Solution.

## System Components

### 1. **Models** (`app/security/models.py`)
- `UserRole`: Enum for user roles (ADMIN, MANAGER, USER, GUEST)
- `Action`: Enum for all system actions (RESEARCH, SUMMARIZE, PLAN, CRITIQUE, etc.)
- `TokenPayload`: JWT token structure with user info and permissions
- `AuthorizationResult`: Result of authorization checks

### 2. **Authentication** (`app/security/authentication.py`)
- Token generation and validation
- User credential verification
- JWT management
- Password hashing

### 3. **Authorization** (`app/security/authorization.py`)
- Role-based permissions mapping
- Agent-to-action mapping
- Rate limiting per action
- Permission checking and enforcement

### 4. **Middleware** (`app/security/middleware.py`)
- FastAPI middleware for token validation
- Request authentication decorator
- Authorization dependency injection

### 5. **Orchestration Hooks** (`app/security/orchestration_hooks.py`)
- Pre-execution authorization checks
- Auth context injection into workflow
- Failure handling

### 6. **API Routes** (`app/api/auth_gateway.py`)
- Login endpoint
- Permission checking endpoints
- Admin permission management

## Integration Steps

### Step 1: Update FastAPI Application (main.py)

```python
from fastapi import FastAPI
from app.api.auth_gateway import router as auth_router
from app.security.middleware import AuthenticationMiddleware

app = FastAPI()

# Add authentication middleware
app.add_middleware(
    AuthenticationMiddleware,
    excluded_paths=[
        "/health",
        "/auth/login",
        "/docs",
        "/openapi.json",
        "/redoc"
    ]
)

# Include auth routes
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])

# Include other routers
# app.include_router(other_routes)
```

### Step 2: Update Configuration (settings.py)

```python
class Settings(BaseSettings):
    # Existing settings...
    
    # Authentication
    AUTH_SECRET_KEY: str = "your-secret-key-change-in-production"
    TOKEN_EXPIRATION_HOURS: int = 24
    
    # Authorization
    RATE_LIMITING_ENABLED: bool = True
```

### Step 3: Update Delegator Node

Use the enhanced delegator with auth checks:

```python
from app.orchestrator.nodes.delegator_auth import delegate_task_with_auth

# In your graph definition:
graph.add_node("delegator", delegate_task_with_auth)
```

### Step 4: Inject Auth Context in Graph

When starting the graph, inject authentication context:

```python
from app.security.orchestration_hooks import orchestration_auth_hooks

# When executing graph:
state = orchestration_auth_hooks.inject_auth_context(state, token_payload)
result = graph.invoke(state)
```

## Usage Examples

### 1. User Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d {
    "username": "user",
    "password": "user123"
  }
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "user-001",
    "username": "user",
    "roles": ["user"],
    "permissions": ["research", "summarize", "plan", "critique"]
  }
}
```

### 2. Check Permissions

```bash
curl -X GET "http://localhost:8000/api/v1/auth/permissions" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 3. Check Agent Access

```bash
curl -X POST "http://localhost:8000/api/v1/auth/check-agent/ResearchAgent" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 4. Check Action Permission

```bash
curl -X POST "http://localhost:8000/api/v1/auth/check-permission/research" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 5. Grant Permission (Admin Only)

```bash
curl -X POST "http://localhost:8000/api/v1/admin/grant-permission/user-001/summarize" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## Default Users for Testing

### Admin User
- **Username:** admin
- **Password:** admin123
- **Permissions:** All actions

### Regular User
- **Username:** user
- **Password:** user123
- **Permissions:** research, summarize, plan, critique, execute_workflow, view_results

### Guest User
- **Username:** guest
- **Password:** guest123
- **Permissions:** view_results only

## Role-Based Permissions Matrix

| Role | RESEARCH | SUMMARIZE | PLAN | CRITIQUE | EXECUTE | VIEW | ADMIN |
|------|----------|-----------|------|----------|---------|------|-------|
| ADMIN | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| MANAGER | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| USER | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| GUEST | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |

## Rate Limiting

Each action has a default rate limit (requests per hour):

- **RESEARCH:** 100
- **SUMMARIZE:** 200
- **PLAN:** 50
- **CRITIQUE:** 75
- **EXECUTE_WORKFLOW:** 25
- **VIEW_RESULTS:** 1000
- **MANAGE_USERS:** 50
- **MODIFY_POLICIES:** 10

## Production Deployment Checklist

- [ ] Change `AUTH_SECRET_KEY` to a strong, randomly generated value
- [ ] Replace in-memory user store with database (PostgreSQL, MongoDB, etc.)
- [ ] Implement proper password hashing with bcrypt
- [ ] Add rate limiting implementation (Redis, in-memory cache)
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Set up token refresh mechanism
- [ ] Add audit logging for all auth events
- [ ] Implement session management
- [ ] Add 2FA/MFA support
- [ ] Set up monitoring and alerting

## Customization

### Add New Roles

Update `UserRole` enum in `app/security/models.py`:

```python
class UserRole(str, Enum):
    CUSTOM_ROLE = "custom_role"
```

### Add New Actions

Update `Action` enum in `app/security/models.py`:

```python
class Action(str, Enum):
    CUSTOM_ACTION = "custom_action"
```

### Update Role Permissions

Modify `role_permissions` dict in `AuthorizationService.__init__()`:

```python
self.role_permissions[UserRole.CUSTOM_ROLE] = [
    Action.RESEARCH,
    Action.CUSTOM_ACTION,
]
```

### Update Agent Capabilities

Modify `agent_actions` dict in `AuthorizationService.__init__()`:

```python
self.agent_actions["CustomAgent"] = Action.CUSTOM_ACTION
```

## Troubleshooting

### "Missing Authorization header"
- Ensure you're sending the token in the Authorization header
- Format: `Authorization: Bearer <token>`

### "Invalid or expired token"
- Token may have expired. Get a new token via login endpoint
- Check that `AUTH_SECRET_KEY` is consistent across all instances

### "Insufficient permissions"
- Your user role doesn't have the required permission
- Contact admin or request permission grant

### "Unknown agent"
- Agent name is not registered in `agent_actions` mapping
- Add the agent to the mapping in `AuthorizationService`

## Security Best Practices

1. **Token Security:**
   - Never expose tokens in logs
   - Store tokens securely in client
   - Use HTTPS in production
   - Implement token refresh mechanism

2. **Password Security:**
   - Use bcrypt or similar for hashing
   - Enforce strong password requirements
   - Never log passwords
   - Consider password expiration policies

3. **Role Management:**
   - Follow principle of least privilege
   - Regularly audit role assignments
   - Remove unused roles/permissions
   - Document role purposes

4. **Auditing:**
   - Log all authentication attempts
   - Log all authorization failures
   - Track permission grants/revokes
   - Monitor unusual access patterns

5. **Rate Limiting:**
   - Implement rate limiting to prevent abuse
   - Monitor rate limit violations
   - Adjust limits based on usage patterns

## Next Steps

1. Update `app/main.py` to integrate authentication
2. Update `app/config/settings.py` with auth configuration
3. Migrate user store to database
4. Implement rate limiting
5. Add audit logging
6. Deploy with HTTPS
