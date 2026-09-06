"""
Message table model for storing conversation history.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.app.database import Base


class Message(Base):
    """
    Represents an individual message exchanged between the user and Jarvis,
    or a system instruction.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False, default="default")
    device_id = Column(String(64), nullable=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, session={self.session_id}, role='{self.role}', created_at={self.created_at})>"
