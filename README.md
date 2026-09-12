# CodeBridge V1

**AI Code Architecture Interpreter & Plain-English Translation Studio**

CodeBridge V1 is an intelligent developer & product bridge designed for local WebUI execution. It ingests codebases from local directories or remote GitHub repositories, extracts concrete AST symbols and database schemas deterministically without hallucination, and translates logic flows into executive-ready business explanations and interactive Mermaid.js diagrams.

---

## 🌟 Key Capabilities

1. **3-Column Architect Studio**:
   - **Column 1 (Business Domain Explorer)**: Translates technical directories into intuitive business capabilities (e.g. `/src/auth` -> *Identity & Access Control*, `/src/billing` -> *Financial & Payment Processing*).
   - **Column 2 (Interactive Monaco Viewer)**: Line-by-line inspection with floating *"Translate in Plain English"* trigger and quick symbol jump.
   - **Column 3 (Translation & Visual Journey)**: 4-part executive breakdown + live Mermaid flowcharts, ER diagrams, and interactive Q&A assistant.

2. **Deterministic AST & Schema Extraction**:
   - **Prisma (`schema.prisma`)**: Models, fields, relations, enums, `@id`, `@relation`.
   - **SQL DDL (`.sql` / migrations)**: `CREATE TABLE`, primary keys, foreign keys.
   - **TypeScript ORM (Drizzle / TypeORM)**: `pgTable`, `mysqlTable`, column chains, relational links.
   - **Python & TypeScript Code**: Functions, classes, decorators, and FastAPI/Express route handlers.

3. **Universal OpenAI-Compatible Gateway**:
   - Hot-switch without restarts between **Local Ollama** (`localhost:11434`), **LM Studio**, **DeepSeek**, **OpenRouter**, or official **OpenAI**.
   - Built-in latency diagnostics and automated model discovery.

4. **Local SQLite Persistence**:
   - Ingested projects, extracted symbols, domain groupings, and generated translations are cached in WAL-mode SQLite (`data/codebridge.db`), providing sub-second repeat queries.

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**

### Installation

```bash
# 1. Clone or navigate to the repository
cd codebridge

# 2. Set up Python virtual environment & backend dependencies
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt

# 3. Install frontend & root orchestrator dependencies
cd frontend && npm install && cd ..
npm install
```

### Running CodeBridge

Launch both the FastAPI backend (`http://127.0.0.1:8000`) and the Vite frontend (`http://localhost:5173`) concurrently:

```bash
npm run dev
```

Open `http://localhost:5173` in your browser to start using CodeBridge.

---

## 🧪 Testing

Run both backend unit & integration tests and verify frontend production build:

```bash
npm test
```

Or test backend individually:

```bash
PYTHONPATH=. backend/.venv/bin/pytest backend/tests
```

---

## 📁 Project Architecture

- [`AGENTS.md`](./AGENTS.md) — Autonomous agent taxonomy, roles, SSE protocols, and prompt guardrails.
- [`DEVELOPMENT-PLAN.md`](./DEVELOPMENT-PLAN.md) — Comprehensive architectural plan and phased milestones.
- `backend/` — FastAPI application, SQLite persistence, Tree-sitter & AST parsers, LLM gateway.
- `frontend/` — React 18, Vite, TypeScript, Tailwind CSS, Monaco Editor, Mermaid.js.
- `examples/ecommerce-app/` — Sample multi-language repository fixture with Prisma schema and payment logic.
