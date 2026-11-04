# Empório da Música AI Customer Service Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-grade AI customer service agent for "Empório da Música" using Python and `uv`, supporting free-tier models (Gemini / Groq / Ollama / Mock) with dual CLI and Streamlit interfaces, structured database queries, policy RAG retrieval, persona guardrails, unit tests, and complete documentation.

**Architecture:** A modular ReAct / tool-calling agent with strict Pydantic schemas. Structured customer/catalog/order data is ingested from CSV into an indexed SQLite database for exact queries. Unstructured store policies from the PDF are extracted, chunked, and retrieved via a BM25/hybrid retriever. The agent features the Empório da Música persona, handles out-of-scope requests, maintains session memory, and provides both a Rich interactive CLI and a Streamlit chat UI.

**Tech Stack:** Python 3.11+, `uv`, `google-genai` / `litellm` / `httpx`, `pydantic`, `sqlite3`, `pypdf`, `rank-bm25`, `rich`, `streamlit`, `pytest`.

**Spec:** Technical challenge described in `desafio_tecnico_ai_eng_artefact.pdf` and store policy in `data/políticas_da_loja.pdf`.

---

### Task Breakdown

- [x] **Task 1: Environment & Project Scaffolding with `uv` and Git**
- [x] **Task 2: Database Layer for Operational Data (CSVs -> SQLite)**
- [x] **Task 3: Policy Retrieval (RAG) Layer**
- [x] **Task 4: Agent Core, Tools, Persona & Provider Abstraction**
- [x] **Task 5: User Interfaces (Rich CLI & Streamlit Web UI)**
- [x] **Task 6: Conversation Transcripts & Scenario Verification**
- [x] **Task 7: Comprehensive Documentation (`README.md`) & Final Polish**
