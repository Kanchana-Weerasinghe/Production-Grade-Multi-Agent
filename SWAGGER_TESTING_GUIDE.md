# 🎯 Swagger UI Testing Guide - Complete Steps

## ✅ Prerequisites

Make sure these are installed:
```bash
pip list | grep -E "fastapi|uvicorn|python-jose|passlib"
```

If any are missing:
```bash
pip install fastapi uvicorn python-jose[cryptography] passlib bcrypt
```

Or using uv:
```bash
uv pip install fastapi uvicorn python-jose[cryptography] passlib bcrypt
```

---

## 🚀 Step 1: Start the FastAPI Server

Open a terminal in your project directory and run:

```bash
# Option A: Direct Python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option B: Using uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## 📖 Step 2: Open Swagger UI

Once the server is running, open your browser and go to:

```
http://localhost:8000/docs
```

You should see:
- 🎵 Beautiful interactive Swagger UI
- 📋 All endpoints listed
- 🧪 "Try it out" buttons for each endpoint
- 🔒 Authorize button for authentication

---

## 🔐 Step 3: Test Endpoints (Complete Workflow)

### **A. Login (Get Token)**

1. Find endpoint: `POST /api/v1/auth/login`
2. Click "Try it out"
3. You'll see a request body box
4. Copy and paste this:

```json
{
  "username": "user",
  "password": "user123"
}
```

5. Click "Execute"
6. Look at **Response body**:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "user-001",
    "username": "user",
    "roles": [
      "user"
    ],
    "permissions": [
      "research",
      "summarize",
      "plan",
      "critique",
      "execute_workflow",
      "view_results"
    ]
  }
}
```

7. **COPY the `access_token` value** (the long string)

---

### **B. Authorize with Token**

1. Scroll to the top of Swagger UI
2. Click the green **🔒 Authorize** button
3. Dialog box appears: "Available authorizations"
4. Paste your token in the text field
5. Click "Authorize"
6. Click "Close"

**Now all protected endpoints will use this token!**

---

### **C. Test Protected Endpoints**

#### **1️⃣ Get Current User Info**
- Endpoint: `GET /api/v1/auth/me`
- Click "Try it out"
- Click "Execute"
- Response: Your user information

```json
{
  "user_id": "user-001",
  "username": "user",
  "roles": [
    "user"
  ],
  "permissions": [
    "research",
    "summarize",
    "plan",
    "critique",
    "execute_workflow",
    "view_results"
  ],
  "token_expires_at": "2026-03-27T10:00:00"
}
```

#### **2️⃣ Get Your Permissions**
- Endpoint: `GET /api/v1/auth/permissions`
- Click "Try it out" → "Execute"
- Response: All actions you can perform

```json
{
  "user_id": "user-001",
  "username": "user",
  "available_actions": [
    "research",
    "summarize",
    "plan",
    "critique",
    "execute_workflow",
    "view_results"
  ],
  "rate_limits": {
    "research": 100,
    "summarize": 200,
    ...
  }
}
```

#### **3️⃣ Check Agent Access**
- Endpoint: `POST /api/v1/auth/check-agent/ResearchAgent`
- Click "Try it out" → "Execute"
- Response:

```json
{
  "agent": "ResearchAgent",
  "authorized": true,
  "reason": null,
  "user_roles": [
    "user"
  ]
}
```

#### **4️⃣ Check Action Permission**
- Endpoint: `POST /api/v1/auth/check-permission/research`
- Click "Try it out" → "Execute"
- Response: Whether you have permission

```json
{
  "action": "research",
  "authorized": true,
  "reason": null,
  "user_roles": [
    "user"
  ],
  "user_permissions": [
    "research",
    "summarize",
    ...
  ]
}
```

---

## 🧪 Step 4: Test with Different Users

### **Test with GUEST User (Limited Access)**

1. Click "Authorize" button again (top of page)
2. Clear the token
3. Go back to **Login endpoint**
4. Try with guest credentials:

```json
{
  "username": "guest",
  "password": "guest123"
}
```

5. Copy new token
6. Authorize again
7. Now try endpoints:
   - ✅ GET `/auth/me` - Works (guest can view their own info)
   - ❌ POST `/auth/check-permission/research` - Returns 403 Forbidden

**Response when guest tries research:**
```json
{
  "action": "research",
  "authorized": false,
  "reason": "User guest does not have permission for action: research",
  "user_roles": [
    "guest"
  ],
  "user_permissions": [
    "view_results"
  ]
}
```

### **Test with ADMIN User (Full Access)**

1. Login with admin:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

2. Authorize with admin token
3. Try all endpoints:
   - ✅ POST `/admin/grant-permission/{user_id}/{action}` - Works (admin only)
   - ✅ GET `/admin/all-actions` - Works (see all system actions)
   - All action checks return authorized: true

---

## 🚨 Testing Authorization Failures

