# ARES — Automated RedTeaming Evaluation System

> A multi-agent web application security testing prototype for controlled laboratory environments and explicitly authorized assessment targets.

---

## Overview

**ARES** is a multi-agent, LLM-assisted web application security assessment prototype inspired by the research paper:

> *"A Multi-Agent Large Language Model Framework for Autonomous Web Application Penetration Testing."*

ARES demonstrates how specialized AI agents — orchestrated through a structured pipeline — collaborate to perform reconnaissance, vulnerability analysis, evidence collection, and HTML report generation against explicitly authorized targets in a controlled laboratory setting. ARES is not the same system as described in that paper; it is an independent research prototype inspired by its architectural concepts.

The **Minor release** (milestones 0–18) represents the complete baseline implementation: a fully operational multi-agent security pipeline with a real LLM reasoning layer (OmniRoute), a real security tool integration (HexStrike), a policy-enforced execution boundary, and a polished dark SOC web console with a live 3D visualization component.

---

## What ARES Currently Does

ARES runs a structured seven-stage assessment pipeline against an authorized target:

```
Target + Scope definition
    ↓
PolicyGateway — strict allowlist enforcement; blocks unauthorized targets before any agent runs
    ↓
ReconAgent — discovers endpoints, headers, and technology fingerprints via ToolGateway
    ↓
ToolGateway → ToolRegistry → HexStrikeAdapter → HexStrike-AI REST service
    ↓
AnalyzerAgent — synthesizes recon data into candidate vulnerabilities using LLM reasoning
    ↓
LLMProvider → OmniRouteProvider (OpenAI-compatible local inference proxy)
    ↓
ValidationAgent — re-evaluates findings to reduce false positives; assigns confidence levels
    ↓
EvidenceManager — persists structured findings, reasoning traces, and raw tool output
    ↓
ReportingService — compiles sanitized, XSS-escaped HTML reports from database state
```

Real-time activity is streamed to the dashboard over WebSockets throughout pipeline execution.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│              ARES Web Console (React 19 + Vite + TypeScript)     │
│  Dashboard · Assessments · Findings · Evidence · Reports ·       │
│  Agents · Architecture · Settings · 3D ARES Core Visualization   │
└───────────────────────┬──────────────────────────────────────────┘
                        │  REST API + WebSocket
┌───────────────────────▼──────────────────────────────────────────┐
│                     FastAPI Application                          │
│  /api/health · /api/dashboard · /api/assessments · /api/config   │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│                  AresController (Orchestrator)                    │
│  Async background task — manages pipeline state transitions      │
│  and broadcasts timestamped activity logs via WebSocket          │
└───────────────────────┬──────────────────────────────────────────┘
                        │
               ┌────────▼────────┐
               │  PolicyGateway  │  ← blocks all non-allowlisted targets
               └────────┬────────┘
                        │
          ┌─────────────▼──────────────┐
          │    Agent Framework          │
          │  BaseAgent · AgentRegistry  │
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │         ReconAgent          │
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────────────────────────┐
          │  ToolGateway → ToolRegistry → ToolAdapter       │
          │      HexStrikeAdapter  |  MockAdapter           │
          └─────────────┬──────────────────────────────────┘
                        │ ReconResult
          ┌─────────────▼──────────────┐
          │        AnalyzerAgent        │
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────────────────────┐
          │  LLMProvider → OmniRouteProvider / Mock    │
          └─────────────┬──────────────────────────────┘
                        │ AnalysisResult
          ┌─────────────▼──────────────┐
          │       ValidationAgent       │
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │    EvidenceManager          │  ← persists findings + raw traces
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │      ReportingService       │  ← generates sanitized HTML report
          └────────────────────────────┘
                        │
                   SQLite (data/ares.db)
