export default function Architecture() {
  const flow = [
    { name: 'UI / DASHBOARD', status: 'IMPLEMENTED', desc: 'Vite + React 19 Frontend', detail: 'React Router, Three.js/R3F 3D Core, GSAP' },
    { name: 'ARES CONTROLLER', status: 'IMPLEMENTED', desc: 'FastAPI Orchestration Core', detail: '7-stage async pipeline with WebSocket broadcast' },
    { name: 'POLICY GATEWAY', status: 'IMPLEMENTED', desc: 'Scope Enforcement & Authorization', detail: 'Allowlist engine — blocks unauthorized targets before execution' },
    { name: 'AGENT FRAMEWORK', status: 'IMPLEMENTED', desc: 'ReconAgent · AnalyzerAgent · ValidationAgent', detail: 'BaseAgent abstraction with typed input/output contracts' },
    { name: 'TOOL GATEWAY', status: 'IMPLEMENTED', desc: 'Isolated Tool Execution Boundary', detail: 'Parameter sanitization · timeout · capability mapping' },
    { name: 'HEXSTRIKE ADAPTER', status: 'LIVE VERIFIED', desc: 'HexStrike-AI REST Integration', detail: 'HTTP POST to 127.0.0.1:8888 · Real DVWA scan verified (Phase 14)' },
    { name: 'LLM REASONER', status: 'IMPLEMENTED', desc: 'LLMProvider Abstraction', detail: 'Structured prompt builder · JSON response parser' },
    { name: 'OMNIROUTE', status: 'LIVE VERIFIED', desc: 'LLM Transport — localhost:20128/v1', detail: 'OpenAI-compatible proxy · Live inference verified (Phase 11)' },
    { name: 'EVIDENCE PIPELINE', status: 'IMPLEMENTED', desc: 'Data Provenance & Validation', detail: 'SQLite persistence · Typed EvidenceOut schema' },
    { name: 'REPORTING ENGINE', status: 'IMPLEMENTED', desc: 'HTML Report Generation', detail: 'ReportingService · XSS-escaped HTML · assessment artifact' },
  ];

  const statusStyle = (status: string) => {
    if (status === 'LIVE VERIFIED') return { color: 'var(--state-success)', border: 'var(--state-success)', bg: 'rgba(16,185,129,0.08)' };
    if (status === 'IMPLEMENTED') return { color: 'var(--accent-primary)', border: 'var(--border-primary)', bg: 'var(--bg-input)' };
    return { color: 'var(--text-muted)', border: 'var(--border-primary)', bg: 'var(--bg-input)' };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <h1 className="page-title">System Topology</h1>
        <p className="page-description">ARES Sub-System Architecture & Integration State</p>
      </div>

      <div className="grid-2">
        <div className="panel" style={{ padding: 0 }}>
          <div className="panel-header" style={{ padding: '20px 20px 12px 20px', marginBottom: 0 }}>
            <span className="panel-title">Data Flow & Integration</span>
          </div>
          <div style={{ padding: '24px 40px', display: 'flex', flexDirection: 'column', gap: 0, position: 'relative' }}>
            {flow.map((node, i) => {
              const s = statusStyle(node.status);
              return (
                <div key={node.name} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: `1px solid ${s.border}`,
                    background: s.bg,
                    borderRadius: 'var(--radius-sm)',
                    textAlign: 'center',
                    position: 'relative',
                    zIndex: 2,
                  }}>
                    <div style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', marginBottom: 2 }}>
                      {node.name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 2 }}>{node.desc}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{node.detail}</div>
                    <div style={{ marginTop: 6 }}>
                      <span className="badge" style={{ color: s.color, borderColor: s.color }}>
                        {node.status}
                      </span>
                    </div>
                  </div>
                  {i < flow.length - 1 && (
                    <div style={{ width: 2, height: 20, background: 'var(--border-primary)', zIndex: 1 }} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Technology Stack */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Technology Stack</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: 'Backend Core', tags: ['Python 3.14', 'FastAPI', 'SQLAlchemy', 'SQLite', 'aiosqlite', 'httpx'] },
                { label: 'Frontend UI', tags: ['React 19', 'TypeScript', 'Vite', 'Three.js', 'React Three Fiber', 'GSAP'] },
                { label: 'Security Tooling', tags: ['HexStrike-AI v6.0.0', 'OmniRoute', 'PolicyGateway', 'ToolGateway'] },
                { label: 'Testing', tags: ['pytest', 'pytest-asyncio', 'httpx'] },
              ].map(({ label, tags }) => (
                <div key={label}>
                  <div style={{ fontSize: 11, fontFamily: 'var(--font-display)', color: 'var(--accent-primary)', marginBottom: 8, textTransform: 'uppercase' }}>{label}</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {tags.map(t => (
                      <span key={t} style={{ fontSize: 11, padding: '2px 8px', border: '1px solid var(--border-hover)', borderRadius: 'var(--radius-xs)', color: 'var(--text-secondary)' }}>{t}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Verification Matrix */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Verification Matrix</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { component: 'HexStrike Integration', status: 'LIVE VERIFIED', note: 'Phase 14 — Real DVWA scan' },
                { component: 'OmniRoute / LLM', status: 'LIVE VERIFIED', note: 'Phase 11 — Live completion' },
                { component: 'PolicyGateway', status: 'IMPLEMENTED', note: '33/33 tests passing' },
                { component: 'ToolGateway', status: 'IMPLEMENTED', note: '37/37 tests passing' },
                { component: 'Evidence Pipeline', status: 'IMPLEMENTED', note: '43/43 tests passing' },
                { component: 'Reporting Service', status: 'IMPLEMENTED', note: '44/44 tests passing' },
                { component: 'E2E Pipeline', status: 'IMPLEMENTED', note: 'Phase 18 controlled verify' },
              ].map(row => (
                <div key={row.component} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border-primary)' }}>
                  <div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)' }}>{row.component}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>{row.note}</div>
                  </div>
                  <span className="badge" style={{
                    color: row.status === 'LIVE VERIFIED' ? 'var(--state-success)' : 'var(--accent-primary)',
                    borderColor: row.status === 'LIVE VERIFIED' ? 'var(--state-success)' : 'rgba(37,99,235,0.4)',
                  }}>
                    {row.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* System Constraint */}
          <div className="panel" style={{ background: 'rgba(37,99,235,0.04)', borderColor: 'rgba(37,99,235,0.2)' }}>
            <div className="panel-header">
              <span className="panel-title" style={{ color: 'var(--accent-primary)' }}>System Constraint</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              ARES is restricted to <strong>localhost</strong> environments only. The Policy Gateway
              enforces target validation before any agent is dispatched. HexStrike execution is bound
              exclusively to <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>127.0.0.1:8888</code> and
              has been live-verified against the authorized DVWA target.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
