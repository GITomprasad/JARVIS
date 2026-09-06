"""
Integration test suite for JARVIS Stage 1 MVP.
Tests FastAPI endpoints, SQLite memory persistence, and sliding-window context.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db

# Use an isolated SQLite database file for testing
TEST_DB_URL = "sqlite:///./test_jarvis.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Dependency override providing isolated test session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    """Create fresh schema before tests and cleanup afterwards."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    if os.path.exists("test_jarvis.db"):
        try:
            os.remove("test_jarvis.db")
        except OSError:
            pass


def test_root_endpoint():
    """Verify root endpoint responds with service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs_url" in data


def test_health_check():
    """Verify health diagnostics endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data
    assert "max_history_messages" in data


def test_empty_message_validation():
    """Ensure empty or whitespace-only messages are rejected with HTTP 400 or 422."""
    response = client.post("/chat", json={"message": "   ", "session_id": "test"})
    assert response.status_code in (400, 422)


def test_chat_memory_and_context():
    """
    Test core conversation flow:
    1. Send user introduction.
    2. Follow up asking for the remembered fact.
    3. Verify context was passed and persisted in SQLite.
    """
    session_id = "test_memory_session"

    # Step 1: First turn
    resp1 = client.post("/chat", json={
        "message": "Hello Jarvis, my name is Bruce Wayne.",
        "session_id": session_id,
        "device_id": "laptop"
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["session_id"] == session_id
    assert data1["history_count"] == 0  # No prior history for brand new session
    assert len(data1["response"]) > 0

    # Step 2: Second turn (should include previous exchange in history)
    resp2 = client.post("/chat", json={
        "message": "What is my name?",
        "session_id": session_id,
        "device_id": "laptop"
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    # The history should contain 2 messages: the user's first message and the assistant's reply
    assert data2["history_count"] == 2
    assert "Bruce" in data2["response"] or "Wayne" in data2["response"] or "remember" in data2["response"].lower()

    # Step 3: Inspect /history/{session_id}
    hist_resp = client.get(f"/history/{session_id}")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total_messages"] == 4  # 2 user prompts + 2 assistant responses
    assert hist_data["messages"][0]["role"] == "user"
    assert hist_data["messages"][1]["role"] == "assistant"
    assert hist_data["messages"][2]["role"] == "user"
    assert hist_data["messages"][3]["role"] == "assistant"


def test_session_isolation():
    """Verify conversations in different sessions remain strictly partitioned."""
    session_a = "session_alpha"
    session_b = "session_beta"

    # Send message to Session A
    client.post("/chat", json={"message": "I am in Alpha", "session_id": session_a})

    # Query Session B
    resp_b = client.post("/chat", json={"message": "Who am I?", "session_id": session_b})
    assert resp_b.status_code == 200
    # Session B should have 0 prior history
    assert resp_b.json()["history_count"] == 0

    hist_b = client.get(f"/history/{session_b}").json()
    assert hist_b["total_messages"] == 2


def test_clear_history():
    """Verify DELETE /history/{session_id} clears database records."""
    session_to_clear = "session_to_clear"
    client.post("/chat", json={"message": "Test clear", "session_id": session_to_clear})

    # Confirm exists
    assert client.get(f"/history/{session_to_clear}").json()["total_messages"] == 2

    # Clear
    del_resp = client.delete(f"/history/{session_to_clear}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_messages_count"] == 2

    # Confirm now empty
    assert client.get(f"/history/{session_to_clear}").json()["total_messages"] == 0