```

---

## Core Components

| Component | Description |
|---|---|
| **AresController** | Background async orchestrator. Manages the seven-stage pipeline, persists state to SQLite, and broadcasts timestamped `ActivityLog` events over WebSocket. |
| **PolicyGateway** | Deterministic allowlist engine. Intercepts every assessment start and blocks any target not in `ALLOWED_TARGETS` before any agent or tool is invoked. |
| **Agent Framework** | `BaseAgent` abstract class with `AgentState` lifecycle, `AgentResult` data contract, and `AgentRegistry` for dynamic dispatch. |
| **PolicyAgent** | Agent-layer wrapper for policy checks integrated into the multi-agent framework. |
| **ReconAgent** | Domain agent that issues typed `ToolRequest` objects to the `ToolGateway` and parses responses into structured `ReconResult` payloads. |
| **AnalyzerAgent** | Builds structured prompts from `ReconResult` data and sends them to `LLMProvider`. Returns `AnalysisResultSchema` containing `CandidateFindingSchema` records with severity, confidence, and reasoning. |
| **LLMReasoner** | LLM-backed reasoning step wired into the controller pipeline for prioritization and planning. |
| **ValidationAgent** | Re-evaluates candidate findings, assigns `evidence_status`, and updates confidence levels to reduce false positives. |
| **LLMProvider / OmniRouteProvider** | Abstract model communication layer. `OmniRouteProvider` dispatches OpenAI-compatible completion requests to a local OmniRoute proxy (`LLM_BASE_URL`). `MockProvider` returns deterministic responses for automated tests. |
| **ToolGateway** | Secure adapter abstraction. Enforces capability allowlists, sanitizes all parameters, dispatches to registered adapters, and enforces per-call timeouts. Direct OS shell execution is strictly prohibited. |
| **HexStrikeAdapter** | REST client sending structured `ToolRequest` payloads to the HexStrike-AI service (`http://127.0.0.1:8888/api/v1/execute`). Live-verified against a real local DVWA target. |
| **MockAdapter** | Deterministic offline adapter used when `TOOL_PROVIDER=mock`. Enables full automated test coverage without any external service dependency. |
| **EvidenceManager** | Persists findings and raw tool output traces to SQLite, deduplicated by title and endpoint per assessment. |
| **ReportingService** | Compiles assessment summary, agent timeline, vulnerability findings table, and raw evidence traces into a sanitized, XSS-escaped HTML report. Accessible via `GET /api/assessments/{id}/report`. |

---

## Current Status

All Minor milestones (0–18) are complete and verified:

| Milestone | Description | Status |
|---|---|---|
| 0 | Workspace Audit & Documentation Freeze | Complete |
| 1 | Project Foundation | Complete |
| 2 | Backend Foundation | Complete |
| 3 | Database (SQLAlchemy async + SQLite) | Complete |
| 4 | Authentication & Authorization | Deferred to Major |
| 5 | Frontend Foundation | Complete |
| 6 | Assessment Management | Complete |
| 7 | ARES Controller | Complete |
| 8 | Agent Framework | Complete |
| 9 | Recon Agent | Complete |
| 10 | Analyzer Agent | Complete |
| 11 | LLM Abstraction + OmniRoute | Complete / Live Verified |
| 12 | Policy Gateway | Complete |
| 13 | Tool Gateway | Complete |
| 14 | HexStrike Integration | Complete / Live Verified |
| 15 | Evidence / Findings Persistence | Complete |
| 16 | Reporting Refinement | Complete |
| 17A | Design Toolchain Setup | Complete |
| 17B | ARES Core 3D Refinement | Complete |
| 18 | Comprehensive Testing | Complete |

---

## Integrations

### OmniRoute — Live Verified

OmniRoute is an OpenAI-compatible local proxy. The `OmniRouteProvider` sends completion requests to a locally running OmniRoute instance. Configuration is performed entirely via environment variables — no credentials are committed to the repository.

| Variable | Description |
|---|---|
| `LLM_PROVIDER` | `omniroute` for live inference; `mock` for deterministic offline testing |
| `LLM_BASE_URL` | Base URL of the local OmniRoute proxy |
| `LLM_API_KEY` | API key — supplied locally via `.env`, never committed |
| `LLM_MODEL` | Model identifier to request |

When `LLM_PROVIDER=mock`, the full test suite runs without any external LLM service.

### HexStrike — Live Verified

HexStrike-AI (v6.0.0) is a local security tool service. The `HexStrikeAdapter` dispatches structured HTTP POST requests to the HexStrike REST API and returns typed `ToolResult` payloads.

