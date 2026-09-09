import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, Finding } from '../services/api';
import { ShieldAlert } from 'lucide-react';

export default function Findings() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [filter, setFilter] = useState<string>('ALL');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    api.getAllFindings().then(data => {
      setFindings(data);
      if (data.length > 0) setSelectedId(data[0].id);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  const filtered = filter === 'ALL' ? findings : findings.filter(f => f.severity === filter);
  const selected = findings.find(f => f.id === selectedId);

  const counts = findings.reduce((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <h1 className="page-title">Intelligence Workspace</h1>
        <p className="page-description">Vulnerability Analysis & Provenance</p>
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        {['ALL', 'Critical', 'High', 'Medium', 'Low', 'Info'].map(sev => (
          <button
            key={sev}
            className={`btn btn-sm ${filter === sev ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setFilter(sev); setSelectedId(null); }}
          >
            {sev.toUpperCase()} {sev !== 'ALL' && counts[sev] ? `[${counts[sev]}]` : sev === 'ALL' ? `[${findings.length}]` : ''}
          </button>
        ))}
      </div>

      {filtered.length > 0 ? (
        <div style={{ display: 'flex', gap: 24, flex: 1, minHeight: 0 }}>
          {/* List View */}
          <div className="panel" style={{ width: '35%', display: 'flex', flexDirection: 'column', padding: 0 }}>
            <div className="panel-header" style={{ padding: '20px 20px 12px 20px', marginBottom: 0, position: 'sticky', top: 0, background: 'var(--bg-panel)', zIndex: 10 }}>
              <span className="panel-title">Identified Items</span>
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {filtered.map(f => (
                <div 
                  key={f.id}
                  onClick={() => setSelectedId(f.id)}
                  style={{
                    padding: 16,
                    borderBottom: '1px solid var(--border-primary)',
                    cursor: 'pointer',
                    background: selectedId === f.id ? 'rgba(255,255,255,0.05)' : 'transparent',
                    borderLeft: selectedId === f.id ? `2px solid ${severityColor(f.severity)}` : '2px solid transparent',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{f.title}</span>
                    <span style={{ color: severityColor(f.severity), fontSize: 10, fontFamily: 'var(--font-display)', fontWeight: 800 }}>{f.severity.toUpperCase()}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {f.endpoint}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Detail View */}
          <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflowY: 'auto' }}>
            {selected ? (
              <>
                <div style={{ padding: 24, borderBottom: '1px solid var(--border-primary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                    <div>
                      <h2 style={{ fontSize: 20, color: 'var(--text-primary)', fontWeight: 700, marginBottom: 8 }}>{selected.title}</h2>
                      <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        <span>CAT: {selected.category}</span>
                        <span>TARGET: {selected.endpoint}</span>
                        <span>CONF: {(selected.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <span className={`badge`} style={{ color: severityColor(selected.severity), borderColor: severityColor(selected.severity), background: 'transparent' }}>
                      {selected.severity.toUpperCase()}
                    </span>
                  </div>
                  
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    {selected.description}
                  </div>
                </div>

                <div style={{ padding: 24, borderBottom: '1px solid var(--border-primary)' }}>
                  <h3 style={{ fontSize: 12, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', marginBottom: 12, textTransform: 'uppercase' }}>Reasoning & Recommendation</h3>
                  <div style={{ marginBottom: 16 }}>
                    <span style={{ display: 'block', color: 'var(--accent-primary)', fontSize: 11, fontFamily: 'var(--font-mono)', marginBottom: 4 }}>[ANALYSIS]</span>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{selected.reasoning}</p>
                  </div>
                  <div>
                    <span style={{ display: 'block', color: 'var(--state-success)', fontSize: 11, fontFamily: 'var(--font-mono)', marginBottom: 4 }}>[FIX]</span>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{selected.recommendation}</p>
                  </div>
                </div>

                <div style={{ padding: 24 }}>
                  <h3 style={{ fontSize: 12, fontFamily: 'var(--font-display)', color: 'var(--text-primary)', marginBottom: 12, textTransform: 'uppercase' }}>Evidence Provenance</h3>
                  {selected.evidence && selected.evidence.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {selected.evidence.map(ev => (
                        <div key={ev.id} style={{ background: 'var(--bg-input)', padding: 16, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                            <span style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>SOURCE: {ev.source}</span>
                            <div style={{ display: 'flex', gap: 8 }}>
                              {ev.source_type === 'MOCK' && (
                                <span className="badge" style={{ color: 'var(--state-warning)', borderColor: 'var(--state-warning)' }}>SIMULATED</span>
                              )}
                              <span className="badge" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border-hover)' }}>{ev.evidence_type}</span>
                            </div>
                          </div>
                          <pre style={{ margin: 0, fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', overflowX: 'auto', whiteSpace: 'pre-wrap' }}>
                            {ev.content}
                          </pre>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>NO EVIDENCE RECORDED</div>
                  )}
                </div>
              </>
            ) : (
              <div className="empty-state" style={{ height: '100%', border: 'none' }}>
                <div className="empty-state-text">SELECT AN ITEM TO VIEW DETAILS</div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="empty-state" style={{ flex: 1 }}>
          <div style={{ marginBottom: 16, color: 'var(--border-hover)' }}><ShieldAlert size={48} strokeWidth={1} /></div>
          <div className="empty-state-title">NO FINDINGS RECORDED</div>
          <div className="empty-state-text">
            ARES has not detected any vulnerabilities.<br />
            Run an authorized assessment to begin vulnerability discovery.
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/assessments/new')} style={{ marginTop: 24 }}>
            + NEW ASSESSMENT
          </button>
        </div>
      )}
    </div>
  );
}

function severityColor(sev: string): string {
  const map: Record<string, string> = {
    Critical: 'var(--state-error)',
    High: 'var(--state-warning)',
    Medium: 'var(--state-warning)',
    Low: 'var(--state-success)',
    Info: 'var(--state-info)',
  };
  return map[sev] || 'var(--state-info)';
}
