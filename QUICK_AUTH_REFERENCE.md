# Action-Level Authentication - Quick Reference

## Quick Start

### 1. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "user123"}'
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
    "permissions": ["research", "summarize", "plan", "critique", "execute_workflow", "view_results"]
  }
}
```

### 2. Use Token in Requests
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <your_token>"
```

## Common Operations

### Check Your Permissions
```bash
curl -X GET http://localhost:8000/api/v1/auth/permissions \
  -H "Authorization: Bearer <token>"
```

### Check Agent Access
```bash
curl -X POST http://localhost:8000/api/v1/auth/check-agent/ResearchAgent \
  -H "Authorization: Bearer <token>"
```

### Check Action Permission
```bash
curl -X POST http://localhost:8000/api/v1/auth/check-permission/research \
  -H "Authorization: Bearer <token>"
```

## Protected Endpoints Pattern

```python
from fastapi import Depends
from app.security import get_current_user, check_action_authorization, Action

@app.post("/api/research")
async def research(
    current_user = Depends(get_current_user),
    auth = Depends(lambda req: check_action_authorization(req, Action.RESEARCH))
):
    # User is authenticated and authorized for RESEARCH action
    return {"status": "success"}
```

## Test Users

| User | Password | Roles | Can Do |
|------|----------|-------|--------|
| admin | admin123 | ADMIN | Everything |
| user | user123 | USER | Research, Summarize, Plan, Critique, Execute |
| guest | guest123 | GUEST | View Results Only |

## Actions & Agents

| Agent | Action | Rate Limit |
|-------|--------|-----------|
| ResearchAgent | RESEARCH | 100/hour |
| SummarizerAgent | SUMMARIZE | 200/hour |
| PlannerAgent | PLAN | 50/hour |
| CriticAgent | CRITIQUE | 75/hour |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ FastAPI Application                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ AuthenticationMiddleware                         │  │
│  │ - Validates JWT tokens                           │  │
│  │ - Extracts user info                             │  │
│  │ - Injects into request.state                     │  │
│  └──────────────────────────────────────────────────┘  │
│                    ↓                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Route Handler                                    │  │
│  │ - Uses get_current_user() dependency             │  │
│  │ - Uses check_action_authorization() dependency   │  │
│  │ - Processes request with auth context           │  │
│  └──────────────────────────────────────────────────┘  │
│                    ↓                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Orchestration (LangGraph)                        │  │
│  │ - Injects auth context into state               │  │
│  │ - delegate_task checks agent authorization      │  │
│  │ - Logs all action attempts                       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Integration Checklist

- [ ] Install dependencies (fastapi, python-jose, passlib, bcrypt)
- [ ] Copy security module to `app/security/`
- [ ] Update `app/config/settings.py` with AUTH settings
- [ ] Import and add middleware to main.py
- [ ] Include auth_gateway router in main.py
- [ ] Update delegator to use delegator_auth
- [ ] Test with provided test users
- [ ] Customize roles/permissions for your use case
- [ ] Set AUTH_SECRET_KEY in production
- [ ] Switch to database-backed user store

## Error Codes

| Code | Error | Solution |
|------|-------|----------|
| 401 | Missing/Invalid token | Include valid Authorization header |
| 403 | Insufficient permissions | Request admin to grant permission |
| 400 | Invalid action | Check action name spelling |
| 500 | Internal server error | Check logs for details |

## Code Examples

### Example 1: Simple Protected Endpoint
```python
@app.get("/api/data")
async def get_data(current_user = Depends(get_current_user)):
    return {"data": "secret", "user": current_user.username}
```

### Example 2: Action-Protected Endpoint
```python
@app.post("/api/research")
async def research(
    current_user = Depends(get_current_user),
    auth = Depends(lambda req: check_action_authorization(req, Action.RESEARCH))
):
    return {"status": "researching"}
```

### Example 3: Custom Authorization
```python
async def require_admin(current_user = Depends(get_current_user)):
    from app.security.models import UserRole
    if UserRole.ADMIN not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user

@app.post("/api/admin")
async def admin_action(current_user = Depends(require_admin)):
    return {"status": "admin action success"}
```

### Example 4: Multiple Permissions
```python
async def require_research_and_summarize(
    current_user = Depends(get_current_user)
):
    required = {Action.RESEARCH, Action.SUMMARIZE}
    user_actions = set(current_user.permissions)
    
    if not required.issubset(user_actions):
        raise HTTPException(status_code=403, detail="Missing required permissions")
    
    return current_user

@app.post("/api/research-summarize")
async def research_and_summarize(
    current_user = Depends(require_research_and_summarize)
):
    return {"status": "success"}
```

## Production Configuration

### Environment Variables
```bash
AUTH_SECRET_KEY=<very-long-random-string>
TOKEN_EXPIRATION_HOURS=24
AUTH_ENABLED=true
RATE_LIMITING_ENABLED=true
```

### Security Best Practices
1. Use strong AUTH_SECRET_KEY
2. Enable HTTPS in production
3. Store tokens in secure cookies/localStorage
4. Implement token refresh
5. Add audit logging
6. Use database for user store
7. Implement rate limiting
8. Monitor failed auth attempts

## Troubleshooting

### Issue: "Missing Authorization header"
**Solution:** Ensure you're sending `Authorization: Bearer <token>` header

### Issue: "Invalid or expired token"
**Solution:** Get new token from login endpoint

### Issue: "Insufficient permissions"
**Solution:** Contact admin to grant necessary permissions

### Issue: "Unknown agent"
**Solution:** Add agent to `agent_actions` mapping in AuthorizationService

## More Information

- Full guide: See `ACTION_LEVEL_AUTH_GUIDE.md`
- Examples: See `app/examples/auth_workflow_example.py`
- Models: `app/security/models.py`
- Authentication: `app/security/authentication.py`
- Authorization: `app/security/authorization.py`
