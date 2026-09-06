"""
Configuration management for JARVIS Backend Brain.
Loads environment variables from .env with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Search for .env in current directory, backend directory, or project root
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
root_dir = backend_dir.parent

for env_path in [backend_dir / ".env", root_dir / ".env", current_dir / ".env"]:
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path)
        break
else:
    # If no specific .env found, trigger default load_dotenv
    load_dotenv()


class Settings:
    """Application runtime settings and configuration tokens."""

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    # Database
    # Default to a local SQLite database file in the project workspace
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jarvis.db")

    # LLM Provider Configuration
    # Supported: 'anthropic', 'openai', 'gemini', 'mock'
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    # Model names
    # Default Gemini: gemini-3.6-flash
    # Default Claude: claude-3-5-sonnet-20241022
    # Default OpenAI: gpt-4o
    LLM_MODEL: str = os.getenv(
        "LLM_MODEL",
        "gemini-3.6-flash" if LLM_PROVIDER == "gemini" else (
            "claude-3-5-sonnet-20241022" if LLM_PROVIDER == "anthropic" else "gpt-4o"
        )
    )

    # Conversation Memory
    # Total past messages (user + assistant) to include in LLM context window
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

    # System Persona
    SYSTEM_PROMPT: str = os.getenv(
        "SYSTEM_PROMPT",
        (
            "You are Jarvis, a personal AI assistant. "
            "Your tone is concise, direct, and sharp. "
            "You assist with daily tasks, programming, planning, and system administration. "
            "Avoid excessive flattery or conversational filler; focus on actionable, clear answers."
        )
    )


settings = Settings()
