"""
Health check and diagnostics endpoint.
"""

from fastapi import APIRouter
from backend.app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service health status")
def health_check():
    """Return backend status and active configuration metadata."""
    return {
        "status": "healthy",
        "service": "JARVIS Brain Backend",
        "version": "0.1.0",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "max_history_messages": settings.MAX_HISTORY_MESSAGES,
    }
