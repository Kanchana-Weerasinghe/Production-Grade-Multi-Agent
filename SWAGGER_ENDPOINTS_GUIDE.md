# 🎨 Swagger Endpoints Visual Guide

## 🚀 Quick Start

**Start Server:**
```bash
# Windows
start_auth_server.bat

# Mac/Linux
bash start_auth_server.sh

# Or direct
python -m uvicorn app.main:app --reload
```

**Open Swagger UI:**
```
http://localhost:8000/docs
```

---

## 📋 All Available Endpoints

### 🟢 **Public Endpoints (No Token Required)**

#### **Health Check**
```
GET /health
├─ No auth required
├─ Returns: Server status
└─ Status 200 OK
```

#### **Login**
```
POST /api/v1/auth/login
├─ No auth required
├─ Body: { "username": "user", "password": "user123" }
├─ Returns: access_token
└─ Status 200 OK | 401 Unauthorized
```

---

### 🔵 **User Endpoints (Token Required)**

#### **Get Current User**
```
GET /api/v1/auth/me
├─ Requires: Bearer Token
├─ Returns: User info, roles, permissions
└─ Status 200 OK | 401 Unauthorized
```

#### **Get User Permissions**
```
GET /api/v1/auth/permissions
├─ Requires: Bearer Token
├─ Returns: List of available actions & rate limits
└─ Status 200 OK | 401 Unauthorized
```

#### **Check Permission**
```
POST /api/v1/auth/check-permission/{action}
├─ Requires: Bearer Token
├─ Path param: action (e.g., "research", "summarize")
├─ Returns: authorized: true/false
└─ Status 200 OK | 400 Bad Request | 401 Unauthorized
```

#### **Check Agent Access**
```
POST /api/v1/auth/check-agent/{agent_name}
├─ Requires: Bearer Token
├─ Path param: agent_name (e.g., "ResearchAgent")
├─ Returns: authorized: true/false
└─ Status 200 OK | 401 Unauthorized
```

---

### 🔴 **Admin Endpoints (Admin Token Required)**

#### **Grant Permission**
```
POST /api/v1/admin/grant-permission/{user_id}/{action}
├─ Requires: Bearer Token (ADMIN only)
├─ Path params: user_id, action
├─ Returns: success message
└─ Status 200 OK | 403 Forbidden | 401 Unauthorized
```

#### **List All Actions**
```
GET /api/v1/admin/all-actions
├─ Requires: Bearer Token (ADMIN only)
├─ Returns: All system actions & rate limits
└─ Status 200 OK | 403 Forbidden | 401 Unauthorized
```

---

## 🧪 Test Scenarios

### Scenario 1: Complete User Workflow
```
1. POST /api/v1/auth/login
   Body: {"username": "user", "password": "user123"}
   ↓ Get token
   
2. GET /api/v1/auth/me
   Header: Authorization: Bearer <token>
   ↓ See your info
   
3. GET /api/v1/auth/permissions
   Header: Authorization: Bearer <token>
   ↓ See what you can do
   
4. POST /api/v1/auth/check-permission/research
   Header: Authorization: Bearer <token>
   ↓ Check specific permission
```

### Scenario 2: Guest User - Limited Access
```
1. POST /api/v1/auth/login
   Body: {"username": "guest", "password": "guest123"}
   ↓ Get guest token
   
2. GET /api/v1/auth/permissions
   ↓ Returns: [view_results] only
   
3. POST /api/v1/auth/check-permission/research
   ↓ Returns: authorized: false
   
4. POST /api/v1/auth/check-permission/view_results
   ↓ Returns: authorized: true
```

### Scenario 3: Admin User - Full Access
```
1. POST /api/v1/auth/login
   Body: {"username": "admin", "password": "admin123"}
   ↓ Get admin token
   
2. GET /api/v1/admin/all-actions
   ↓ See all 8 actions
   
3. POST /api/v1/admin/grant-permission/user-001/research
   ↓ Grant new permission
```

---

## 📊 Response Examples

