# ✨ Swagger Authentication Testing - Quick Setup

## 📦 What Was Created

✅ **Updated `app/main.py`** - Complete FastAPI application with:
   - Authentication middleware
   - CORS support
   - All auth routes included
   - Error handling
   - Swagger UI auto-enabled

✅ **Startup Scripts:**
   - `start_auth_server.bat` - For Windows
   - `start_auth_server.sh` - For Mac/Linux

✅ **Documentation:**
   - `SWAGGER_TESTING_GUIDE.md` - Complete step-by-step guide
   - `SWAGGER_ENDPOINTS_GUIDE.md` - Visual reference of all endpoints
   - This file - Quick setup summary

---

## 🚀 Get Started in 2 Minutes

### **Windows Users:**
```bash
# Double-click this file:
start_auth_server.bat

# Or open PowerShell/CMD and run:
python -m uvicorn app.main:app --reload
```

### **Mac/Linux Users:**
```bash
# Make script executable
chmod +x start_auth_server.sh

# Run it
./start_auth_server.sh

# Or direct command
python -m uvicorn app.main:app --reload
```

### **Any OS:**
```bash
# Option 1: Direct
python -m uvicorn app.main:app --reload

# Option 2: Using uv
uv run uvicorn app.main:app --reload
```

---

## ✅ You Should See This Output

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

## 🎯 Open Swagger UI

Once server is running, open your browser:

```
http://localhost:8000/docs
```

You'll see:
- 📋 All 7 authentication endpoints
- 🔐 Authorization button
- 🧪 "Try it out" buttons
- 📊 Live responses

**Alternative UI (ReDoc):**
```
http://localhost:8000/redoc
```

---

## 🔑 Test Users (Pre-configured)

| User | Password | Best For |
|------|----------|----------|
| **admin** | admin123 | Full access, all features |
| **user** | user123 | Standard workflow |
| **guest** | guest123 | Limited access testing |

---

## 🧪 Quick 5-Minute Test

1. **Start server** (run startup script or command above)
2. **Open** http://localhost:8000/docs
3. **Login** with `user / user123`:
   - Find `POST /api/v1/auth/login`
   - Click "Try it out"
   - Enter credentials
   - Copy token from response
4. **Authorize** in Swagger:
   - Click green "🔒 Authorize" button
   - Paste token
   - Click "Authorize"
5. **Try endpoints**:
   - GET `/api/v1/auth/me` - See your info
   - GET `/api/v1/auth/permissions` - See what you can do
   - POST `/api/v1/auth/check-agent/ResearchAgent` - Check agent access

**Done! ✅**

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **SWAGGER_TESTING_GUIDE.md** | Step-by-step complete guide (READ FIRST) |
| **SWAGGER_ENDPOINTS_GUIDE.md** | Visual reference of all endpoints |
| **ACTION_LEVEL_AUTH_GUIDE.md** | Deep technical documentation |
| **QUICK_AUTH_REFERENCE.md** | Quick curl/code reference |

---

## 🎨 What Endpoints You Can Test

### Public (No Token)
- `GET /health` - Server status
- `POST /api/v1/auth/login` - Get token

### User (Token Required)
- `GET /api/v1/auth/me` - Your info
- `GET /api/v1/auth/permissions` - What you can do
- `POST /api/v1/auth/check-permission/{action}` - Check action
- `POST /api/v1/auth/check-agent/{agent_name}` - Check agent

### Admin (Admin Token Required)
- `POST /api/v1/admin/grant-permission/{user_id}/{action}` - Grant permission
- `GET /api/v1/admin/all-actions` - See all actions

---

## 🔍 Test Scenarios

### ✅ Everything Works
```
1. Login with "user" ✓
2. Get token ✓
3. Check permissions ✓
4. Access endpoints ✓
```

### ❌ Permission Denied (Guest User)
```
1. Login with "guest" ✓
2. Try research action ✗
3. Get 403 Forbidden ✓
```

