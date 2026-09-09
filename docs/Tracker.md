# ARES PROJECT MEMORY

**Project**: ARES-Based Web Application Penetration Testing Prototype  
**Project Type**: Minor Project  
**Purpose**: Controlled AI-assisted web application security assessment prototype for explicitly authorized targets.  
**Last Updated**: 2026-08-27  

### Core Technologies
- **Frontend**: React (v19), TypeScript, Vite, Three.js, React Three Fiber (@react-three/fiber), Drei (@react-three/drei), GSAP
- **Backend**: Python (3.14), FastAPI, Pydantic (v2), SQLAlchemy (Async), aiosqlite
- **AI Infrastructure**: LLMProvider, OmniRouteProvider, MockProvider
- **Security Orchestration**: PolicyGateway, ToolGateway, HexStrikeAdapter, HexStrike-AI (v6.0.0)
- **Storage**: SQLite (`data/ares.db`) via `aiosqlite`
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`

---

## Project Scope

### Minor Project Scope [IN SCOPE]
- Web dashboard (React) and Backend (FastAPI).
- Assessment lifecycle & management (CRUD, status flow).
- Controlled target validation & policy enforcement (`PolicyGateway`).
- Reconnaissance & discovery (`ReconAgent` via `ToolGateway` & `HexStrikeAdapter`).
- Structured vulnerability analysis (`AnalyzerAgent`).
- LLM reasoning abstraction (`LLMProvider` interfacing with `OmniRouteProvider`).
- Controlled tool gateway enforcing strict capability allowlists and parameter sanitization (`ToolGateway`).
- Live REST integration with HexStrike-AI service.
- Evidence collection & structured finding generation.
- Automated HTML report generation (`ReportingService`).
- Activity logging & real-time WebSocket updates.
- Polished, dark SOC web UI with 3D Holographic Intelligence Core.
- **Strict Constraint**: Operating EXCLUSIVELY against explicitly authorized, local laboratory targets (`http://localhost/DVWA/`, `127.0.0.1`, `demo.local`).

### Deferred Scope [MAJOR PROJECT / OUT OF SCOPE]
- Full ARES-RL / PPO model training & state reinforcement learning pipeline.
- Broad browser autonomy (Playwright / Selenium deep integration).
- Deep Burp Suite API integration (Extender APIs).
- Authentication, Multi-tenant RBAC, and multi-user access control.
- Public SaaS or large-scale Kubernetes production infrastructure.
- Advanced vector embeddings memory for cross-assessment learning.
- Unrestricted public-target scanning or autonomous exploitation.

---

## Architecture Memory

```
WEB UI (React + R3F 3D Core)
    ↓ REST / WebSockets
FastAPI (App Framework)
    ↓
AresController (Orchestrator)
    ↓
PolicyGateway (Scope & Target Authorization)
    ↓
Agent Framework (BaseAgent / AgentRegistry)
    ↓
ReconAgent (Reconnaissance Domain Agent)
    ↓
ToolGateway (Controlled Execution Boundary)
    ↓
ToolRegistry (Capability Mapper)
    ↓
ToolAdapter
    ↓
HexStrikeAdapter / MockAdapter
    ↓
ToolResult (Execution Artifact)
    ↓
ReconResult (Typed Schema)
    ↓
AnalyzerAgent (Vulnerability Synthesis)
    ↓
LLMProvider (Model Abstraction Layer)
    ↓
OmniRouteProvider / MockProvider (LLM Transport)
    ↓
AnalysisResult (Typed Vulnerability Candidates)
    ↓
Validation (ValidationAgent)
    ↓
Evidence (Evidence & Findings Persistence)
    ↓
ReportingService (HTML Report Rendering)
    ↓
Report (Final Artifact)
```

### Component Boundaries
- **AresController**: Manages background execution of the 7-stage pipeline, state transitions, and WebSocket log broadcasting.
- **PolicyGateway**: Intercepts all requests, strictly enforcing target allowlists (`ALLOWED_TARGETS`) and capability boundaries before any tool execution occurs.
- **ToolGateway**: Provides a secure adapter abstraction preventing direct shell execution. Sanitizes parameters and dispatches requests to registered adapters.
- **Agents (`ReconAgent`, `AnalyzerAgent`, `ValidationAgent`)**: Encapsulate domain reasoning and work without directly invoking raw operating system commands.
- **LLMProvider**: Handles abstract model communication (`OmniRouteProvider` for live inference, `MockProvider` for deterministic offline testing).
- **ReportingService**: Compiles persistent database state, findings, and evidence into sanitized HTML reports.

---

## Phase History (0 – 18)

### PHASE 0: Workspace Audit and Documentation Freeze
- **Status**: COMPLETE
- **Objective**: Freeze existing documentation and audit project structure.
- **What Was Implemented**: PRD, TechSpec, Schema, AppFlow, Design, Tracker, and Rules established in `docs/`.
- **Important Decisions**: Established documentation freeze before beginning Minor Project implementation.
- **Files Added**: `docs/PRD.md`, `docs/TechSpec.md`, `docs/AppFlow.md`, `docs/Design.md`, `docs/Schema.md`, `docs/ImplementationPlan.md`, `docs/Tracker.md`, `docs/Rules.md`.
- **Files Modified**: None.
- **Files Removed**: None.
- **Tests**: Documentation validation.
- **Manual Verification**: Inspected doc files for consistency.
- **Live Verification**: N/A (Documentation phase).
- **Known Limitations**: Static baseline.
- **Next Dependency**: Phase 1.