**Security posture:** HexStrike must remain bound strictly to `127.0.0.1:8888`. It must never be exposed on a public interface.

| Variable | Description |
|---|---|
| `TOOL_PROVIDER` | `hexstrike` for live tool execution; `mock` for deterministic testing |
| `HEXSTRIKE_BASE_URL` | Internal base URL of the local HexStrike service |
| `HEXSTRIKE_API_KEY` | API key — supplied locally via `.env`, never committed |

Live verification confirmed real HTTP 200 responses from a local DVWA installation, with real endpoint discovery, real HTTP headers captured, and real technology stack fingerprints (`PHP`, `Apache`, `MySQL`) identified. The full execution path `ReconAgent → ToolGateway → ToolRegistry → HexStrikeAdapter → HexStrike-AI → ToolResult → ReconResult → AnalyzerAgent` was verified operational.

---

## Frontend

The ARES web console is a dark SOC-aesthetic application built with React 19, Vite, and TypeScript.

**Pages:**

| Page | Description |
|---|---|
| **Dashboard** | Live system metrics, assessment activity feed, inline ARES Core 3D visualization |
| **Assessments** | Create and manage assessments; status-coded list view |
| **Assessment Detail** | Per-assessment pipeline stage view, real-time WebSocket activity log, explicit START button |
| **Findings** | Split-pane vulnerability browser with severity filtering |
| **Evidence** | Raw tool output and reasoning trace viewer |
| **Reports** | HTML report access for completed assessments |
| **Agents** | Connected agent topology graph |
| **Architecture** | Live architecture diagram rendered in the console |
| **Settings** | Environment configuration viewer |

**ARES Core 3D** (`frontend/src/components/ares-core/`) is a WebGL holographic intelligence visualization built with Three.js, React Three Fiber, Drei, and GSAP. It renders a central nucleus, interlocking orbital rings, distributed particle nodes, and a camera controller with cursor-parallax tracking. State-driven color shifts reflect the active pipeline stage.

> WebGL support is required for the 3D Core visualization.

---

## Project Structure

```
ares-minor/
├── backend/
│   ├── app/
│   │   ├── agents/          # AresController, BaseAgent, ReconAgent, AnalyzerAgent,
│   │   │                    # ValidationAgent, PolicyAgent, LLMReasoner, registry
│   │   ├── api/             # REST routes and WebSocket handler
│   │   ├── core/            # config.py, logging, error handling
│   │   ├── database/        # async SQLAlchemy engine and session
│   │   ├── llm/             # LLMProvider, OmniRouteProvider, MockProvider, factory
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── policy/          # PolicyGateway
│   │   ├── schemas/         # Pydantic v2 request/response schemas
│   │   ├── services/        # EvidenceManager, ReportingService
│   │   └── tools/
│   │       └── adapters/    # HexStrikeAdapter, MockAdapter, base
│   ├── tests/               # pytest suite
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── ares-core/   # AresCore, CoreScene, Nucleus, OrbitalSystem,
│   │   │                    # ParticleField, TopologySphere, IntelligenceNodes, ...
│   │   ├── pages/           # Dashboard, Assessments, Findings, Evidence,
│   │   │                    # Reports, Agents, Architecture, Settings, ...
│   │   └── services/        # API client abstraction
│   └── package.json
├── data/                    # SQLite database files (git-ignored)
├── docs/                    # PRD, TechSpec, AppFlow, Schema, Tracker, Rules
├── .env.example             # Environment variable template
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Environment Configuration

Create a local `.env` from the provided template. **Never commit this file.**

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and supply your local credentials. The default `mock` configuration is safe and functional for development and automated testing without any external services:

```ini
# LLM provider — use 'mock' to run without an external LLM service
LLM_PROVIDER=mock
LLM_BASE_URL=http://localhost:20128/v1
LLM_API_KEY=         # supply your OmniRoute key locally if using omniroute
LLM_MODEL=           # e.g. gpt-4o-mini

# Tool provider — use 'mock' to run without HexStrike
TOOL_PROVIDER=mock
HEXSTRIKE_BASE_URL=http://127.0.0.1:8888/api/v1
HEXSTRIKE_API_KEY=   # supply your HexStrike key locally if using hexstrike

