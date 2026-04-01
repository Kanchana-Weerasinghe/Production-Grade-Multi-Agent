@echo off
REM Start Travo Authentication Service - Windows

echo.
echo ========================================
echo   Travo Agent Solution - Auth Service
echo ========================================
echo.

REM Check if uvicorn is installed
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install fastapi uvicorn python-jose[cryptography] passlib bcrypt
)

echo.
echo Starting server on http://localhost:8000
echo.
echo 🎯 Swagger UI:  http://localhost:8000/docs
echo 📖 ReDoc:       http://localhost:8000/redoc
echo 🏥 Health:      http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
