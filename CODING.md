# Coding Guidelines & Backend Structure

This document outlines the coding patterns and project organization used in this e-commerce application.

---

## 1. Directory Structure

```text
Ecommerce_new/
├── ARCHITECTURE.md          # System architecture and flow
├── BRD.md                   # Business requirements & scope
├── CODING.md                # Code structure and patterns (this file)
├── UI_UX.md                 # Screen layouts and user journeys
├── .gitignore               # Protects .env, .venv, and build files
├── test_groq.py             # Temporary verification script for Groq integration
│
└── backend/
    ├── .env                 # Environment secrets (DATABASE_URL, SECRET_KEY, GROQ_API_KEY, GROQ_MODEL)
    ├── .venv/               # Python virtual environment
    ├── requirements.txt     # Python dependencies (includes langgraph, langchain-groq, langfuse)
    ├── database.py          # SQLAlchemy connection to Neon PostgreSQL
    ├── models.py            # SQLAlchemy database tables (User, Product, Cart, CartItem)
    ├── schemas.py           # Pydantic data validation models
    ├── auth.py              # Password hashing, JWT token creation & authentication
    ├── main.py              # FastAPI app setup, routes, and error handling
    └── agent/               # Agent foundation (LLM configuration & read-only access)
        ├── __init__.py      # Agent package exports
        ├── llm.py           # ChatGroq model factory (reads GROQ_API_KEY, GROQ_MODEL)
        ├── data_access.py   # Read-only data access (products, stock, cart)
        ├── flow.py          # LangGraph state graph flow for 'Ask the Store'
        └── tracing.py       # Langfuse tracing integration (timing, flow, Groq calls, DB steps)
```

---

## 2. Component Responsibilities

1. **`database.py`**:
   * Reads `DATABASE_URL` strictly from `backend/.env`.
   * Manages connection pool to Neon PostgreSQL.
   * Provides `get_db` generator for route dependencies.

2. **`models.py`**:
   * Defines database tables using SQLAlchemy Declarative Base.
   * Tables: `users`, `products`, `cart`, `cart_items`.

3. **`schemas.py`**:
   * Defines Pydantic models for request bodies and API responses.
   * Ensures data sent by client is validated before processing.

4. **`auth.py`**:
   * Hashes and verifies passwords using `bcrypt`.
   * Encodes and decodes JWT access tokens using `pyjwt`.
   * Reads `SECRET_KEY` strictly from `backend/.env`.
   * Provides `get_current_user` dependency for protected routes.

5. **`main.py`**:
   * Initializes FastAPI application and CORS middleware.
   * Hosts REST API endpoints (`/api/health`, `/api/auth/...`, `/api/products...`, `/api/cart...`, `/api/agent/ask`).

6. **`agent/llm.py`**:
   * Reads `GROQ_API_KEY` and `GROQ_MODEL` from `backend/.env`.
   * Creates and configures the `ChatGroq` model instance.
   * Never hard-codes or logs/prints the API key.

7. **`agent/data_access.py`**:
   * Provides a dedicated read-only layer for agent tools and operations.
   * Performs read-only queries for product catalog, pricing, and stock.
   * Performs read-only queries for the authenticated user's cart (no write mutations).
   * Reuses existing database models and authenticated user sessions.

8. **`agent/flow.py`**:
   * Implements the LangGraph StateGraph workflow for "Ask the Store".
   * Classifies user questions to confirm store relevance (products, prices, stock, user cart).
   * Routes non-store questions to a polite refusal without database lookups.
   * Fetches real read-only database data scoped strictly to the authenticated `user_id`.
   * Formats the context and prompts the Groq model to formulate accurate, factual answers without hallucinating numbers.

9. **`agent/tracing.py`**:
   * Reads `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST` from `backend/.env`.
   * Traces each agent execution with spans for intent classification, database reads, Groq generations, and answers.
   * Tags no-data and refused queries, and safely ignores credentials or tokens.

---

## 3. Core Coding Rules

* **Secrets Management**: Credentials (`DATABASE_URL`, `SECRET_KEY`, `GROQ_API_KEY`, `GROQ_MODEL`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`) must **never** be hardcoded or printed. Always load from `backend/.env`.
* **Single Backend**: FastAPI is the only backend. No Node.js or duplicate servers.
* **Agent Read-Only Isolation**: The agent data access layer strictly performs read operations (no INSERT, UPDATE, DELETE).
* **Simple & Reusable**: Prefer readable, standard Python over complex abstractions.
* **Error Handling**: Use standard `HTTPException` with clear status codes (`400 Bad Request`, `401 Unauthorized`, `404 Not Found`).
* **Authentication**: Use Bearer JWT tokens in the `Authorization: Bearer <token>` header for protected endpoints.


