"""
Chat endpoint routing and conversation orchestration.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageHistoryItem,
    SessionHistoryResponse,
)
from backend.app.services.memory import MemoryService
from backend.app.services.llm import get_llm_service, BaseLLMProvider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse, summary="Send a message to JARVIS")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Core conversation loop:
    1. Persists user prompt in SQLite.
    2. Retrieves sliding window of last N messages for conversation context.
    3. Calls LLM with history and Jarvis system persona.
    4. Persists Jarvis response in SQLite.
    5. Returns response and conversation metadata.
    """
    user_text = payload.message.strip()
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty."
        )

    session_id = payload.session_id.strip() or "default"
    device_id = payload.device_id.strip() if payload.device_id else "laptop"

    try:
        # 1. Store user message in SQLite
        user_message_record = MemoryService.save_message(
            db=db,
            session_id=session_id,
            role="user",
            content=user_text,
            device_id=device_id
        )

        # 2. Retrieve last N messages before the current one to feed into context
        # (Exclude the user message just saved to avoid duplicate when constructing the prompt)
        history_records = MemoryService.get_recent_messages(
            db=db,
            session_id=session_id,
            limit=settings.MAX_HISTORY_MESSAGES,
            exclude_id=user_message_record.id
        )

        history_for_llm = [
            {"role": msg.role, "content": msg.content}
            for msg in history_records
        ]

        # 3. Call LLM provider
        llm: BaseLLMProvider = get_llm_service()
        response_text = llm.generate_response(
            prompt=user_text,
            history=history_for_llm,
            system_prompt=settings.SYSTEM_PROMPT
        )

        # 4. Store assistant reply in SQLite
        assistant_message_record = MemoryService.save_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=response_text,
            device_id="jarvis_brain"
        )

        # 5. Return structured response
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            message_id=assistant_message_record.id,
            history_count=len(history_for_llm),
            provider=llm.provider_name
        )

    except Exception as e:
        logger.exception("Error in /chat endpoint processing: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating assistant response: {str(e)}"
        )


@router.get(
    "/history/{session_id}",
    response_model=SessionHistoryResponse,
    summary="Retrieve session message history"
)
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve full chronological conversation transcript for a session."""
    messages = MemoryService.get_all_session_messages(db, session_id=session_id)
    return SessionHistoryResponse(
        session_id=session_id,
        total_messages=len(messages),
        messages=[MessageHistoryItem.model_validate(m) for m in messages]
    )


@router.delete("/history/{session_id}", summary="Clear session memory")
def clear_session_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Clear conversation history for a given session (reset memory)."""
    deleted_count = MemoryService.clear_session_history(db, session_id=session_id)
    return {
        "status": "success",
        "session_id": session_id,
        "deleted_messages_count": deleted_count
    }