### **Scenario 1: No Token**
- Don't authorize (clear token)
- Try: `GET /api/v1/auth/permissions`
- **Result:** 401 Unauthorized

### **Scenario 2: Invalid/Expired Token**
- Authorize with a wrong token
- Try: `GET /api/v1/auth/me`
- **Result:** 401 Unauthorized

### **Scenario 3: Valid Token, Wrong Permission**
- Login as GUEST
- Try: `POST /auth/check-permission/research`
- **Result:** 403 Forbidden (permission denied)

### **Scenario 4: Wrong Credentials**
- Endpoint: `POST /api/v1/auth/login`
- Try: `{"username": "user", "password": "wrongpassword"}`
- **Result:** 401 Unauthorized

---

## 📊 Complete Test Checklist

| Test | User | Expected | Status |
|------|------|----------|--------|
| **Login Success** | user | 200 + token | ☐ |
| **Get User Info** | user | 200 + user data | ☐ |
| **Get Permissions** | user | 200 + actions | ☐ |
| **Check Research** | user | 200 + authorized: true | ☐ |
| **Login as Guest** | guest | 200 + token | ☐ |
| **Guest Research** | guest | 200 + authorized: false | ☐ |
| **Guest View Results** | guest | 200 + authorized: true | ☐ |
| **Login as Admin** | admin | 200 + token | ☐ |
| **Admin Grant Perm** | admin | 200 + success | ☐ |
| **Admin View All** | admin | 200 + all actions | ☐ |
| **No Token** | none | 401 + error | ☐ |
| **Invalid Token** | bad | 401 + error | ☐ |
| **Agent Access** | user | 200 + authorized | ☐ |

---

## 🔍 Understanding Swagger UI Elements

### **In Each Endpoint:**

```
┌─────────────────────────────────────────────────┐
│ POST /api/v1/auth/login                    ▼   │
│ User authentication endpoint              [Try] │
├─────────────────────────────────────────────────┤
│                                                  │
│ Parameters: (none shown)                        │
│                                                  │
│ Request body:                                   │
│ ┌──────────────────────────────────────────┐   │
│ │ {                                        │   │
│ │   "username": "string",                  │   │
│ │   "password": "string"                   │   │
│ │ }                                        │   │
│ └──────────────────────────────────────────┘   │
│                                                  │
│ Responses:                                      │
│ ☐ 200 Success                                   │
│ ☐ 401 Unauthorized                             │
│                                                  │
└─────────────────────────────────────────────────┘
```

Click **"Try it out"** to interact with the endpoint.

---

## 💾 Troubleshooting

### **Problem: "Address already in use"**
```bash
# Port 8000 is already in use. Kill it:
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti :8000 | xargs kill -9

# Then restart
```

### **Problem: "ModuleNotFoundError"**
```bash
# You might need to install from project root:
pip install -e .
# or
uv pip install -e .
```

### **Problem: "No response/timeout"**
- Check server is running in terminal
- Check URL is correct: `http://localhost:8000/docs`
- Try refreshing browser

### **Problem: "401 Unauthorized" on protected endpoints**
- You forgot to authorize
- Click green 🔒 "Authorize" button
- Paste token
- Try again

### **Problem: "Invalid token"**
- Token may have expired (default 24 hours)
- Get a new token from login endpoint
- Re-authorize

---

## 🎓 Learning Path

1. **Start here:** Login with USER account
2. **Then:** Check your permissions (should have 6 actions)
3. **Then:** Test agent access (ResearchAgent should work)
4. **Then:** Login with GUEST (should have only 1 action)
5. **Then:** Try GUEST accessing research (should fail with 403)
6. **Then:** Login with ADMIN (should have all actions)
7. **Then:** Test admin endpoint like grant-permission
8. **Finally:** Test with invalid/no token (should get 401)

---

## 📚 Additional Resources

- Swagger/OpenAPI Docs: http://localhost:8000/docs
- ReDoc Alternative: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json
- Full Auth Guide: `ACTION_LEVEL_AUTH_GUIDE.md`
- Quick Reference: `QUICK_AUTH_REFERENCE.md`

---

## 🎯 Test Users

```
username: admin    | password: admin123  | role: ADMIN   (all permissions)
username: user     | password: user123   | role: USER    (research, summarize, etc.)
username: guest    | password: guest123  | role: GUEST   (view_results only)
```

---

## ✨ Pro Tips

1. **Keep token visible:** Copy token to notepad while testing
2. **Test one user at a time:** Click Authorize → Clear → Re-authorize with new token
3. **Watch the logs:** Check server terminal for detailed auth logs
4. **Try ReDoc:** Same URL but `/redoc` instead of `/docs` - different UI style
5. **Export responses:** Many browsers allow copying response JSON
6. **Network tab:** Open browser DevTools (F12) → Network tab to see actual requests

---

**You're ready! Start the server and open http://localhost:8000/docs** 🚀
