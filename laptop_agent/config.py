"""
Laptop Agent client configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Check for .env in current, parent, or project root directory
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent

for env_path in [current_dir / ".env", root_dir / ".env", root_dir / "backend" / ".env"]:
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path)
        break
else:
    load_dotenv()


class AgentConfig:
    """Agent runtime settings."""
    BACKEND_URL: str = os.getenv("JARVIS_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    DEVICE_ID: str = os.getenv("JARVIS_DEVICE_ID", "laptop")
    DEFAULT_SESSION_ID: str = os.getenv("JARVIS_SESSION_ID", "default")


config = AgentConfig()
