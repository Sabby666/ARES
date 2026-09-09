import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, Evidence } from '../services/api';
import { Database, ExternalLink, Clock, Filter } from 'lucide-react';

function formatTs(ts: string | null | undefined): string {
  if (!ts) return '—';
  try { return new Date(ts).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }); }
  catch { return '—'; }
}

function sourceTypeBadge(sourceType: string) {
  if (sourceType === 'MOCK') return { color: 'var(--state-warning)', label: 'SIMULATED' };
  if (sourceType === 'HEXSTRIKE') return { color: 'var(--state-success)', label: 'HEXSTRIKE' };
  if (sourceType === 'LLM') return { color: 'var(--accent-primary)', label: 'LLM' };
  return { color: 'var(--text-muted)', label: sourceType };
}

function evidenceTypeBadge(evType: string) {
  if (evType === 'TOOL_OUTPUT') return { color: 'var(--state-info)', label: 'TOOL OUTPUT' };
  if (evType === 'ANALYSIS') return { color: 'var(--accent-secondary)', label: 'ANALYSIS' };
  if (evType === 'VALIDATION') return { color: 'var(--state-success)', label: 'VALIDATION' };
  return { color: 'var(--text-muted)', label: evType };
}

function safePreview(content: string, maxLen = 300): string {
  if (!content) return '';
  const text = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text;
}

export default function EvidencePage() {
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Evidence | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const navigate = useNavigate();

  useEffect(() => {
    api.getAllEvidence()
      .then(data => {
        setEvidence(data);
        if (data.length > 0) setSelected(data[0]);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  const evidenceTypes = ['ALL', ...Array.from(new Set(evidence.map(e => e.evidence_type)))];
  const filtered = filterType === 'ALL' ? evidence : evidence.filter(e => e.evidence_type === filterType);

  const counts = evidence.reduce((acc, e) => {
    acc[e.evidence_type] = (acc[e.evidence_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div>
          <h1 className="page-title">Evidence Workspace</h1>
          <p className="page-description">Tool output, analysis artifacts, and validation provenance</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="badge" style={{ color: 'var(--state-success)', borderColor: 'var(--state-success)' }}>
            {evidence.length} RECORDS
          </span>
        </div>
      </div>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <Filter size={12} style={{ color: 'var(--text-muted)' }} />
        {evidenceTypes.map(t => (
          <button
            key={t}
            className={`btn btn-sm ${filterType === t ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterType(t)}
          >
            {t} {t !== 'ALL' && counts[t] ? `[${counts[t]}]` : t === 'ALL' ? `[${evidence.length}]` : ''}
          </button>
        ))}
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)', color: 'var(--state-error)', fontSize: 12 }}>
          {error}
        </div>
      )}

      {filtered.length > 0 ? (
        <div style={{ display: 'flex', gap: 24, flex: 1, minHeight: 0 }}>

          {/* Evidence List */}
          <div className="panel" style={{ width: '38%', display: 'flex', flexDirection: 'column', padding: 0 }}>
            <div className="panel-header" style={{ padding: '16px 20px 12px 20px', marginBottom: 0, position: 'sticky', top: 0, background: 'var(--bg-panel)', zIndex: 10 }}>
              <span className="panel-title">Evidence Records</span>
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {filtered.map(ev => {
                const st = sourceTypeBadge(ev.source_type);
                const et = evidenceTypeBadge(ev.evidence_type);
                const isActive = selected?.id === ev.id;
                return (
                  <div
                    key={ev.id}
                    onClick={() => setSelected(ev)}
                    style={{
                      padding: '14px 16px',
                      borderBottom: '1px solid var(--border-primary)',
                      cursor: 'pointer',
                      background: isActive ? 'rgba(37,99,235,0.06)' : 'transparent',
                      borderLeft: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{ev.action}</span>
                      <span style={{ fontSize: 10, fontFamily: 'var(--font-display)', fontWeight: 700, color: st.color }}>{st.label}</span>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)', marginBottom: 4 }}>
                      [{ev.agent}]
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{ fontSize: 10, color: et.color, border: `1px solid ${et.color}`, padding: '1px 5px', borderRadius: 2 }}>{et.label}</span>
                      <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: 3 }}>
                        <Clock size={9} />{formatTs(ev.timestamp as unknown as string)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Evidence Detail */}
          <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflowY: 'auto' }}>
            {selected ? (
              <>
                <div style={{ padding: 24, borderBottom: '1px solid var(--border-primary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                    <div>
                      <h2 style={{ fontSize: 18, color: 'var(--text-primary)', fontWeight: 700, marginBottom: 6 }}>{selected.action}</h2>
                      <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
                        AGENT: {selected.agent}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {(() => { const st = sourceTypeBadge(selected.source_type); return <span className="badge" style={{ color: st.color, borderColor: st.color }}>{st.label}</span>; })()}
                      {(() => { const et = evidenceTypeBadge(selected.evidence_type); return <span className="badge" style={{ color: et.color, borderColor: et.color }}>{et.label}</span>; })()}
                    </div>
                  </div>

                  {/* Metadata grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    {[
                      { label: 'SOURCE', value: selected.source },
                      { label: 'TIMESTAMP', value: formatTs(selected.timestamp as unknown as string) },
                      { label: 'ASSESSMENT ID', value: selected.assessment_id?.slice(0,8) + '…' },
                      { label: 'FINDING ID', value: selected.finding_id ? selected.finding_id.slice(0,8) + '…' : 'N/A (assessment-level)' },
                    ].map(row => (
                      <div key={row.label} style={{ background: 'var(--bg-input)', padding: '10px 14px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-primary)' }}>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: 4 }}>{row.label}</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>{row.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Navigation links */}
                  <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                    <button
                      className="btn btn-secondary"
                      style={{ fontSize: 11, padding: '5px 10px', display: 'flex', alignItems: 'center', gap: 6 }}
                      onClick={() => navigate(`/assessments/${selected.assessment_id}`)}
                    >
                      <ExternalLink size={11} /> VIEW ASSESSMENT
                    </button>
                    {selected.finding_id && (
                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: 11, padding: '5px 10px', display: 'flex', alignItems: 'center', gap: 6 }}
                        onClick={() => navigate('/findings')}
                      >
                        <ExternalLink size={11} /> VIEW FINDING
                      </button>
                    )}
                  </div>
                </div>

                {/* Content */}
                <div style={{ padding: 24 }}>
                  <div style={{ fontSize: 11, fontFamily: 'var(--font-display)', color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Evidence Content
                  </div>
                  <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 16 }}>
                    <pre style={{ margin: 0, fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: 400 }}>
                      {safePreview(selected.content)}
                    </pre>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state" style={{ height: '100%', border: 'none' }}>
                <div className="empty-state-text">SELECT A RECORD TO VIEW DETAILS</div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="empty-state" style={{ flex: 1 }}>
          <div style={{ marginBottom: 16, color: 'var(--border-hover)' }}><Database size={48} strokeWidth={1} /></div>
          <div className="empty-state-title">NO EVIDENCE COLLECTED</div>
          <div className="empty-state-text">
            Evidence is collected automatically during an assessment.<br />
            Run an assessment against an authorized target to populate this workspace.
          </div>
          <button className="btn btn-primary" style={{ marginTop: 24 }} onClick={() => navigate('/assessments/new')}>
            + NEW ASSESSMENT
          </button>
        </div>
      )}
    </div>
  );
}
