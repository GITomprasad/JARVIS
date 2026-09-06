"""
FastAPI Application Entry Point.
Initializes middleware, routers, database schemas, and application lifecycle.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.routers import chat_router, health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jarvis.brain")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager: handles startup and shutdown tasks."""
    logger.info("Initializing JARVIS Brain database schemas...")
    init_db()
    logger.info(
        "JARVIS Brain online. LLM Provider: %s | Model: %s",
        settings.LLM_PROVIDER,
        settings.LLM_MODEL
    )
    yield
    logger.info("JARVIS Brain shutting down.")


app = FastAPI(
    title="JARVIS Backend Brain",
    description="Central AI Brain for Personal Assistant across Laptop and Mobile",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for local cross-origin development (e.g. Flutter mobile or Web frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(chat_router)


@app.get("/", tags=["Root"])
def root_info():
    """Root endpoint welcoming clients and directing to interactive documentation."""
    return {
        "message": "JARVIS Brain is active.",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
        "chat_endpoint": "/chat"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
