# PromptRank

**PromptRank** is a competitive platform (Codeforces-style) where contestants write system prompts to solve hidden challenges. Submissions are auto-evaluated across correctness, robustness, efficiency, and consistency, and players earn dynamic ELO-style ratings.

This repository contains the full stack application for PromptRank, including a FastAPI backend for evaluation and a Next.js frontend with a dark, performance-oriented UI.

---

## 🏗 System Architecture

The platform uses a scalable architecture built around high async throughput and isolated LLM evaluation.

*   **API Backend:** FastAPI (Python, async) — Handles auth, contest management, submissions, and leaderboard queries.
*   **Worker Service:** Celery + Redis — Fetches submissions and runs the N-sampling LLM evaluation loop in isolated environments.
*   **Database:** PostgreSQL (asyncpg) — Stores users, contests, problems, hidden testcases, submissions, and rating histories.
*   **Cache / Queue:** Redis — Backs the Celery queue and caches real-time leaderboards.
*   **Frontend:** Next.js (React + TypeScript) — Provides the web interface, including the Monaco-based prompt editor and submission dashboards.

## 🚀 Quick Start (Local Development)

The easiest way to run the full stack locally is via Docker Compose.

### Prerequisites
*   Docker & Docker Compose
*   Node.js v18+ (if running the frontend natively)
*   Python 3.12+ (if running the backend natively)

### Running with Docker Compose

1.  **Environment Setup**
    Copy the example environment file in the backend directory and configure your LLM Provider keys:
    ```bash
    cp backend/.env.example backend/.env
    ```
    *Make sure to add your `OPENAI_API_KEY` (or other provider) inside `backend/.env`.*

2.  **Start Services**
    From the root of the project, run:
    ```bash
    docker-compose up --build
    ```
    This will start:
    *   PostgreSQL database on port `5432`
    *   Redis server on port `6379`
    *   FastAPI backend on `http://localhost:8000`
    *   Celery worker processing submissions

3.  **Database Migrations**
    The backend uses Alembic for migrations. Once the database container is up, run migrations from the backend container/local env:
    ```bash
    cd backend
    alembic upgrade head
    ```

### Running the Frontend (Next.js)

If you are running the frontend locally via Node:

1.  Install dependencies:
    ```bash
    cd frontend
    npm install
    # or yarn install / pnpm install
    ```

2.  Run the development server:
    ```bash
    npm run dev
    ```
    Access the application at `http://localhost:3000`.

---

## 📚 Evaluation Metrics & Scoring

PromptRank evaluates each submission deterministically using fixed model parameters over `N` repeated runs. The Final Score (0–100) is a weighted aggregate of orthogonal dimensions:

*   **Accuracy (40%):** Correctness against ground truth, allowing numeric tolerances and partial field matches.
*   **Consistency (20%):** Stability of outputs across multiple runs (measuring variance and Jaccard similarity).
*   **Format Compliance (15%):** Strict adherence to the requested output schema (e.g., exact JSON keys and types).
*   **Token Efficiency (10%):** Normalized metric rewarding prompts that achieve correct outputs using fewer tokens.
*   **Robustness (10%):** Performance on a subset of adversarial testcases (noise, typos, language shifts).
*   **Latency (5%):** Average response time normalized across submissions.

## 🏆 Rating System

PromptRank implements a modified ELO rating system. Leaderboards update in real-time during contests based on the best submission score per user. After a contest ends, the Rating Engine computes expected vs. actual scores to calculate and persist ELO adjustments based on a variable K-factor (40 for new users, 20 for established).

## 🛡️ Security & Anti-Cheat

To ensure the integrity of the competitions, the platform enforces strict security rules:
*   Submissions are rate-limited (e.g., max 3 per contest problem).
*   Hidden test cases are rotated and randomized.
*   The worker environment disables tool calls and isolates network egress exclusively to allowed LLM APIs.
*   Backend anomaly detection flags similar prompt fingerprints and improbable success patterns.

---

## 🛠 Project Structure

```text
promptrank/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── routers/          # API endpoints (auth, contests, submissions, admin)
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── schemas.py        # Pydantic validation schemas
│   │   ├── database.py       # Async SQLAlchemy configuration
│   │   ├── auth.py           # JWT auth utilities
│   │   ├── llm/              # Custom LLM provider abstraction layer
│   │   └── worker.py         # Celery task definitions
│   ├── alembic.ini           # Alembic config
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend image build
├── frontend/
│   ├── src/                  # Next.js Application source
│   ├── package.json
│   └── next.config.mjs
└── docker-compose.yml        # Full stack orchestration
```

## 🤝 Contributing

When contributing to the codebase, adhere strictly to the established **Design Philosophy**:
*   **Backend:** Write asynchronous, non-blocking code. Use Type hints heavily. Never hardcode LLM provider logic; use the abstract `LLMProvider` interface.
*   **Frontend:** The UI should feel like a *serious IDE and compiler interface*, not a chat application. Maintain the dark, data-dense, distraction-free aesthetic. Adhere to the established CSS variables and design tokens.

---
*PromptRank — Measurable, Defensible, and Scalable Competitive Prompt Engineering.*