# Authorized targets — only add hosts you are explicitly authorized to test
ALLOWED_TARGETS='["localhost","127.0.0.1","demo.local","http://localhost","http://127.0.0.1","http://demo.local"]'
```

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `GET http://localhost:8000/api/health`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in a WebGL-capable browser.

---

## Testing

The backend test suite requires no live external services when run in default mock mode.

```bash
cd backend
source venv/bin/activate
pytest
```

**Verified results (Milestone 18 — full suite):**

| Module | Result |
|---|---|
| Controller & WebSocket (Phase 7) | 55 passed, 1 skipped |
| Agent Framework (Phase 8) | 65 passed, 1 skipped |
| Analyzer Agent (Phase 10) | 84 / 84 passed |
| Policy Gateway (Phase 12) | 33 / 33 passed |
| Tool Gateway (Phase 13) | 37 / 37 passed |
| Evidence & Findings (Phase 15) | 43 / 43 passed |
| Reporting Service (Phase 16) | 44 / 44 passed |
| **Full suite (Phase 18)** | **131 passed, 0 failed, 1 skipped** |

Frontend build validation:

```bash
cd frontend
npm run build
```

---

## Safety and Responsible Use

**ARES must only be used against systems you own or have explicit written authorization to test.**

Acceptable targets in this Minor release:

- Your own intentionally vulnerable laboratory applications (e.g., a local DVWA installation)
- `localhost`, `127.0.0.1`, and explicitly authorized local hosts
- Other targets for which you hold verifiable authorization to conduct security testing

**The PolicyGateway is the primary enforcement control.** Any target URL not present in `ALLOWED_TARGETS` is rejected before any agent, tool adapter, or LLM is invoked. The pipeline transitions to `BLOCKED` state and no downstream execution occurs.

Additional constraints enforced by the implementation:

- No direct OS shell execution — all tool invocations pass through `ToolGateway`
- No `subprocess` calls with `shell=True` anywhere in the codebase
- HexStrike-AI is bound strictly to `127.0.0.1` (loopback only)
- API keys and credentials are loaded from `.env` and never logged or committed
- HTML reports are XSS-escaped before rendering
- All pipeline events produce immutable, timestamped `ActivityLog` records

---

## Current Limitations

| Limitation | Notes |
|---|---|
| **No authentication or RBAC** | Single-user local deployment only. Multi-tenant auth deferred to Major. |
| **Fixed target allowlist** | `ALLOWED_TARGETS` is configured statically in `.env`. |
| **Local service dependencies for live mode** | Live operation requires a running OmniRoute proxy and a locally bound HexStrike-AI instance. |
| **No PDF export** | Deferred to Major. HTML reports only. |
| **WebGL required** | The 3D Core visualization requires a WebGL-capable browser. |
| **Not for production deployment** | Research prototype; not designed for multi-user or public-facing environments. |
| **Controlled target scope** | Arbitrary public-internet scanning is blocked by the PolicyGateway and is not the intended use case for this release. |

---

## Roadmap — Major Release

The Major line is intended to evolve ARES toward:

- Iterative penetration testing loop (Recon → Hypothesis → Test → Observe → Re-reason)
- `PlannerAgent` and `ObservationAgent` for iterative next-action reasoning
- Specialist agents for broader vulnerability classes
- Security skill system for structured attack methodology
- Richer application and browser state modelling
- Stronger finding validation and attack chain construction
- Authentication, RBAC, and multi-user support
- Broader authorized target support with configurable scope policies

None of these capabilities are part of the frozen Minor baseline.

---

## Acknowledgements

ARES is an independent research prototype. Its architecture was inspired by:

> *"A Multi-Agent Large Language Model Framework for Autonomous Web Application Penetration Testing"*

ARES is not an official implementation of that paper, does not reproduce its experimental results, and may differ significantly from the system described therein.

---

## License

No open-source license is currently applied to this repository.

This is an academic/research prototype. Use is strictly limited to explicitly authorized laboratory and benchmark environments. The system must not be used for unauthorized access to computer systems. The authors accept no liability for misuse.
