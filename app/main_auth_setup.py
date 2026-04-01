"""
Example FastAPI setup with authentication and authorization
This file shows how to integrate the security system into your application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.auth_gateway import router as auth_router
from app.security.middleware import AuthenticationMiddleware
from app.config.settings import settings
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Application starting up...")
    yield
    logger.info("🛑 Application shutting down...")


def create_app():
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Travo Agent Solution",
        description="Multi-agent system with action-level authentication",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # ========================================================================
    # CORS Configuration
    # ========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ========================================================================
    # Authentication Middleware
    # ========================================================================
    if settings.AUTH_ENABLED:
        logger.info("✅ Authentication middleware enabled")
        app.add_middleware(
            AuthenticationMiddleware,
            excluded_paths=[
                "/health",
                "/api/v1/auth/login",
                "/api/v1/auth/register",
                "/docs",
                "/openapi.json",
                "/redoc",
                "/favicon.ico"
            ]
        )
    else:
        logger.warning("⚠️ Authentication middleware disabled")
    
    # ========================================================================
    # Routes
    # ========================================================================
    
    # Health check (no auth required)
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "ok",
            "service": "Travo Agent",
            "auth_enabled": settings.AUTH_ENABLED
        }
    
    # Include authentication routes
    app.include_router(
        auth_router,
        prefix="/api/v1",
        tags=["authentication"]
    )
    
    # Include other routers here
    # Example:
    # from app.api.agent_gateway import router as agent_router
    # app.include_router(agent_router, prefix="/api/v1", tags=["agents"])
    
    # ========================================================================
    # Error Handlers
    # ========================================================================
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for logging"""
        logger.error(f"Unhandled exception: {str(exc)}", extra={
            "path": request.url.path,
            "method": request.method,
        })
        return {
            "detail": "Internal server error",
            "status": 500
        }
    
    return app


# Create app instance
if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    
    logger.info(f"Starting Travo Agent Solution...")
    logger.info(f"  - Log Level: {settings.LOG_LEVEL}")
    logger.info(f"  - Auth Enabled: {settings.AUTH_ENABLED}")
    logger.info(f"  - Rate Limiting: {settings.RATE_LIMITING_ENABLED}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )
else:
    app = create_app()
