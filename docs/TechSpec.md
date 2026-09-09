# TechSpec: ARES Architecture

## 1. Architecture Overview
The ARES Minor Project adopts a decoupled, service-oriented architecture.
```
WEB UI (React) 
  ↓ REST / WebSockets
BACKEND (FastAPI / ARES Controller)
  ↓
POLICY / SCOPE GATEWAY
  ↓
AGENT LAYER
  ↓
LLM REASONER (LLMProvider Abstraction)
  ↓
TOOL GATEWAY (Safe execution boundary)
  ↓
HEXSTRIKE-AI (Adapter)
  ↓
CONTROLLED SECURITY TOOLS
  ↓
AUTHORIZED LAB TARGET
```

## 2. Frontend
- **Framework**: React 19 + TypeScript + Vite.
- **Styling**: Custom Vanilla CSS (Dark SOC Aesthetic) + Lucide Icons.
- **Routing**: React Router DOM.
- **State**: React Hooks, Fetch API for REST, native WebSockets for live streams.

## 3. Backend
- **Framework**: Python 3.14 + FastAPI.
- **Validation**: Pydantic v2.
- **Concurrency**: `asyncio` for non-blocking agent execution.

## 4. API Architecture
- **REST APIs**: For CRUD operations on Assessments, Findings, Reports, and System configs.
- **WebSockets**: For streaming real-time Agent ActivityLogs and Assessment Status updates.

## 5. Authentication & 6. Authorization
- **Minor Project**: Local lab mode (no strict auth required initially).
- **Major Project**: JWT-based authentication, Role-Based Access Control (RBAC) via middleware.

## 7. Database
- **Minor Project**: SQLite (using `aiosqlite` and `SQLAlchemy` async).
- **Major Project Migration Path**: SQLAlchemy ORM ensures easy migration to PostgreSQL.

## 8. Agent Architecture
Agents are Python modules orchestrated by the `AresController`.
- `PolicyAgent`: Enforces target allowlists.
- `ReconAgent`: Gathers environmental data.
- `AnalyzerAgent`: Synthesizes recon data.
- `LLMReasoner`: Evaluates findings using LLMs.
- `ValidationAgent`: Verifies findings.

## 9. LLM Architecture & 10. OmniRoute Integration
The system implements an abstract `LLMProvider` interface.
- **OmniRoute** is the default development provider using an OpenAI-compatible API interface.
- Configuration via environment variables: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
- Prevents hardcoding dependencies to a single vendor.

## 11. HexStrike-AI Integration & 12. Tool Gateway
- **HexStrike-AI** acts as the execution layer.
- **Tool Gateway**: A safe adapter layer ensuring that the frontend or LLM cannot execute arbitrary shell commands. It translates semantic intents (e.g., "scan ports") into constrained, parameterized HexStrike module calls.

## 13. Policy Gateway
- intercepts all requests to start assessments.
- Validates targets against allowed domains (localhost, 127.0.0.1).

## 14. Evidence System & 15. Findings System
- **Evidence**: Raw JSON or text outputs from HexStrike tools and LLM responses.
- **Findings**: Structured records detailing Vulnerability Title, Severity, Confidence, Reasoning, and Remediation.

## 16. Reporting System
- Aggregates findings and evidence into a final HTML or Markdown report upon assessment completion.

## 17. Memory Strategy
- **Minor Project**: Relational database persistence (Assessment state and Activity Logs).
- **Major Project**: Vector embeddings of previous exploits for cross-assessment context.

## 18. WebSocket / Live Updates
- FastAPI WebSocket endpoint per assessment ID. Broadcasts JSON payload containing agent status and log messages.

## 19. Logging & 20. Error Handling
- Structured Python logging.
- Global exception handlers in FastAPI to return standard JSON error formats.

## 21. Security Controls
- No `shell=True` in subprocesses.
- Restricted tool execution via predefined parameters.

## 22. Configuration & 23. Environment Variables
- `pydantic-settings` manages configuration from `.env`.
- Keys: `DATABASE_URL`, `LLM_API_KEY`, `ALLOWED_TARGETS`.

## 24. Docker & 25. Deployment
- **Minor Project**: Docker Compose with `backend` and `frontend` services.
- **Major Project**: Scalable Kubernetes deployment.

## 26. Testing Stack & 27. Development Tooling
- `pytest`, `pytest-asyncio`, `httpx` for backend.
- `npm run dev`, ESLint, Prettier for frontend.
