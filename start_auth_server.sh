#!/bin/bash

# Start Travo Authentication Service - Mac/Linux

echo ""
echo "========================================"
echo "  Travo Agent Solution - Auth Service"
echo "========================================"
echo ""

# Check if uvicorn is installed
python -c "import uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install fastapi uvicorn python-jose[cryptography] passlib bcrypt
fi

echo ""
echo "Starting server on http://localhost:8000"
echo ""
echo "🎯 Swagger UI:  http://localhost:8000/docs"
echo "📖 ReDoc:       http://localhost:8000/redoc"
echo "🏥 Health:      http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
