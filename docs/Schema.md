# Schema: Data Source of Truth

## 1. Database Strategy
- **RDBMS**: SQLite (Minor Project) -> PostgreSQL (Major Project).
- **ORM**: SQLAlchemy with `asyncio` engine.
- **Migrations**: Alembic (deferred until post-prototype phase).

## 2. Entities & 3. Tables

### `assessments`
Core tracking table for a pentest run.
- `id` (String, PK, UUID)
- `name` (String)
- `target` (String)
- `scope` (String, nullable)
- `description` (String, nullable)
- `status` (String) - Enum: CREATED, POLICY_CHECK, RECON, ANALYSIS, LLM_REASONING, VALIDATION, EVIDENCE, REPORTING, COMPLETED, FAILED, BLOCKED
- `started_at` (DateTime, nullable)
- `completed_at` (DateTime, nullable)
- `duration_ms` (Integer, nullable)
- `created_at` (DateTime, default: now)
- *JSON fields for state*: `recon_data`, `analysis_data`, `reasoning_data`

### `findings`
Identified vulnerabilities.
- `id` (String, PK, UUID)
- `assessment_id` (String, FK -> assessments.id)
- `title` (String)
- `category` (String)
- `severity` (String) - Enum: Critical, High, Medium, Low, Info
- `confidence` (Float) - 0.0 to 1.0
- `endpoint` (String)
- `description` (Text)
- `reasoning` (Text) - LLM explanation
- `recommendation` (Text)
- `status` (String) - Enum: Open, Validated, False Positive
- `agent` (String) - Discovering agent
- `created_at` (DateTime, default: now)

### `activity_logs`
System and agent logs for real-time WebSocket streaming and audit.
- `id` (String, PK, UUID)
- `assessment_id` (String, FK -> assessments.id)
- `agent` (String)
- `message` (Text)
- `log_type` (String) - Enum: info, action, success, error, warning
- `timestamp` (DateTime, default: now)

### `reports`
Final generated artifacts.
- `id` (String, PK, UUID)
- `assessment_id` (String, FK -> assessments.id)
- `report_type` (String) - e.g., 'HTML', 'Markdown'
- `content` (Text)
- `generated_at` (DateTime, default: now)

## Future Major Project Expansion
- **`projects` / `users`**: To support multi-tenant RBAC.
- **`agent_executions` / `tool_executions`**: To granularly track HexStrike module runtime, parameters, and raw STDOUT.
- **`evidence`**: To store binary blobs, screenshots (Playwright), or PCAP data.
- **`rl_states`**: To store state-reward vectors for ARES-RL model training.

## 4-15. Definitions
- **Primary Keys**: UUID4 strings.
- **Timestamps**: UTC timezone-aware.
- **Relationships**: `Assessment` has one-to-many with `Finding`, `ActivityLog`, and `Report`. cascade delete applied.
- **Soft Delete**: Not implemented for Minor Project.
