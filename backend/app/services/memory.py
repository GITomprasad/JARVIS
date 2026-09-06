"""
Conversation memory service.
Handles persistence and retrieval of historical chat messages from SQLite.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.message import Message


class MemoryService:
    """Manages conversational history and context windows."""

    @staticmethod
    def save_message(
        db: Session,
        session_id: str,
        role: str,
        content: str,
        device_id: Optional[str] = None
    ) -> Message:
        """Persist an individual message (user, assistant, system) to the database."""
        db_message = Message(
            session_id=session_id,
            role=role,
            content=content,
            device_id=device_id
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_recent_messages(
        db: Session,
        session_id: str,
        limit: int = 10,
        exclude_id: Optional[int] = None
    ) -> List[Message]:
        """
        Fetch the last N messages for a given session, ordered chronologically.
        If exclude_id is provided, skips that specific message (useful when we just saved the current user prompt).
        """
        query = db.query(Message).filter(Message.session_id == session_id)
        if exclude_id is not None:
            query = query.filter(Message.id != exclude_id)

        # Retrieve newest messages first, then reverse to chronological order
        recent_desc = query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit).all()
        return list(reversed(recent_desc))

    @staticmethod
    def get_all_session_messages(db: Session, session_id: str) -> List[Message]:
        """Fetch all historical messages for a given session in chronological order."""
        return (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .all()
        )

    @staticmethod
    def clear_session_history(db: Session, session_id: str) -> int:
        """Delete all messages belonging to a given session. Returns count of deleted messages."""
        deleted_count = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted_count
