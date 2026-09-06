# ⚡ Personal JARVIS

> A modular, multi-device personal AI assistant running across desktop and mobile, powered by a central FastAPI backend "brain", SQLite conversation memory, and Claude/OpenAI LLM APIs.

---

## 📌 Architecture Overview

```
                        +----------------------------------------+
                        |        Central Backend "Brain"         |
                        |            (FastAPI / Python)          |
                        +----------------------------------------+
                               /            |             \
                              /             |              \
                             v              v               v
                +-----------------+  +--------------+  +------------------+
                | SQLite Database |  |  Memory Svc  |  |  LLM Provider    |
                |  (jarvis.db)    |  |  (Sliding    |  |  - Anthropic     |
                |                 |  |   Window N)  |  |  - OpenAI / Mock |
                +-----------------+  +--------------+  +------------------+
                             ^              ^
                             |              |
                    [REST: POST /chat, GET /history]
                             |              |
                +------------------+   +------------------+
                |   Laptop Agent   |   |    Mobile App    |
                | (CLI / Actions)  |   | (Flutter - S3)   |
                +------------------+   +------------------+
```

---

## 🏛️ Architectural Decisions & Trade-offs

### 1. Database: SQLite vs. PostgreSQL
- **Stage 1 & 2 Choice**: **SQLite** via SQLAlchemy.
  - *Pros*: Zero server setup, stored as a single file (`jarvis.db`), sub-millisecond local latency, trivial backups. Perfect for a single-user personal assistant.
  - *When to migrate to Postgres*: When scaling to multi-user access, or deploying the backend to serverless/container clouds (Render, AWS ECS, Fly.io) where persistent volume mounts are cumbersome compared to managed databases (e.g. Supabase, RDS).

### 2. Communication: REST vs. WebSockets
- **Stage 1 Choice**: **REST API** (`POST /chat`, `GET /history/{session_id}`).
  - *Pros*: Simple, stateless, easy to inspect with Swagger UI (`/docs`), curl, or any HTTP client.
  - *When WebSockets will be introduced (Stage 2 & 3)*: In Stage 2, when the backend needs to push structured action execution requests to the laptop agent asynchronously, and for token-by-token streaming responses.

### 3. LLM Provider Flexibility & Mock Mode
- Decoupled `BaseLLMProvider` abstraction supporting **Anthropic Claude (Sonnet)**, **OpenAI (GPT-4o)**, and a built-in deterministic **Mock Provider**.
- If no API key is provided, the system gracefully falls back to the Mock Provider, allowing immediate offline testing of the memory and client loop without crashing or incurring API charges.

---

## 📁 Project Structure

```
JARVIS/
├── backend/
│   ├── app/
│   │   ├── config.py              # Environment settings & persona prompt
│   │   ├── database.py            # SQLite engine & session management
│   │   ├── main.py                # FastAPI entry point, CORS, lifespan
│   │   ├── models/
│   │   │   └── message.py         # SQLAlchemy message model
│   │   ├── schemas/
│   │   │   └── chat.py            # Pydantic request/response validation
│   │   ├── services/
│   │   │   ├── llm.py             # Claude / OpenAI / Mock provider logic
│   │   │   └── memory.py          # Sliding-window context & persistence
│   │   └── routers/
│   │       ├── chat.py            # /chat, /history endpoints
│   │       └── health.py          # /health diagnostics endpoint
│   ├── requirements.txt           # Backend dependencies
│   └── .env.example               # Configuration template
├── laptop_agent/
│   ├── cli.py                     # Interactive rich terminal client
│   ├── config.py                  # Client configuration
│   └── requirements.txt           # Client dependencies
├── tests/
│   └── test_chat.py               # Automated pytest suite (6 tests)
├── .env                           # Active environment variables (gitignored)
├── .gitignore                     # Repository hygiene
└── README.md                      # Documentation
```

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows)
- (Optional) Anthropic Claude or OpenAI API key

### 1. Setup Environment
```bash
# Clone or open the repository
cd JARVIS

# Copy environment template
cp .env.example .env
```

Edit `.env` to configure your API keys:
```ini
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-5-sonnet-20241022
MAX_HISTORY_MESSAGES=10
```
*(If you leave `ANTHROPIC_API_KEY` empty, JARVIS automatically starts in Mock Mode for offline testing).*

### 2. Install Dependencies
```bash
python -m pip install -r backend/requirements.txt
python -m pip install -r laptop_agent/requirements.txt
```

### 3. Run Automated Tests
```bash
python -m pytest tests/ -v
```

### 4. Start the Backend Brain
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
- Interactive API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 5. Launch the Laptop Agent CLI
In a separate terminal:
```bash
python laptop_agent/cli.py
```

---

## 💬 CLI Client Commands

Within the CLI interface (`laptop_agent/cli.py`):
- `Your query` — Send natural language command to Jarvis
- `/history` — View the stored conversation transcript
- `/clear` — Reset conversation memory for the current session
- `/session <id>` — Switch between different sessions (e.g., `default`, `coding`, `planning`)
- `/help` — Display list of commands
- `/exit` — Quit client

---

## 🔒 Security & Safety Notes

- **Secrets Isolation**: API keys reside strictly in `.env`, excluded via `.gitignore`.
- **Local Data Sovereignty**: All conversation history is stored locally in SQLite (`jarvis.db`) on your machine.
- **Stage 2 Action Pre-Planning**: Ahead of Stage 2 (Local Actions), actions will be constrained by strict directory and executable whitelisting to avoid arbitrary destructive system commands.

---

## 🗺️ Project Roadmap

- [x] **Stage 1 — MVP**: FastAPI brain, SQLite conversation memory, Claude/OpenAI/Mock provider, laptop CLI agent.
- [ ] **Stage 2 — Local Actions**: Tool/function calling layer, desktop action executor (`open_app`, `run_script`, `search_files`), command whitelist & sandbox.
- [ ] **Stage 3 — Mobile App**: Flutter chat client, shared secret authentication, unified cross-device conversation continuation.
- [ ] **Stage 4 — Automations & Scheduling**: APScheduler background tasks, rule engine (`trigger -> action`), morning briefings and focus mode.
- [ ] **Stage 5 — Voice**: Modular Whisper speech-to-text and TTS voice pipeline.