### PHASE 1: Project Foundation
- **Status**: COMPLETE / REAL
- **Objective**: Establish monorepo structure, FastAPI backend, and React Vite frontend foundation.
- **What Was Implemented**: Clean monorepo directory layout, environment configuration via `.env.example`.
- **Important Decisions**: Separated `backend/` and `frontend/` cleanly; centralized configuration via pydantic-settings.
- **Files Added**: `.env.example`, `backend/app/main.py`, `backend/app/core/config.py`, `frontend/package.json`, `frontend/vite.config.ts`.
- **Files Modified**: Root configuration files.
- **Files Removed**: Unused legacy scripts.
- **Tests**: Initial app boot check.
- **Manual Verification**: Backend startup via uvicorn, frontend startup via vite.
- **Live Verification**: Verified environment variable loading.
- **Known Limitations**: Basic scaffolding.
- **Next Dependency**: Phase 2.

### PHASE 2: Backend Foundation
- **Status**: COMPLETE / REAL
- **Objective**: Set up core FastAPI routing, structured logging, CORS, and `/health` endpoint.
- **What Was Implemented**: Centralized exception handling, CORS middleware, system health check route.
- **Important Decisions**: Allowed CORS for local frontend ports (`5173`, `3000`).
- **Files Added**: `backend/app/api/health.py`, `backend/app/core/logging.py`, `backend/app/core/errors.py`.
- **Files Modified**: `backend/app/main.py`.
- **Files Removed**: None.
- **Tests**: Health check pytest (`test_health.py`).
- **Manual Verification**: `GET /api/v1/health` returning `200 OK`.
- **Live Verification**: Live REST endpoint response verified.
- **Known Limitations**: No authentication layer (deferred to Major).
- **Next Dependency**: Phase 3.

### PHASE 3: Database Foundation
- **Status**: COMPLETE / REAL
- **Objective**: Implement async SQLite engine and SQLAlchemy ORM models.
- **What Was Implemented**: `Assessment`, `Finding`, `ActivityLog`, and `Report` database schemas with UUID primary keys and JSON state columns.
- **Important Decisions**: SQLite with `aiosqlite` chosen for Minor scope; ORM structured for future PostgreSQL migration.
- **Files Added**: `backend/app/db/session.py`, `backend/app/models/assessment.py`, `backend/app/models/finding.py`, `backend/app/models/activity_log.py`, `backend/app/models/report.py`.
- **Files Modified**: `backend/app/core/config.py`.
- **Files Removed**: None.
- **Tests**: Database model unit tests (`test_db.py`).
- **Manual Verification**: Table creation and async session initialization.
- **Live Verification**: Verified SQLite database file auto-creation in `data/ares.db`.
- **Known Limitations**: SQLite single-writer lock; no migration tool (Alembic) required for prototype.
- **Next Dependency**: Phase 5.

### PHASE 4: Authentication & Authorization
- **Status**: DEFERRED TO MAJOR
- **Objective**: Multi-tenant RBAC and JWT authentication.
- **What Was Implemented**: Deferred. Single-user local lab deployment mode active.
- **Important Decisions**: Excluded from Minor scope to focus on multi-agent tool orchestration safety.
- **Files Added**: None.
- **Files Modified**: None.
- **Files Removed**: None.
- **Tests**: N/A.
- **Manual Verification**: N/A.
- **Live Verification**: N/A.
- **Known Limitations**: Single-user local access only.
- **Next Dependency**: Phase 5.

### PHASE 5: Frontend Foundation
- **Status**: COMPLETE / REAL
- **Objective**: Establish React routing, UI shell, dark SOC CSS framework, and API client.
- **What Was Implemented**: AppShell navigation, dark CSS variables, API client abstraction, backend connectivity indicator.
- **Important Decisions**: Custom Vanilla CSS adopted for total aesthetic control and high-performance dark theme.
- **Files Added**: `frontend/src/components/AppShell.tsx`, `frontend/src/api/client.ts`, `frontend/src/index.css`.
- **Files Modified**: `frontend/src/App.tsx`.
- **Files Removed**: Default Vite demo files.
- **Tests**: `npm run build` static verification.
- **Manual Verification**: Browser inspection of UI shell and active connectivity indicator.
- **Live Verification**: Frontend successfully communicates with backend health API.
- **Known Limitations**: Initial basic layout before Phase 17 redesign.
- **Next Dependency**: Phase 6.

