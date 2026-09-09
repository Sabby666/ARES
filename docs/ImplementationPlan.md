# Implementation Plan

## Overview
This roadmap defines the evolution from the current Teacher Demo Prototype to the fully realized ARES Minor Project.

### [REQUIRED - MINOR]
Phases 0 through 18, focusing on functional multi-agent coordination, LLM abstraction, tool gateway safety, and a robust UI.

### [OPTIONAL - MINOR]
Phase 20 (Polish) and richer live monitoring features.

### [DEFERRED - MAJOR]
Browser automation, advanced HexStrike RL training, multi-tenant auth, scalable deployment.

---

## Phases

### PHASE 0: Workspace Audit and Documentation Freeze [COMPLETED]
- **Objective**: Establish PRD, TechSpec, Schema, AppFlow, Design, Tracker, and Rules.

### PHASE 1: Project Foundation [COMPLETED IN PROTOTYPE]
- **Objective**: Initialize monorepo, FastAPI backend, React Vite frontend.

### PHASE 2: Backend Foundation [COMPLETED IN PROTOTYPE]
- **Objective**: Base FastAPI setup, CORS, configuration layers.

### PHASE 3: Database [COMPLETED IN PROTOTYPE]
- **Objective**: Async SQLite engine, SQLAlchemy models (Assessment, Finding, Log).

### PHASE 4: Authentication and Authorization [DEFERRED - MAJOR]
- **Objective**: Local lab deployment assumes trusted user.

### PHASE 5: Frontend Foundation [COMPLETED IN PROTOTYPE]
- **Objective**: React routing, UI shell, dark SOC CSS framework.

### PHASE 6: Assessment Management [COMPLETED IN PROTOTYPE]
- **Objective**: CRUD endpoints for assessments, Dashboard UI.

### PHASE 7: ARES Controller [COMPLETED IN PROTOTYPE]
- **Objective**: Background task orchestrator managing the 7-stage pipeline.

### PHASE 8: Agent Framework [COMPLETED IN PROTOTYPE]
- **Objective**: Base class interfaces for specialized agents.

### PHASE 9: Recon Agent [COMPLETED IN PROTOTYPE (MOCKED)]
- **Next Step**: Transition mock to Tool Gateway -> HexStrike adapter.

### PHASE 10: Analyzer Agent [COMPLETED IN PROTOTYPE (MOCKED)]
- **Next Step**: Enhance logic mapping.

### PHASE 11: LLM abstraction + OmniRoute [REQUIRED - MINOR]
- **Objective**: Replace mock LLMReasoner with an abstract `LLMProvider` interfacing with OmniRoute.
- **Tasks**: Create OpenAI-compatible client wrapper, parse semantic reasoning for exploit generation.

### PHASE 12: Policy Gateway [REQUIRED - MINOR]
- **Objective**: Strictly enforce local-only target rules. (Partially done in prototype, needs hardening).

### PHASE 13: Tool Gateway [REQUIRED - MINOR]
- **Objective**: Build the safe abstraction layer over shell execution.
- **Tasks**: Define parameter sanitization, strict module allowlists.

### PHASE 14: HexStrike integration [REQUIRED - MINOR]
- **Objective**: Connect Tool Gateway to actual HexStrike-AI modules (or simulated equivalents if HexStrike cannot run locally).
- **Tasks**: Subprocess adapters without `shell=True`.

### PHASE 15: Evidence and Findings [REQUIRED - MINOR]
- **Objective**: Connect real LLM/Tool outputs to the `findings` database table.

### PHASE 16: Reporting [COMPLETED IN PROTOTYPE]
- **Objective**: HTML report generation from DB data.

### PHASE 17: Live activity / WebSocket [COMPLETED IN PROTOTYPE]
- **Objective**: Stream logs to UI.

### PHASE 18: Testing [REQUIRED - MINOR]
- **Objective**: E2E testing of the full pipeline (OmniRoute + Tool Gateway).

### PHASE 19: Docker/deployment [OPTIONAL - MINOR]
- **Objective**: Docker Compose for easy lab spin-up.

### PHASE 20: Minor Project Polish [OPTIONAL - MINOR]
- **Objective**: UI refinements, error state handling, empty states.
