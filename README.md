# ARES — Multi-Agent Security Assessment Prototype

> **Academic Use Only** — This is a classroom prototype. No real exploitation, no external scanning.

## Overview

ARES (Automated Red-Teaming Evaluation System) is a multi-agent security assessment prototype inspired by the research paper *"A Multi-Agent Large Language Model Framework for Autonomous Web Application Penetration Testing."*

It demonstrates how specialized AI agents collaborate through a structured pipeline to perform simulated security assessments.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ARES Controller                       │
│  Policy → Recon → Analysis → LLM → Validation → Report │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket + REST API
┌────────────────────┴────────────────────────────────────┐
│              React Dashboard (Vite + TS)                 │
│  Dashboard | Assessments | Findings | Agents | Reports   │
└─────────────────────────────────────────────────────────┘
```

## Development Stage: Phase 1 — Project Foundation

The project has established its foundational architecture, including centralized configuration, error handling, structured logging, and frontend/backend connectivity. 

**Current Limitations:**
- HexStrike tool execution is NOT yet implemented.
- OmniRoute LLM provider is NOT yet implemented.
- Agent reasoning remains mocked.

## Quick Start

### Configuration

Copy `.env.example` to the project root as `.env`:

```bash
cp .env.example .env
```

You can customize `APP_ENV`, `FRONTEND_URL`, and other parameters.

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser. The top right corner will display the backend connectivity status. Health endpoint is accessible at `http://localhost:8000/api/health`.

## Agent Pipeline

| Stage | Agent | Description |
|-------|-------|-------------|
| 1 | **Policy Agent** | Validates target is within scope (localhost only) |
| 2 | **Recon Agent** | Discovers endpoints, technologies, and attack surface |
| 3 | **Analyzer Agent** | Identifies candidate vulnerabilities |
| 4 | **LLM Reasoner** | Prioritizes findings and builds attack chains |
| 5 | **Validation Agent** | Re-tests findings to reduce false positives |
| 6 | **Controller** | Stores evidence and generates HTML report |

## Safety

- ✅ **Localhost only** — Policy Agent blocks any target outside `localhost`, `127.0.0.1`, `demo.local`
- ✅ **No arbitrary shell execution** — Tool execution is strictly controlled via Tool Gateway (upcoming phase).

## Tech Stack

- **Backend:** Python 3.14, FastAPI, SQLAlchemy (async), SQLite, WebSockets
- **Frontend:** React 19, TypeScript, Vite, React Router, Lucide Icons
- **Design Toolchain:** UI UX Pro Max, Taste v2 (design-taste-frontend), Design DNA, Impeccable, Emil Motion, Three.js / React Three Fiber, GSAP
- **Design:** Dark SOC aesthetic with glassmorphism, cyan/blue accents

## License

Academic prototype — not for production use.