### PHASE 6: Assessment Management
- **Status**: COMPLETE / REAL
- **Objective**: Provide REST CRUD endpoints and Dashboard UI for managing assessments.
- **What Was Implemented**: Endpoints (`POST /assessments`, `GET /assessments`, `GET /assessments/{id}`), New Assessment form with ethical testing scope warning, Dashboard listing.
- **Important Decisions**: Pydantic schemas enforce required fields (name, target, scope).
- **Files Added**: `backend/app/api/assessments.py`, `backend/app/schemas/assessment.py`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/NewAssessment.tsx`.
- **Files Modified**: `frontend/src/App.tsx`.
- **Files Removed**: None.
- **Tests**: Assessment API pytest suite (`test_assessments.py`).
- **Manual Verification**: Created and listed assessments via UI.
- **Live Verification**: Persistence confirmed in SQLite database.
- **Known Limitations**: Manual stop/cancel requires controller integration.
- **Next Dependency**: Phase 7.

### PHASE 7: ARES Controller
- **Status**: COMPLETE / REAL
- **Objective**: Implement background task orchestrator for the 7-stage assessment pipeline.
- **What Was Implemented**: `AresController` class managing pipeline lifecycle (`POLICY_CHECK`, `RECON`, `ANALYSIS`, `LLM_REASONING`, `VALIDATION`, `EVIDENCE`, `REPORTING`), WebSocket manager for real-time log streaming.
- **Important Decisions**: Pipeline runs asynchronously via `asyncio.create_task`; status and stage data updated in DB per step.
- **Files Added**: `backend/app/agents/controller.py`, `backend/app/api/websockets.py`.
- **Files Modified**: `backend/app/main.py`.
- **Files Removed**: None.
- **Tests**: Controller unit & pipeline tests (55 passed, 1 skipped).
- **Manual Verification**: Triggered pipeline from UI and watched WebSocket stream updates.
- **Live Verification**: Verified async pipeline state transitions and WebSocket log broadcasts.
- **Known Limitations**: Mock agent stages initially used.
- **Next Dependency**: Phase 8.

### PHASE 8: Agent Framework
- **Status**: COMPLETE / REAL
- **Objective**: Create object-oriented multi-agent framework with standardized interfaces.
- **What Was Implemented**: `BaseAgent` abstract class, `AgentState` lifecycle, `AgentResult` data contract, `AgentException` error model, `AgentRegistry`.
- **Important Decisions**: Enforced strict input/output contracts for all agent subclasses.
- **Files Added**: `backend/app/agents/base.py`, `backend/app/agents/registry.py`, `backend/app/schemas/agent.py`.
- **Files Modified**: `backend/app/agents/controller.py`.
- **Files Removed**: None.
- **Tests**: Agent framework pytest suite (65 passed, 1 skipped).
- **Manual Verification**: Agent initialization and state registration verified.
- **Live Verification**: Verified agent lifecycle transitions during execution.
- **Known Limitations**: Domain agents required concrete tool bindings.
- **Next Dependency**: Phase 9.

### PHASE 9: Recon Agent
- **Status**: COMPLETE / REAL
- **Objective**: Implement reconnaissance domain agent interfacing with ToolGateway.
- **What Was Implemented**: `ReconAgent` class generating structured `ToolRequest` objects for capability `ActionCapability.RECON`, parsing tool outputs into typed `ReconResult`.
- **Important Decisions**: Decoupled `ReconAgent` from direct adapter execution—all tool invocations pass strictly through `ToolGateway`.
- **Files Added**: `backend/app/agents/recon_agent.py`, `backend/app/schemas/recon.py`.
- **Files Modified**: `backend/app/agents/controller.py`, `backend/app/agents/registry.py`.
- **Files Removed**: Legacy mock recon generator.
- **Tests**: ReconAgent unit tests (`test_recon_agent.py`).
- **Manual Verification**: Verified `ReconAgent` produces valid `ReconResult` schemas from tool adapters.
- **Live Verification**: Verified execution boundary via `ToolGateway`.
- **Known Limitations**: Default mock adapter used when `TOOL_PROVIDER=mock`.
- **Next Dependency**: Phase 10.

### PHASE 10: Analyzer Agent
- **Status**: COMPLETE / REAL
- **Objective**: Synthesize recon data into candidate findings using `LLMProvider`.
- **What Was Implemented**: `AnalyzerAgent.analyze()` accepting typed `ReconResult`, building structured prompt via `build_analyzer_user_prompt()`, returning `AnalysisResultSchema` with `CandidateFindingSchema` (including `evidence_status`).
- **Important Decisions**: Analyzer builds prompt exclusively from `ReconResult.to_controller_dict()` without hardcoding data; carries analysis provenance.
- **Files Added**: `backend/app/agents/analyzer_agent.py`, `backend/app/schemas/analysis.py`, `backend/app/prompts/analyzer.py`.
- **Files Modified**: `backend/app/agents/controller.py`.
- **Files Removed**: Legacy raw dict analysis parser.
- **Tests**: 34 new Phase 10 tests + updated existing suite (All 84/84 passing).
- **Manual Verification**: Verified prompt construction and JSON response parsing.
- **Live Verification**: Verified analyzer execution flow within `AresController`.
- **Known Limitations**: Relies on underlying `LLMProvider` selection.
- **Next Dependency**: Phase 11.

### PHASE 11: LLM Abstraction + OmniRoute Integration
- **Status**: LIVE VERIFIED
- **Objective**: Build extensible `LLMProvider` abstraction supporting live OmniRoute inference and Mock fallbacks.
- **What Was Implemented**: `LLMProvider` base class, `OmniRouteProvider` (OpenAI-compatible client pointing to `LLM_BASE_URL`), `MockProvider` for deterministic testing.
- **Important Decisions**: OmniRoute configured via environment variables (`LLM_BASE_URL=http://localhost:20128/v1`, `LLM_API_KEY`, `LLM_MODEL`).
- **Files Added**: `backend/app/llm/base.py`, `backend/app/llm/omniroute.py`, `backend/app/llm/mock.py`, `backend/app/llm/factory.py`.
- **Files Modified**: `backend/app/core/config.py`, `backend/app/agents/analyzer_agent.py`.
- **Files Removed**: Direct LLM client hardcoding.
- **Tests**: LLM provider unit and integration tests (`test_llm.py`).
- **Manual Verification**: Verified real OmniRoute API request/response cycle.
- **Live Verification**: Live OmniRoute request/response verified during full pipeline run.
- **Known Limitations**: Local OmniRoute instance must be running for live mode.
- **Next Dependency**: Phase 12.

