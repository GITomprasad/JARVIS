# ⚡ JARVIS — Personal AI Operating System

<p align="center">
  <strong>A modular, multi-device personal AI assistant built to listen, reason, remember, and act.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLite-Memory-003B57?style=for-the-badge&logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/AI-Claude%20%7C%20OpenAI-purple?style=for-the-badge" alt="AI">
  <img src="https://img.shields.io/badge/Status-Stage%201%20MVP-success?style=for-the-badge" alt="Status">
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 🧠 Overview

**JARVIS** is a modular personal AI assistant designed to become a centralized intelligence layer across devices.

Instead of being just another chatbot, JARVIS is designed around a simple idea:

> **Understand → Remember → Reason → Act**

The system uses a central **FastAPI backend ("Brain")** that manages conversations, memory, LLM communication, and future device actions.

JARVIS currently supports:

- 🤖 Claude / OpenAI / Mock LLM providers
- 🧠 Persistent conversation memory
- 💬 Interactive laptop CLI
- 🌐 REST API
- 🗄️ SQLite-based storage
- 🔌 Modular service architecture
- 🧪 Automated testing with pytest
- 🔐 Environment-based secret management

The architecture is intentionally designed so that additional devices, tools, automation, and voice capabilities can be added without rewriting the core system.

---

# ✨ Features

### 🤖 Multi-LLM Architecture

JARVIS separates the assistant logic from the underlying AI provider.

Supported providers include:

- Anthropic Claude
- OpenAI
- Deterministic Mock Provider

This makes it possible to switch providers without changing the rest of the application.

---

### 🧠 Persistent Memory

JARVIS stores conversations using SQLite and SQLAlchemy.

The memory layer provides:

- Conversation persistence
- Session-based history
- Sliding-window context
- Conversation retrieval
- Memory reset functionality

Example:

```text
User
 ↓
"Remember that I'm working on a Python project."
 ↓
JARVIS
 ↓
Memory Service
 ↓
SQLite
