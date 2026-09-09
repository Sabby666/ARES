"""
ARES Analyzer prompt templates — Phase 10.

Prompts are constructed from discrete ReconResult sections so the LLM
reasons per-field rather than on a raw JSON blob. This enables clearer
OBSERVED / INFERRED / POTENTIAL classification.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Analyzer prompts
# ─────────────────────────────────────────────────────────────────────────────

ANALYZER_SYSTEM_PROMPT = """\
You are ARES Analyzer, an AI security reasoning engine operating inside an \
authorized academic penetration-testing laboratory.

AUTHORIZATION CONTEXT
- This analysis is performed on an explicitly authorized target.
- You are reasoning about recon data gathered by a controlled tool chain.
- No real exploitation is performed or authorized by your output.

STRICT RULES
1. Reason ONLY from the supplied evidence. Do not invent endpoints, headers, \
   or observations that are not present in the input.
2. Every finding MUST carry an `evidence_status` field set to exactly one of:
   - "OBSERVED"   — the indicator is directly visible in the recon data
   - "INFERRED"   — strongly implied by a combination of recon signals
   - "POTENTIAL"  — plausible based on technology stack or patterns, \
                    but not directly confirmed by recon data
3. Do NOT write "confirmed exploitation" or "vulnerability confirmed" — \
   that requires the ValidationAgent's explicit test results.
4. Do NOT generate payloads, exploit code, or destructive action sequences.
5. Findings with no supporting recon evidence MUST be omitted entirely.
6. Return ONLY valid JSON that matches the required schema. No markdown wrapper.
"""

ANALYZER_USER_PROMPT_TEMPLATE = """\
Authorized Security Analysis Request
=====================================
Target       : {target}
Reachable    : {reachable}
Status Code  : {status_code}
Execution Mode: {execution_mode}
Source Adapter: {source}

--- ENDPOINTS DISCOVERED ({endpoints_count}) ---
{endpoints_section}

--- TECHNOLOGY STACK ---
{technologies_section}

--- RESPONSE HEADERS ---
{headers_section}

--- RECON OBSERVATIONS ---
{observations_section}

--- OPEN PORTS ---
{open_ports_section}

--- TLS ---
{tls_section}

TASK
----
Analyze the above reconnaissance data and return a JSON object with a \
"findings" list. Each finding must include:
  title, category, severity, confidence, endpoint, description, reasoning,
  recommendation, evidence_status, evidence_requirements, suggested_validation_context

Remember:
- evidence_status must be "OBSERVED", "INFERRED", or "POTENTIAL"
- Do not claim confirmation without direct evidence
- Omit speculative findings that have zero supporting signals
"""


# ─────────────────────────────────────────────────────────────────────────────
# Reasoner prompts (unchanged from Phase 11 — kept here for co-location)
# ─────────────────────────────────────────────────────────────────────────────

REASONER_SYSTEM_PROMPT = """\
You are ARES Reasoner, an AI risk-assessment engine operating inside an \
authorized academic penetration-testing laboratory.

RULES
1. Reason ONLY from the supplied findings and recon evidence.
2. Do NOT invent findings.
3. Calculate a realistic risk score between 0.0 and 10.0 based on severity \
   and exploitability.
4. Construct logical, multi-step attack chains combining multiple findings \
   where applicable.
5. Provide a professional markdown-formatted reasoning summary.
6. Return ONLY valid JSON that matches the required schema.
"""

REASONER_USER_PROMPT_TEMPLATE = """\
Authorized Risk Analysis Request
==================================
Reconnaissance Data:
{recon_data}

Candidate Findings:
{findings}

Return a JSON object with "attack_chains", "risk_score", and "reasoning_summary".
"""


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build structured analyzer prompt from ReconResult fields
# ─────────────────────────────────────────────────────────────────────────────

def build_analyzer_user_prompt(recon_data: dict) -> str:
    """
    Build a structured analyzer prompt from a ReconResult-derived dict.

    Renders each section discretely so the LLM can reason per-field rather
    than scanning a raw JSON blob. Falls back gracefully for missing keys.
    """

    # ── Endpoints section ────────────────────────────────────────────────────
    endpoints = recon_data.get("endpoints", [])
    if endpoints:
        ep_lines = []
        for ep in endpoints:
            tech_str = ", ".join(ep.get("tech", [])) or "—"
            ep_lines.append(
                f"  {ep.get('method', '?'):6s} {ep.get('path', '?'):30s}  "
                f"HTTP {ep.get('status', '?')}  [{tech_str}]"
            )
        endpoints_section = "\n".join(ep_lines)
    else:
        endpoints_section = "  (none discovered)"

    # ── Technologies section ─────────────────────────────────────────────────
    techs = recon_data.get("technologies", [])
    if techs:
        tech_lines = [
            f"  {t.get('name', '?')} {t.get('version', '')} ({t.get('category', '?')})"
            for t in techs
        ]
        technologies_section = "\n".join(tech_lines)
    else:
        technologies_section = "  (none detected)"

    # ── Headers section ──────────────────────────────────────────────────────
    headers = recon_data.get("headers", {})
    if headers:
        hdr_lines = [f"  {k}: {v}" for k, v in headers.items()]
        headers_section = "\n".join(hdr_lines)
    else:
        headers_section = "  (none captured)"

    # ── Observations section ─────────────────────────────────────────────────
    observations = recon_data.get("observations", [])
    if observations:
        obs_lines = [f"  • {obs}" for obs in observations]
        observations_section = "\n".join(obs_lines)
    else:
        observations_section = "  (none recorded)"

    # ── Open ports ───────────────────────────────────────────────────────────
    ports = recon_data.get("open_ports", [])
    open_ports_section = ", ".join(str(p) for p in ports) if ports else "(none)"

    # ── TLS ──────────────────────────────────────────────────────────────────
    tls = recon_data.get("tls") or {}
    if tls:
        tls_lines = [f"  {k}: {v}" for k, v in tls.items()]
        tls_section = "\n".join(tls_lines)
    else:
        tls_section = "  (no TLS data)"

    return ANALYZER_USER_PROMPT_TEMPLATE.format(
        target=recon_data.get("target", "(unknown)"),
        reachable=recon_data.get("reachable", True),
        status_code=recon_data.get("status_code", "—"),
        execution_mode=recon_data.get("execution_mode", "SIMULATED"),
        source=recon_data.get("source", "unknown"),
        endpoints_count=len(endpoints),
        endpoints_section=endpoints_section,
        technologies_section=technologies_section,
        headers_section=headers_section,
        observations_section=observations_section,
        open_ports_section=open_ports_section,
        tls_section=tls_section,
    )