### PHASE 12: Policy Gateway
- **Status**: COMPLETE / REAL
- **Objective**: Implement policy gateway enforcing strict target allowlists and scope restrictions.
- **What Was Implemented**: `PolicyGateway` enforcing target allowlist (`ALLOWED_TARGETS`), capability restrictions, and scope boundary checks.
- **Important Decisions**: Any target not present in `ALLOWED_TARGETS` is immediately rejected before agent allocation; pipeline state transitions to `BLOCKED`.
- **Files Added**: `backend/app/policy/gateway.py`, `backend/app/schemas/policy.py`.
- **Files Modified**: `backend/app/agents/controller.py`.
- **Files Removed**: Basic inline target regex check.
- **Tests**: Policy Gateway unit & edge case tests (All 33/33 passing).
- **Manual Verification**: Tested authorized (`http://localhost`) vs unauthorized (`https://example.com`) targets.
- **Live Verification**: Confirmed unauthorized targets are blocked at runtime without hitting downstream agents.
- **Known Limitations**: Fixed domain/IP allowlist; dynamic wildcard subdomains require configuration update.
- **Next Dependency**: Phase 13.

### PHASE 13: Tool Gateway
- **Status**: COMPLETE / REAL
- **Objective**: Build safe execution abstraction layer wrapping all security tool adapters.
- **What Was Implemented**: `ToolGateway`, `ToolRegistry`, typed `ToolRequest` and `ToolResult` schemas, parameter sanitization, and timeout management.
- **Important Decisions**: Subprocess execution with `shell=True` is strictly forbidden; capability mapping dynamically resolves `TOOL_PROVIDER`.
- **Files Added**: `backend/app/tools/gateway.py`, `backend/app/tools/registry.py`, `backend/app/tools/adapters/base.py`, `backend/app/tools/adapters/mock.py`, `backend/app/schemas/tools.py`.
- **Files Modified**: `backend/app/core/config.py`.
- **Files Removed**: Direct command invocation helpers.
- **Tests**: Tool Gateway test suite (All 37/37 passing).
- **Manual Verification**: Executed mock tool adapters through gateway.
- **Live Verification**: Confirmed gateway captures duration, errors, and structured output deterministically.
- **Known Limitations**: Must register adapters explicitly per capability in `ToolRegistry`.
- **Next Dependency**: Phase 14.

### PHASE 14: HexStrike Integration
- **Status**: LIVE VERIFIED
- **Objective**: Connect `ToolGateway` to live local HexStrike-AI REST service.
- **What Was Implemented**: `HexStrikeAdapter` communicating with HexStrike REST API (`/api/v1/execute`), dedicated virtual environment (`hexstrike_env`) hosting HexStrike-AI (v6.0.0) bound privately to `127.0.0.1:8888`.
- **Important Decisions**: Bound HexStrike strictly to `127.0.0.1:8888` for lab security; integrated via REST client `httpx` with timeout handling (`HEXSTRIKE_UNAVAILABLE`, `HEXSTRIKE_TIMEOUT`).
- **Files Added**: `backend/app/tools/adapters/hexstrike.py`, `backend/manual_tool_verify.py`.
- **Files Modified**: `backend/app/tools/registry.py`, `backend/app/core/config.py`.
- **Files Removed**: None.
- **Tests**: Adapter connectivity tests and live manual verification script.
- **Manual Verification**: Verified live HTTP POST request to `127.0.0.1:8888/api/v1/execute` returning HTTP 200 with real scan data.
- **Live Verification**: Full live path verified (`ReconAgent → ToolGateway → ToolRegistry → HexStrikeAdapter → Real HexStrike API → ToolResult → ReconResult → AnalyzerAgent`).
- **Known Limitations**: Requires HexStrike process running locally on port 8888.
- **Next Dependency**: Phase 15.

### PHASE 15: Evidence & Findings Persistence
- **Status**: COMPLETE / REAL
- **Objective**: Connect live LLM reasoning and tool output traces to persistent SQLite database storage.
- **What Was Implemented**: Automatic finding generation with severity, confidence, reasoning, and endpoint tracking; raw evidence JSON persistence.
- **Important Decisions**: Findings mapped to `Finding` ORM model; deduplicated by title and endpoint per assessment.
- **Files Added**: `backend/app/services/finding_service.py`, `backend/app/services/evidence_service.py`.
- **Files Modified**: `backend/app/agents/controller.py`, `backend/app/models/finding.py`.
- **Files Removed**: Hardcoded sample finding generators.
- **Tests**: Evidence and finding persistence pytest suite (All 43/43 passing).
- **Manual Verification**: Inspected database records in `ares.db` after assessment completion.
- **Live Verification**: Verified stored findings and activity logs match runtime execution artifacts.
- **Known Limitations**: Finding status transitions default to `Open`.
- **Next Dependency**: Phase 16.

