import { useEffect, useState } from 'react';
import { api, Finding, DashboardData } from '../services/api';
import { ShieldAlert, TrendingUp, Tag, AlertTriangle } from 'lucide-react';

function severityColor(sev: string): string {
  const map: Record<string, string> = {
    Critical: 'var(--state-error)',
    High: 'var(--state-warning)',
    Medium: '#F59E0B',
    Low: 'var(--state-success)',
    Info: 'var(--state-info)',
  };
  return map[sev] || 'var(--text-muted)';
}

function severityOrder(sev: string): number {
  return { Critical: 0, High: 1, Medium: 2, Low: 3, Info: 4 }[sev] ?? 5;
}

export default function ThreatIntel() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getAllFindings(), api.getDashboard()])
      .then(([f, d]) => { setFindings(f); setDashboard(d); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  const hasData = findings.length > 0;

  // Derived security context from real findings
  const severityCounts: Record<string, number> = findings.reduce((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const categories: Record<string, number> = findings.reduce((acc, f) => {
    if (f.category) acc[f.category] = (acc[f.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sortedCategories = Object.entries(categories).sort((a, b) => b[1] - a[1]);

  const topFindings = [...findings]
    .sort((a, b) => severityOrder(a.severity) - severityOrder(b.severity))
    .slice(0, 8);

  // Extract observed technologies from recon_data in assessments (if present in description/reasoning)
  const techKeywords = ['PHP', 'Apache', 'MySQL', 'WordPress', 'jQuery', 'OpenSSL', 'nginx', 'Laravel', 'Node.js', 'Express', 'React', 'Django', 'Flask', 'Ruby on Rails'];
  const observedTech = new Set<string>();
  findings.forEach(f => {
    const text = `${f.description} ${f.reasoning} ${f.recommendation}`.toLowerCase();
    techKeywords.forEach(t => { if (text.includes(t.toLowerCase())) observedTech.add(t); });
  });

  const SEVERITY_LEVELS = ['Critical', 'High', 'Medium', 'Low', 'Info'];
  const totalFindings = findings.length;
  const highRisk = (severityCounts['Critical'] || 0) + (severityCounts['High'] || 0);
  const riskScore = totalFindings === 0 ? 0 : Math.min(100, Math.round(
    ((severityCounts['Critical'] || 0) * 40 +
     (severityCounts['High'] || 0) * 20 +
     (severityCounts['Medium'] || 0) * 8 +
     (severityCounts['Low'] || 0) * 2) / Math.max(1, totalFindings) * 5
  ));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div>
          <h1 className="page-title">Security Context</h1>
          <p className="page-description">Local threat intelligence derived from assessment evidence</p>
        </div>
        <span className="badge" style={{ color: 'var(--accent-primary)', borderColor: 'rgba(37,99,235,0.3)' }}>
          DERIVED FROM ASSESSMENT DATA
        </span>
      </div>

      {!hasData ? (
        <div className="empty-state" style={{ flex: 1 }}>
          <div style={{ marginBottom: 16, color: 'var(--border-hover)' }}><ShieldAlert size={48} strokeWidth={1} /></div>
          <div className="empty-state-title">NO THREAT CONTEXT</div>
          <div className="empty-state-text">
            Threat context becomes available after an assessment.<br />
            Run an authorized assessment to generate local security intelligence.
          </div>
          <div style={{ marginTop: 24, padding: '12px 20px', background: 'rgba(37,99,235,0.06)', border: '1px solid rgba(37,99,235,0.2)', borderRadius: 'var(--radius-sm)', maxWidth: 480, textAlign: 'left' }}>
            <div style={{ fontSize: 11, fontFamily: 'var(--font-display)', color: 'var(--accent-primary)', marginBottom: 8 }}>SCOPE NOTE</div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              ARES generates local security context exclusively from completed assessments against
              authorized targets (localhost, 127.0.0.1). No external threat intelligence feeds are
              connected. All intelligence is derived from real tool output and LLM analysis.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Risk summary metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
            {[
              { label: 'TOTAL SIGNALS', value: totalFindings, color: 'var(--text-primary)', icon: <ShieldAlert size={14} /> },
              { label: 'HIGH RISK', value: highRisk, color: highRisk > 0 ? 'var(--state-error)' : 'var(--text-muted)', icon: <AlertTriangle size={14} /> },
              { label: 'CATEGORIES', value: sortedCategories.length, color: 'var(--accent-primary)', icon: <Tag size={14} /> },
              { label: 'RISK INDEX', value: `${riskScore}`, color: riskScore > 60 ? 'var(--state-error)' : riskScore > 30 ? 'var(--state-warning)' : 'var(--state-success)', icon: <TrendingUp size={14} /> },
            ].map(m => (
              <div key={m.label} className="panel" style={{ padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{m.label}</span>
                  <span style={{ color: m.color }}>{m.icon}</span>
                </div>
                <div style={{ fontSize: 26, fontWeight: 600, color: m.color, fontFamily: 'var(--font-sans)', lineHeight: 1 }}>
                  {m.value}
                </div>
              </div>
            ))}
          </div>

          <div className="grid-2">
            {/* Severity Distribution */}
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">Severity Distribution</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {SEVERITY_LEVELS.map(sev => {
                  const count = severityCounts[sev] || 0;
                  const pct = totalFindings > 0 ? (count / totalFindings) * 100 : 0;
                  return (
                    <div key={sev}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: severityColor(sev) }}>{sev.toUpperCase()}</span>
                        <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: count > 0 ? severityColor(sev) : 'var(--text-muted)' }}>{count}</span>
                      </div>
                      <div style={{ height: 4, background: 'var(--bg-input)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${pct}%`, background: severityColor(sev), borderRadius: 2, transition: 'width 0.4s ease' }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Vulnerability Categories */}
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">Vulnerability Categories</span>
              </div>
              {sortedCategories.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {sortedCategories.slice(0, 8).map(([cat, cnt]) => (
                    <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--bg-input)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-primary)' }}>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{cat}</span>
                      <span className="badge" style={{ color: 'var(--accent-primary)', borderColor: 'rgba(37,99,235,0.3)', fontFamily: 'var(--font-mono)' }}>{cnt}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No categories recorded</div>
              )}
            </div>
          </div>

          <div className="grid-2">
            {/* Top Signals */}
            <div className="panel" style={{ padding: 0 }}>
              <div className="panel-header" style={{ padding: '16px 20px 12px 20px', marginBottom: 0 }}>
                <span className="panel-title">Top Risk Signals</span>
                <span className="badge" style={{ color: 'var(--text-muted)', borderColor: 'var(--border-primary)' }}>REAL FINDINGS</span>
              </div>
              <div style={{ overflowY: 'auto', maxHeight: 320 }}>
                {topFindings.map(f => (
                  <div key={f.id} style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-primary)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: severityColor(f.severity), marginTop: 4, flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{f.title}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{f.category} • {f.endpoint || 'N/A'}</div>
                    </div>
                    <span style={{ fontSize: 10, color: severityColor(f.severity), fontFamily: 'var(--font-display)', fontWeight: 700, flexShrink: 0 }}>{f.severity.toUpperCase()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Observed Technologies + Scope note */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {observedTech.size > 0 && (
                <div className="panel">
                  <div className="panel-header">
                    <span className="panel-title">Observed Technology Exposure</span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {Array.from(observedTech).map(tech => (
                      <span key={tech} style={{ fontSize: 12, padding: '4px 10px', border: '1px solid var(--border-hover)', borderRadius: 'var(--radius-xs)', color: 'var(--text-secondary)', background: 'var(--bg-input)' }}>
                        {tech}
                      </span>
                    ))}
                  </div>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 12, lineHeight: 1.5 }}>
                    Inferred from finding descriptions and LLM analysis. May not be exhaustive.
                  </p>
                </div>
              )}

              <div className="panel" style={{ background: 'rgba(37,99,235,0.04)', borderColor: 'rgba(37,99,235,0.2)' }}>
                <div className="panel-header">
                  <span className="panel-title" style={{ color: 'var(--accent-primary)' }}>Intelligence Scope</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[
                    ['Source', 'Assessment evidence (local)'],
                    ['Target scope', 'Authorized lab targets only'],
                    ['External feeds', 'None — no public threat intel'],
                    ['Assessments analyzed', String(dashboard?.stats?.total_assessments ?? 0)],
                    ['Total signals', String(totalFindings)],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                      <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                      <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
