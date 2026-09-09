import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, AssessmentSummary } from '../services/api';
import { StatusBadge } from './Dashboard';
import { Plus, Target, Clock, Activity, ChevronRight } from 'lucide-react';

function formatDate(dt: string | null | undefined): string {
  if (!dt) return '—';
  try {
    return new Date(dt).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
  } catch {
    return '—';
  }
}

export default function Assessments() {
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('ALL');
  const navigate = useNavigate();

  const RUNNING_STATUSES = ['POLICY_CHECK', 'RECON', 'ANALYSIS', 'LLM_REASONING', 'VALIDATION', 'EVIDENCE', 'REPORTING'];
  const STATUS_GROUPS = ['ALL', 'CREATED', 'RUNNING', 'COMPLETED', 'FAILED', 'BLOCKED'];

  const getGroup = (status: string) => {
    if (RUNNING_STATUSES.includes(status)) return 'RUNNING';
    return status;
  };

  const load = () => {
    setLoading(true);
    api.listAssessments()
      .then(setAssessments)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const filtered = filter === 'ALL' ? assessments : assessments.filter(a => getGroup(a.status) === filter);
  const counts = assessments.reduce((acc, a) => {
    const g = getGroup(a.status);
    acc[g] = (acc[g] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div>
          <h1 className="page-title">Assessments</h1>
          <p className="page-description">Assessment workspace — manage and monitor security cycles</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/assessments/new')}
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <Plus size={14} /> NEW ASSESSMENT
        </button>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {STATUS_GROUPS.map(g => (
          <button
            key={g}
            className={`btn btn-sm ${filter === g ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter(g)}
          >
            {g} {g !== 'ALL' && counts[g] ? `[${counts[g]}]` : g === 'ALL' ? `[${assessments.length}]` : ''}
          </button>
        ))}
        <button className="btn btn-secondary btn-sm" onClick={load} style={{ marginLeft: 'auto', fontSize: 10 }}>
          ↻ REFRESH
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)', color: 'var(--state-error)', fontSize: 12 }}>
          {error}
        </div>
      )}

      {filtered.length > 0 ? (
        <div className="panel" style={{ padding: 0, flex: 1 }}>
          <div className="panel-header" style={{ padding: '16px 20px 12px 20px', marginBottom: 0 }}>
            <span className="panel-title">Cycle Registry</span>
            <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
              {filtered.length} {filter !== 'ALL' ? filter.toLowerCase() : 'total'}
            </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: 20 }}>Assessment</th>
                  <th>Status</th>
                  <th>Mode</th>
                  <th>Findings</th>
                  <th>Summary</th>
                  <th>Created</th>
                  <th style={{ paddingRight: 20 }}></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(a => (
                  <tr key={a.id} onClick={() => navigate(`/assessments/${a.id}`)} style={{ cursor: 'pointer' }}>
                    <td style={{ paddingLeft: 20 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{a.name}</div>
                      <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Target size={10} /> {a.target}
                      </div>
                    </td>
                    <td><StatusBadge status={a.status} /></td>
                    <td>
                      {a.execution_mode?.includes('SIMULATED') ? (
                        <span className="badge" style={{ color: 'var(--state-warning)', borderColor: 'var(--state-warning)' }}>SIMULATED</span>
                      ) : (
                        <span className="badge" style={{ color: 'var(--state-success)', borderColor: 'var(--state-success)' }}>HEXSTRIKE</span>
                      )}
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 600, color: a.findings_count > 0 ? 'var(--state-error)' : 'var(--text-muted)' }}>
                        {a.findings_count}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)', maxWidth: 200, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {a.validation_summary || '—'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        <Clock size={10} /> {formatDate(a.created_at as unknown as string)}
                      </div>
                    </td>
                    <td style={{ paddingRight: 20 }}>
                      <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="empty-state" style={{ flex: 1 }}>
          <div style={{ marginBottom: 16, color: 'var(--border-hover)' }}><Activity size={48} strokeWidth={1} /></div>
          <div className="empty-state-title">NO ASSESSMENTS</div>
          <div className="empty-state-text">
            {filter !== 'ALL' ? `No ${filter.toLowerCase()} assessments found.` : 'Create your first assessment to begin an intelligence cycle.'}
          </div>
          {filter === 'ALL' && (
            <button className="btn btn-primary" onClick={() => navigate('/assessments/new')} style={{ marginTop: 24 }}>
              + NEW ASSESSMENT
            </button>
          )}
        </div>
      )}
    </div>
  );
}