### PHASE 16: Reporting Refinement
- **Status**: COMPLETE / REAL
- **Objective**: Build standalone HTML report generation service compiling persistent assessment data.
- **What Was Implemented**: `ReportingService` producing comprehensive, XSS-escaped HTML reports containing assessment summary, policy status, agent timeline, vulnerability findings table, and raw evidence traces.
- **Important Decisions**: Extracted report formatting from controller into dedicated service module.
- **Files Added**: `backend/app/services/reporting_service.py`.
- **Files Modified**: `backend/app/api/assessments.py`, `backend/app/models/report.py`.
- **Files Removed**: Inline report string template in controller.
- **Tests**: Reporting service unit & HTML rendering tests (All 44/44 passing).
- **Manual Verification**: Opened generated HTML reports in web browser; verified structure and escaping.
- **Live Verification**: `GET /api/v1/assessments/{id}/report` serves live generated HTML artifact.
- **Known Limitations**: Markdown export optional; PDF rendering deferred to Major.
- **Next Dependency**: Phase 17A.

### PHASE 17A: Design Toolchain Setup
- **Status**: COMPLETE
- **Objective**: Install 3D and animation dependencies for UI redesign.
- **What Was Implemented**: Installed Three.js, React Three Fiber, Drei, GSAP, and design skills (`ui-ux-pro-max`, `design-taste-frontend`, `design-dna`, `impeccable`, `emil-design-eng`, `3d-web-experience`).
- **Important Decisions**: Selected R3F + GSAP stack for responsive 3D intelligence visualization.
- **Files Added**: `frontend/src/components/canvas/` directory structure.
- **Files Modified**: `frontend/package.json`.
- **Files Removed**: None.
- **Tests**: `npm run build` validation.
- **Manual Verification**: Confirmed WebGL context rendering in browser.
- **Live Verification**: Frontend builds without dependency conflicts.
- **Known Limitations**: Toolchain setup only; visual components built in Phase 17B.
- **Next Dependency**: Phase 17B.

### PHASE 17B: ARES UI/UX Redesign & Visual Identity
- **Status**: COMPLETE
- **Objective**: Implement 3D Holographic Intelligence Core and dark SOC visual identity.
- **What Was Implemented**: 3D Holographic Intelligence Core (`AresCore3D`), inline metric rails replacing generic KPI cards, split-pane Findings viewer, connected Agents topology graph, GSAP motion system.
- **Important Decisions**: Accepted visual direction for Minor scope: restrained, technical, dark SOC aesthetic with dynamic state-driven 3D Core.
- **Files Added**: `frontend/src/components/canvas/AresCore3D.tsx`, `frontend/src/components/canvas/Nucleus.tsx`, `frontend/src/components/canvas/OrbitalRings.tsx`, `frontend/src/components/canvas/ParticleField.tsx`, `frontend/src/pages/Architecture.tsx`.
- **Files Modified**: `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/AssessmentDetail.tsx`, `frontend/src/pages/Findings.tsx`, `frontend/src/pages/Agents.tsx`, `frontend/src/components/AppShell.tsx`.
- **Files Removed**: Generic CSS card templates.
- **Tests**: `npm run build` succeeds cleanly.
- **Manual Verification**: Full interactive testing of 3D Core, smooth zoom, state transitions, and responsive layout across pages.
- **Live Verification**: Live WebGL 3D canvas rendering and real-time state synchronization verified in browser.
- **Known Limitations**: Requires WebGL-enabled browser.
- **Next Dependency**: Phase 18.

### PHASE 18: Comprehensive End-to-End Testing
- **Status**: COMPLETE / REAL
- **Objective**: Conduct comprehensive E2E pipeline verification and backend/frontend test suite validation.
- **What Was Implemented**: Full E2E pipeline execution testing (Policy → Recon → Analysis → Reasoning → Evidence → Reporting), regression test suite pass.
- **Important Decisions**: Verified all component contracts end-to-end under controlled laboratory conditions.
- **Files Added**: `backend/tests/test_e2e_pipeline.py`.
- **Files Modified**: `backend/tests/conftest.py`.
- **Files Removed**: Obsolete prototype test stubs.
- **Tests**: All backend pytests passing; frontend build clean.
- **Manual Verification**: Completed end-to-end test assessment via UI and verified persistence.
- **Live Verification**: Full pipeline validated under controlled environment settings.
- **Known Limitations**: Cold-start environment persistence pending final startup verification.
- **Next Dependency**: Final Cold-Start Configuration Verification.

---

## HexStrike Environment