### ⚠️ No Token
```
1. Don't authorize ✓
2. Try protected endpoint ✗
3. Get 401 Unauthorized ✓
```

---

## 📊 Endpoints Summary

```
7 Endpoints Total:

🟢 PUBLIC (2)
  - GET    /health
  - POST   /api/v1/auth/login

🔵 USER (4)
  - GET    /api/v1/auth/me
  - GET    /api/v1/auth/permissions
  - POST   /api/v1/auth/check-permission/{action}
  - POST   /api/v1/auth/check-agent/{agent_name}

🔴 ADMIN (2)
  - POST   /api/v1/admin/grant-permission/{user_id}/{action}
  - GET    /api/v1/admin/all-actions
```

---

## 🎯 Key Features You Can Test

✅ **Authentication**
- Login with different users
- Token generation
- Invalid credentials handling

✅ **Authorization**
- Check what each role can do
- Role-based permissions
- Action-level restrictions

✅ **User Levels**
- Admin (all permissions)
- User (standard permissions)
- Guest (view-only)

✅ **Security**
- 401 Unauthorized (no token)
- 403 Forbidden (wrong permission)
- Token validation
- Password protection

---

## 🚨 If You Get Errors

### "Address already in use"
```bash
# Kill process on port 8000
Windows: netstat -ano | findstr :8000 
         taskkill /PID <PID> /F
Mac/Linux: lsof -ti :8000 | xargs kill -9
```

### "ModuleNotFoundError"
```bash
pip install fastapi uvicorn python-jose[cryptography] passlib bcrypt
```

### "401 Unauthorized on protected endpoints"
- Click 🔒 "Authorize" button in Swagger
- Paste your token
- Try again

### "Page not found"
- Check URL: http://localhost:8000/docs
- Make sure server is running
- Check server logs in terminal

---

## 📱 Browser Tips

1. **Open DevTools** (F12) to see network requests
2. **Copy responses** for reference
3. **Keep token visible** in another window
4. **Use multiple tabs** - one for each user test

---

## ⏱️ Token Expiration

- Default expiration: **24 hours**
- When expired: Get 401 Unauthorized
- Solution: Login again to get new token

---

## 🎓 Next Steps After Testing

1. ✅ Test all endpoints in Swagger UI
2. ✅ Understand the authentication flow
3. ✅ Verify all user roles work correctly
4. ✅ Test permission denials
5. ✅ Read `ACTION_LEVEL_AUTH_GUIDE.md` for deep dive
6. ✅ Integrate with your actual application

---

## 💡 Pro Tips

1. **Triple-click copying token** - Select all characters
2. **Bookmark Swagger UI** - http://localhost:8000/docs
3. **Keep terminal visible** - See auth logs in real-time
4. **Test one user at a time** - Avoid confusion
5. **Check ReDoc** - Alternative documentation view

---

## 🔗 Quick Links

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## ✅ Verification Checklist

Before moving forward:

- [ ] Server starts without errors
- [ ] Can access http://localhost:8000/docs
- [ ] Can login with user / user123
- [ ] Get token in response
- [ ] Can authorize in Swagger
- [ ] Can call protected endpoints
- [ ] Guest has limited permissions
- [ ] Admin has all permissions
- [ ] Invalid token returns 401
- [ ] No token returns 401

---

## 🎉 You're Ready!

**Run your startup script now:**

Windows:
```
start_auth_server.bat
```

Mac/Linux:
```
bash start_auth_server.sh
```

**Then open:**
```
http://localhost:8000/docs
```

**Happy testing!** 🚀

---

## 📞 Need Help?

Check these files in order:
1. **SWAGGER_TESTING_GUIDE.md** - Step-by-step instructions
2. **SWAGGER_ENDPOINTS_GUIDE.md** - Endpoint reference
3. **ACTION_LEVEL_AUTH_GUIDE.md** - Technical details
4. **Server terminal** - Check logs for errors

---

Last Updated: March 26, 2026
Version: 1.0 - Ready for Testing ✅
