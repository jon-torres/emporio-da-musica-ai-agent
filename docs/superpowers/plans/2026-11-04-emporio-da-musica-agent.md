# Empório da Música AI Customer Service Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-grade AI customer service agent for "Empório da Música" using Python and `uv`, supporting free-tier models (Gemini / Groq / Ollama / Mock) with dual CLI and Streamlit interfaces, structured database queries, policy RAG retrieval, persona guardrails, unit tests, and complete documentation.

**Architecture:** A modular ReAct / tool-calling agent with strict Pydantic schemas. Structured customer/catalog/order data is ingested from CSV into an indexed SQLite database for exact queries. Unstructured store policies from the PDF are extracted, chunked, and retrieved via a BM25/hybrid retriever. The agent features the Empório da Música persona, handles out-of-scope requests, maintains session memory, and provides both a Rich interactive CLI and a Streamlit chat UI.

**Tech Stack:** Python 3.11+, `uv`, `google-genai` / `litellm` / `httpx`, `pydantic`, `sqlite3`, `pypdf`, `rank-bm25`, `rich`, `streamlit`, `pytest`.

**Spec:** Technical challenge described in `desafio_tecnico_ai_eng_artefact.pdf` and store policy in `data/políticas_da_loja.pdf`.

---

### Task Breakdown

- [ ] **Task 1: Environment & Project Scaffolding with `uv` and Git**
  - Initialize git repository.
  - Initialize project with `uv init` / `pyproject.toml`, `.gitignore`, `.env.example`.
  - Add core dependencies (`pydantic`, `pydantic-settings`, `rich`, `streamlit`, `pypdf`, `rank-bm25`, `python-dotenv`, `google-genai`, `pytest`).
  - Set up `src/` layout with `emporio_agent` package.
  - Verify `uv sync` and run basic check.
  - Commit.

- [ ] **Task 2: Database Layer for Operational Data (CSVs -> SQLite)**
  - Parse CSVs (`categories.csv`, `products.csv`, `customers.csv`, `orders.csv`, `order_items.csv`, `promotions.csv`).
  - Create SQLite database schema with indexes and relationships.
  - Build query functions (`search_products(query, max_price, category, in_stock_only)`, `get_product_by_id`, `get_order_status(order_id_or_tracking)`, `get_active_promotions()`).
  - Write unit tests in `tests/test_database.py`.
  - Verify tests pass and commit.

- [ ] **Task 3: Policy Retrieval (RAG) Layer**
  - Implement PDF text extractor and semantic section chunker for `data/políticas_da_loja.pdf`.
  - Implement BM25 retriever with keyword matching and section tags (returns, warranty, shipping, store hours, payment methods).
  - Add deterministic query interface `query_policies(query: str, top_k: int = 3)`.
  - Write unit tests in `tests/test_rag.py`.
  - Verify tests pass and commit.

- [ ] **Task 4: Agent Core, Tools, Persona & Provider Abstraction**
  - Implement LLM provider abstraction supporting Google Gemini (free API tier via Google AI Studio), Groq / OpenRouter, local Ollama, and an offline Mock provider for automated tests and CI.
  - Define agent tools matching Pydantic schemas:
    - `search_catalog`
    - `get_product_details`
    - `check_order_status`
    - `consult_store_policies`
    - `get_store_info`
  - Implement system prompt defining the Empório da Música persona (friendly musical friend, Portuguese, strict factual grounding, polite redirect for accessories like cables/strings).
  - Implement memory & multi-turn message handling.
  - Write unit tests in `tests/test_agent.py`.
  - Verify tests pass and commit.

- [ ] **Task 5: User Interfaces (Rich CLI & Streamlit Web UI)**
  - Build interactive terminal CLI (`src/emporio_agent/cli.py`) with rich markdown rendering, spinner, session reset, and tool call inspection.
  - Build Streamlit chat interface (`src/emporio_agent/ui.py`) with side drawer showing retrieved context, order lookup helper, and quick suggested prompt buttons.
  - Add CLI entrypoint in `pyproject.toml` (`emporio-agent` and `emporio-ui`).
  - Verify both run smoothly and commit.

- [ ] **Task 6: Conversation Transcripts & Scenario Verification**
  - Generate and document 5 complete conversation transcripts in `examples/`:
    - `01_catalog_budget_search.md` ("Quais opções de violões disponíveis custando até R$1000?")
    - `02_store_info_and_hours.md` ("Qual o endereço da loja e horário de funcionamento?")
    - `03_price_and_specs_check.md` ("Quanto custa o Takamine GD20?")
    - `04_refund_policy_non_trivial.md` ("Me arrependi da minha compra, posso devolver meu pedido?")
    - `05_out_of_scope_redirection.md` ("Vocês vendem encordoamento de guitarra e pedal de distorção?")
  - Verify each scenario matches the manual rules and real CSV data.
  - Commit.

- [ ] **Task 7: Comprehensive Documentation (`README.md`) & Final Polish**
  - Write thorough `README.md` in Portuguese addressing every challenge deliverable:
    - Setup & running instructions with `uv`.
    - Technical justifications: framework/architecture, LLM choice (free tier Gemini/Groq), retrieval design, prompt engineering.
    - Known limitations & future roadmap ("o que você faria com mais tempo").
    - Transparent documentation of AI assistant workflow.
  - Run full test suite with `uv run pytest`.
  - Verify clean git commit history with descriptive messages.