- **Service Name**: HexStrike-AI (v6.0.0)
- **Binding Address**: `127.0.0.1` (Strictly local loopback interface)
- **Port**: `8888`
- **Base URL Endpoint**: `http://127.0.0.1:8888/api/v1`
- **Security Posture**: LOCAL / PRIVATE LAB ONLY. Never bind to `0.0.0.0`, never expose port 8888 to public interfaces, never configure router port forwarding.
- **Adapter Location**: [hexstrike.py](file:///home/sabby/Projects/ares-prototype/backend/app/tools/adapters/hexstrike.py)
- **ARES Invocation Path**:
  ```
  ReconAgent
      ↓ (generates ToolRequest)
  ToolGateway
      ↓ (validates capability & parameters)
  ToolRegistry
      ↓ (maps ActionCapability.RECON to HexStrikeAdapter)
  HexStrikeAdapter
      ↓ (HTTP POST to http://127.0.0.1:8888/api/v1/execute)
  HexStrike-AI REST Service
      ↓ (executes constrained security tool module)
  ToolResult
      ↓ (returned to ToolGateway)
  ReconResult (Structured payload returned to ReconAgent)
  ```
- **Verified Target**: `http://localhost/DVWA/` (Damn Vulnerable Web Application local installation)
- **Verified Result Characteristics**:
  - Real endpoints observed in target response payload
  - Real HTTP headers captured
  - Real technology stack signatures identified (PHP, Apache, MySQL)
  - `execution_mode` = `REAL`
  - Provenance source explicitly indicates HexStrike-backed execution

> [!IMPORTANT]
> HexStrike must ALWAYS remain bound strictly to `127.0.0.1`. Never prompt or configure an AI agent to perform unauthorized scans or target any public domain.

---

## OmniRoute Environment

- **Architecture**: `LLMProvider` abstraction -> `OmniRouteProvider` -> OmniRoute Local Proxy -> LLM Model
- **Configuration Variables**:
  - `LLM_PROVIDER`: `omniroute` (or `mock` for deterministic test mode)
  - `LLM_BASE_URL`: `http://localhost:20128/v1`
  - `LLM_API_KEY`: Configured via `.env` (never hardcoded)
  - `LLM_MODEL`: Configured via `.env` (e.g. `auto/best-reasoning` or `gpt-4o-mini`)
- **Phase 11 Verification Status**: LIVE VERIFIED
- **Agent Invocation Path**:
  ```
  AnalyzerAgent
      ↓ (prepares prompt from ReconResult)
  LLMProvider (Interface)
      ↓ (resolves active provider)
  OmniRouteProvider
      ↓ (HTTP POST OpenAI-compatible completion request)
  OmniRoute Local Proxy (http://localhost:20128/v1)
      ↓
  Structured AnalysisResult (Candidate findings with reasoning & confidence)
  ```

---

## Non-Negotiable Security Rules

1. **Explicit Target Authorization**: Assessments MUST ONLY target explicitly authorized local laboratory environments (`localhost`, `127.0.0.1`, `demo.local`, `http://localhost/DVWA/`). Public domains are strictly forbidden.
2. **PolicyGateway Enforcement**: `PolicyGateway` must NEVER be bypassed. All target URLs and capabilities must be evaluated prior to agent dispatch.
3. **ToolGateway Abstraction**: Agents must NEVER execute direct OS shell commands or invoke adapters directly. All execution must flow through `ToolGateway`.
4. **No Arbitrary Shell Execution**: `subprocess` calls with `shell=True` are strictly prohibited anywhere in the codebase.
5. **No Destructive Exploitation**: The system performs read-only reconnaissance, vulnerability identification, and controlled validation. Autonomous destructive actions or lateral movement are prohibited.
6. **Secret Management**: API keys, Bearer tokens, and secrets must NEVER be committed to source code or logged in activity outputs. Use `backend/.env`.
7. **Local Service Binding**: HexStrike-AI and OmniRoute proxies must remain bound strictly to private loopback interfaces (`127.0.0.1`).
8. **Factual Verification**: Never fabricate live verification results. Clearly distinguish `REAL` execution from `SIMULATED` mock execution.
9. **Mock Mode Preservation**: `TOOL_PROVIDER=mock` and `LLM_PROVIDER=mock` must remain fully operational for unit tests and offline development.
10. **Sanitized Input Handling**: All parameters passed to tool adapters must undergo strict validation and parameter sanitization.
11. **Report Escaping**: HTML reports generated by `ReportingService` must sanitize user inputs and tool output strings against XSS.
12. **Audit Logging**: All policy decisions, tool invocations, LLM completions, and pipeline state changes must produce immutable timestamped `ActivityLog` entries.

---

## Real vs Mocked Matrix

| Component / Subsystem | Implementation Status | Provider / Transport Mode | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **AresController** | REAL | Asynchronous orchestrator | Phase 7 test suite (55 passed) |
| **Agent Framework** | REAL | BaseAgent / Registry abstraction | Phase 8 test suite (65 passed) |
| **PolicyGateway** | REAL | Deterministic allowlist engine | Phase 12 test suite (33 passed) |
| **ToolGateway** | REAL | Safe adapter execution boundary | Phase 13 test suite (37 passed) |
| **MockToolAdapter** | SIMULATED | Deterministic mock adapter | Phase 13 mock verification |
| **HexStrikeAdapter** | REAL | REST client to HexStrike API | Phase 14 live verification script |
| **HexStrike Service** | LIVE VERIFIED | Local REST service (`127.0.0.1:8888`) | Phase 14 live REST response |
| **ReconAgent** | REAL Boundary | ToolGateway dependent | Phase 9 test suite |
| **AnalyzerAgent** | REAL | Structured prompt & JSON parser | Phase 10 test suite (84 passed) |
| **LLMProvider** | REAL Abstraction | Provider factory | Phase 11 unit tests |
| **OmniRouteProvider**| LIVE VERIFIED | OpenAI-compatible local proxy | Phase 11 live completion request |
| **MockLLMProvider** | SIMULATED | Deterministic JSON responder | Phase 10 & test suite fallback |
| **Evidence & Findings**| REAL | Async SQLite ORM persistence | Phase 15 test suite (43 passed) |
| **ReportingService** | REAL | Sanitized HTML compiler | Phase 16 test suite (44 passed) |
| **3D Core Visuals** | REAL WebGL | R3F + Three.js + GSAP | Phase 17B browser WebGL verification |
| **E2E Pipeline** | CONTROLLED VERIFIED | Full pipeline execution | Phase 18 test suite |

---

## Testing History

- **Phase 7 (Controller & WebSocket)**: 56 total tests | 55 passed | 1 skipped
- **Phase 8 (Agent Framework)**: 66 total tests | 65 passed | 1 skipped
- **Phase 10 (Analyzer Agent & Schema)**: 84 / 84 passed (100%)
- **Phase 12 (Policy Gateway)**: 33 / 33 passed (100%)
- **Phase 13 (Tool Gateway)**: 37 / 37 passed (100%)
- **Phase 15 (Evidence & Findings)**: 43 / 43 passed (100%)
- **Phase 16 (Reporting Service)**: 44 / 44 passed (100%)
- **Phase 14 Live Verification**: Actual HexStrike HTTP 200 response observed with real target scan payload.
- **Phase 18 (End-to-End Suite)**: Controlled E2E tests passed cleanly; Policy, ToolGateway, WebSockets, DB persistence, and frontend build (`npm run build`) verified.

---

## ARES UI / Visual Direction

### Visual Philosophy
ARES represents a high-end autonomous security intelligence console:
- **Tone**: Technical, restrained, intelligent, dark SOC aesthetic.
- **Avoid**: Generic admin panel templates, bright neon overkill, cyberpunk clichés, excessive card grids, unconstrained background glow.

### Color Palette
- **Background**: Near-black (`#030508`) and deep navy-black (`#0A0E17`).
- **Primary Accent**: Electric Blue (`#2563EB`).
- **Secondary Accent**: Indigo / Violet (`#8B5CF6`).
- **Status Colors**:
  - `SUCCESS`: Restrained Green (`#10B981`)
  - `WARNING`: Amber (`#F59E0B`)
  - `BLOCKED`: Muted Violet (`#8B5CF6`)
  - `ERROR`: Crimson (`#EF4444`)
  - `INFO`: Blue (`#3B82F6`)

### Typography
- **Display / Brand**: `Outfit` (Uppercase, clear tracking)
- **UI / Body**: `Inter` (High legibility)
- **Monospace / Telemetry**: `Fira Code` / `JetBrains Mono`

### 3D Core Architecture
Built using Three.js, React Three Fiber, Drei, and GSAP:
- **Central Nucleus**: Solid grounding geometric sphere.
- **Topology Sphere / Orbital Rings**: Interlocking toruses representing active data paths.
- **Particle System**: Distributed orbital nodes representing discovery and analysis data streams.
- **Interactivity**: Smooth mouse/cursor parallax tracking, state-driven rotation speeds, color theme shifts based on active pipeline stage.

> [!NOTE]
> The current Phase 17B UI design and 3D Holographic Core implementation are ACCEPTED for the Minor Project scope. Do not perform further visual redesigns unless explicitly requested.

---

## AI Agent Startup Protocol

Every AI coding agent (Claude Code, Antigravity, or other subagents) interacting with this codebase MUST strictly execute the following startup sequence:

1. **Read `docs/Tracker.md` FIRST** to establish accurate context on completed phases, architecture, and current state.
2. **Read `docs/Rules.md` SECOND** to review non-negotiable development and safety guidelines.
3. **Read the relevant task documentation** (`docs/PRD.md`, `docs/TechSpec.md`, `docs/Schema.md`, etc.) before making structural changes.
4. **Inspect actual repository source code** using file viewing tools; NEVER guess variable names, file locations, or schemas.
5. **Identify the exact current phase** and verify whether the requested task belongs strictly to that phase.
6. **Never assume previous conversation context** carries over between independent agent invocations.
7. **Never claim live execution or test success** without empirical runtime evidence or passing test outputs.
8. **Never accidentally implement Major Project scope** (such as autonomous exploit loops, multi-tenant auth, or Kubernetes configs).
9. **Never alter core architectural boundaries** (`Controller`, `PolicyGateway`, `ToolGateway`, `LLMProvider`).
10. **Always keep changes incremental**, verifying modifications against existing tests.
11. **Report exact files created, modified, or deleted** at the end of every turn.
12. **Run verification commands** (`pytest`, `npm run build`) before declaring completion of a task.
13. **Update `docs/Tracker.md`** immediately following any phase transition or configuration status change.

---

## CURRENT SESSION

### Development Position
**ARES NO-AUTO-EXECUTION & USER-TARGET-ONLY EXECUTION — PRISTINE & VERIFIED (0 FAILED)**

### Root Cause Analysis of Auto-Demo Record Reappearance
- **Identified Root Cause**: When `pytest` was executed, SQLAlchemy connected directly to the production SQLite database `data/ares.db` because `DATABASE_URL` was static. `pytest` test runs inserted test fixtures ("E2E Happy Path", "WS Test", "Policy Block Test", "Duplicate Run Test", etc.) directly into `data/ares.db`. The background `uvicorn` server read those rows, making test records appear as if they were recreated by the application.
- **Root Cause Resolution**: Created `backend/tests/conftest.py` which intercepts `DATABASE_URL` before any app code imports `engine.py` and routes all `pytest` database operations to `data/ares_test.db`. Production database `data/ares.db` is 100% isolated and never touched by `pytest`.

### Fix & Enforcement Summary
1. **Database Test Isolation**: Implemented `backend/tests/conftest.py` routing all test fixtures to `data/ares_test.db` with automated table creation hooks.
2. **Frontend Explicit Start Flow**:
   - `NewAssessment.tsx`: Set default form target to `http://localhost/DVWA/`. Removed automatic `api.startAssessment(id)` call upon creation. Form submission creates the assessment record in `CREATED` status and redirects to detail view without triggering scan pipeline.
   - `AssessmentDetail.tsx`: Added an explicit **"START ASSESSMENT"** button for `CREATED`, `FAILED`, and `BLOCKED` states. Clicking this button is the ONLY trigger for `POST /api/assessments/{id}/start`.
3. **Database Reset**: Created database backup `data/ares_backup.db` and executed `scripts/reset_db.py`. Reset `data/ares.db` state to: `assessments: 0`, `findings: 0`, `evidence: 0`, `reports: 0`, `activity_logs: 0`, `projects: 1` ("ARES Workspace").
4. **Target Integrity Verification**: Tested creation and start of `http://localhost/DVWA/`. Verified that target is strictly preserved through Policy -> Recon -> HexStrike -> Analyzer -> OmniRoute -> Validation -> Evidence -> Reporting.

### System Verification Metrics
- **Backend Pytest Suite**: **131 PASSED, 0 FAILED, 1 SKIPPED** (running against `data/ares_test.db`)
- **Frontend Build**: **PASS** (`npm run build` in 9.07s)
- **Production DB State (`data/ares.db`)**: **0 assessments, 0 findings, 0 evidence, 0 reports**
- **Startup Auto-Execution**: **0 background tasks, 0 scans, 0 external requests**

---

## Immutable Historical Decisions

- **Phase 4 (Auth & RBAC)**: Remains deferred to Major Project.
- **ARES-RL (Reinforcement Learning)**: Remains outside Minor Project scope.
- **Advanced Autonomous Exploitation**: Remains outside Minor Project scope.
- **HexStrike Integration**: Live verification complete (Phase 14).
- **UI Redesign**: Complete and accepted (Phase 17B).
- **3D Core**: Complete and accepted (Phase 17B).
- **Mock Mode**: Must be preserved for automated testing.
- **Live Mode**: Must remain private/local (`127.0.0.1`).
- **Secrets**: No secrets or API keys documented in `Tracker.md` or committed to source.

---

## MAJOR PROJECT

### MAJOR M1 — Agentic VAPT Loop
- **STATUS**: COMPLETE
- **Objective**: Transition from a linear pipeline to an iterative reasoning loop.
- **What Was Implemented**: `PlannerAgent` for next-action hypothesis and planning, `ObservationAgent` for evaluating tool results. Introduced bounded `while` loop within `AresController.run()` respecting `MAX_VAPT_ACTIONS`. Extended finding states (`POTENTIAL`, `CANDIDATE`, `VALIDATING`, `VALIDATED`, etc.) and capabilities (`EXPLOITATION`, `BRUTE_FORCE`).
- **Verification**: 131 backend tests passed. Architecture handles iterative Replanning, State update, Policy enforcement, and Tool isolation safely.

### MAJOR M2 — Agentic Benchmark Framework
- **STATUS**: COMPLETE / READY FOR MANUAL LIVE BENCHMARK
- **Objective**: Validate the implementation and harden boundaries for a live agentic benchmark against DVWA. Provide a manual runbook and reporting structure.
- **What Was Implemented**: Verified architecture integrity. Ensured no live execution against target during tests. Verified mock tests deterministically cover planner/observation logic. Confirmed UI elements expose live streamed intelligence. Formatted manual benchmark runbook.
- **Verification**: Backend pytest (131 passed), frontend npm build (passed). Live HexStrike path preserved but isolated. Target isolation and startup safety confirmed.

### MAJOR M3 — Iterative Pentesting Loop
- **STATUS**: IMPLEMENTATION COMPLETE
- **Objective**: Transition ARES from vulnerability assessment to iterative penetration testing (Recon → Attack Surface → Hypothesis → Test → Observe → Re-reason → Report).
- **What Was Implemented**: `AttackSurface` model, `PentestAction` model, `PlannerAgent`, `ObservationAgent`, policy-controlled execution, iterative replanning, finding state machine, action budgets, evidence linkage, automated test results.
- **Verification**: IMPLEMENTATION VERIFIED. Backend pytest (131 passed, 0 failed, 1 skipped). Frontend build clean. Pentest loops correctly update finding states based on planner hypotheses and observation logic deterministically.
- **Live Pentest Status**: NOT VERIFIED (No live exploitation or vulnerability validation has been run against a target for M3 yet).