### Successful Login
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "user-001",
    "username": "user",
    "roles": ["user"],
    "permissions": ["research", "summarize", "plan", ...]
  }
}
```

### Successful Permission Check
```json
{
  "action": "research",
  "authorized": true,
  "reason": null,
  "user_roles": ["user"],
  "user_permissions": ["research", "summarize", ...]
}
```

### Denied Permission
```json
{
  "action": "research",
  "authorized": false,
  "reason": "User guest does not have permission for action: research",
  "user_roles": ["guest"],
  "user_permissions": ["view_results"]
}
```

### Error Responses
```json
// 401 Unauthorized (No/Invalid Token)
{
  "detail": "Missing or invalid token"
}

// 403 Forbidden (Valid Token, Wrong Permission)
{
  "detail": "Insufficient permissions"
}

// 401 Unauthorized (Wrong Credentials)
{
  "detail": "Invalid username or password"
}
```

---

## 🎮 Interactive Testing in Swagger UI

### Step-by-Step

1. **Open:** http://localhost:8000/docs
2. **Find:** POST /api/v1/auth/login
3. **Click:** "Try it out" button
4. **Enter:** 
   ```json
   {
     "username": "user",
     "password": "user123"
   }
   ```
5. **Click:** "Execute"
6. **Copy:** The `access_token` value
7. **Click:** Green "🔒 Authorize" button (top of page)
8. **Paste:** Token in text field
9. **Click:** "Authorize"
10. **Try:** Other endpoints (they'll use your token)

---

## 🔑 Test User Credentials

| User | Password | Roles | Permissions | Use For |
|------|----------|-------|-------------|---------|
| admin | admin123 | ADMIN | All 8 actions | Test full access |
| user | user123 | USER | 6 standard actions | Test normal user |
| guest | guest123 | GUEST | view_results only | Test restricted user |

---

## 🎯 Endpoints by Purpose

### **Authentication**
- POST /api/v1/auth/login - Get token

### **User Info**
- GET /api/v1/auth/me - Get current user
- GET /api/v1/auth/permissions - Get my permissions

### **Permission Checking**
- POST /api/v1/auth/check-permission/{action} - Check action
- POST /api/v1/auth/check-agent/{agent_name} - Check agent

### **Admin Operations**
- POST /api/v1/admin/grant-permission/{user_id}/{action} - Grant permission
- GET /api/v1/admin/all-actions - List all actions

---

## ✅ Testing Checklist

### Basic Tests
- [ ] Health check works
- [ ] Can login with user
- [ ] Can login with guest
- [ ] Can login with admin
- [ ] Invalid password returns 401

### Permission Tests
- [ ] User has research permission
- [ ] Guest does NOT have research
- [ ] Guest has view_results
- [ ] Admin has all permissions

### Token Tests
- [ ] Token expires after 24 hours
- [ ] Invalid token returns 401
- [ ] Valid token grants access

### Admin Tests
- [ ] Admin can grant permissions
- [ ] Admin can view all actions
- [ ] Non-admin cannot grant permissions
- [ ] Non-admin cannot view all actions

---

## 🚨 Common Status Codes

| Code | Meaning | Fix |
|------|---------|-----|
| 200 | Success | ✅ All good |
| 400 | Bad Request | Check parameters |
| 401 | Unauthorized | Wrong credentials or missing token |
| 403 | Forbidden | Valid token but no permission |
| 404 | Not Found | Wrong endpoint URL |
| 500 | Server Error | Check server logs |

---

## 📱 Alternative: ReDoc Documentation

Same endpoints, different UI:
```
http://localhost:8000/redoc
```

Good for:
- Reading documentation
- Understanding data models
- Seeing all endpoints organized by tag

---

## 🔗 OpenAPI Schema

Get raw OpenAPI/Swagger schema:
```
http://localhost:8000/openapi.json
```

Use for:
- Integration with other tools
- Code generation
- API documentation

---

**Ready to test? Open http://localhost:8000/docs now!** 🎉
