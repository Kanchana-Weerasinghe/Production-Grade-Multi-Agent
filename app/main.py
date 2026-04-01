"""
Main FastAPI Application with Authentication and Authorization
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.api.auth_gateway import router as auth_router
from app.security.middleware import AuthenticationMiddleware
from app.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Travo Agent Solution starting up...")
    print(f"   Auth Enabled: {settings.AUTH_ENABLED}")
    print(f"   Log Level: {settings.LOG_LEVEL}")
    print(f"   Zero Trust: {getattr(settings, 'ENABLE_ZERO_TRUST', True)}")
    print(f"   JIT Privileges: {getattr(settings, 'ENABLE_JIT_PRIVILEGES', True)}")
    
    # Start background cleanup task for JIT tokens
    from app.security.jit_manager import jit_manager
    import asyncio
    
    async def cleanup_jit_tokens():
        while True:
            await asyncio.sleep(60)  # Clean up every minute
            jit_manager.cleanup_expired_tokens()
    
    cleanup_task = asyncio.create_task(cleanup_jit_tokens())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    print("🛑 Application shutting down...")


def create_app():
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Travo Agent Solution",
        description="Multi-Agent System with Action-Level Authentication",
        version="1.0.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # ========================================================================
    # OpenAPI Security Scheme (for Swagger UI Authorization button)
    # ========================================================================
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Travo Agent Solution",
            version="1.0.0",
            description="Multi-Agent System with Action-Level Authentication",
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT token from /api/v1/auth/login"
            }
        }
        # Apply security to all endpoints except login and health
        for path, methods in openapi_schema.get("paths", {}).items():
            if path not in ["/health", "/api/v1/auth/login", "/api/v1/health"]:
                for method in methods.values():
                    if isinstance(method, dict):
                        method["security"] = [{"bearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # ========================================================================
    # CORS Configuration
    # ========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ========================================================================
    # Authentication Middleware
    # ========================================================================
    if settings.AUTH_ENABLED:
        print("✅ Authentication middleware enabled")
        app.add_middleware(
            AuthenticationMiddleware,
            excluded_paths=[
                "/health",
                "/docs",
                "/openapi.json",
                "/redoc",
                "/favicon.ico",
                "/api/v1/auth/login",
            ]
        )
    else:
        print("⚠️ Authentication middleware disabled")
    
    # ========================================================================
    # Routes - Health Check
    # ========================================================================
    
    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint (no auth required)"""
        return {
            "status": "ok",
            "service": "Travo Agent Solution",
            "auth_enabled": settings.AUTH_ENABLED,
            "version": "1.0.0"
        }
    
    # ========================================================================
    # Routes - Authentication & Authorization
    # ========================================================================
    app.include_router(
        auth_router,
        prefix="/api/v1",
        tags=["Authentication & Authorization"]
    )
    
    # ========================================================================
    # Error Handlers
    # ========================================================================
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for logging"""
        print(f"❌ Unhandled exception: {str(exc)}")
        print(f"   Path: {request.url.path}, Method: {request.method}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "status": 500
            }
        )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting Travo Agent Solution...")
    print(f"  - Host: 0.0.0.0")
    print(f"  - Port: 8000")
    print(f"  - Swagger UI: http://localhost:8000/docs")
    print(f"  - ReDoc: http://localhost:8000/redoc")
    print(f"  - Log Level: {settings.LOG_LEVEL}")
    print(f"  - Auth Enabled: {settings.AUTH_ENABLED}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
