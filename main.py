from fastapi import FastAPI
from app.api.gateway import router as gateway_router

app = FastAPI(title="Agentic Platform")

app.include_router(gateway_router, prefix="/api")
