import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink, FileText } from 'lucide-react';
import { api, AssessmentSummary } from '../services/api';

export default function Reports() {
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.listAssessments().then(setAssessments).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  const completed = assessments.filter(a => a.status === 'COMPLETED');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <h1 className="page-title">Intelligence Archive</h1>
        <p className="page-description">Retrieved Security Reports</p>
      </div>

      {completed.length > 0 ? (
        <div className="panel" style={{ padding: 0 }}>
          <div className="panel-header" style={{ padding: '20px 20px 12px 20px', marginBottom: 0 }}>
            <span className="panel-title">Completed Cycles</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: 20 }}>Target</th>
                  <th>Mode</th>
                  <th>Findings</th>
                  <th>Summary</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {completed.map(a => (
                  <tr key={a.id}>
                    <td style={{ paddingLeft: 20 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{a.name}</div>
                      <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{a.target}</div>
                    </td>
                    <td>
                      {a.execution_mode?.includes('SIMULATED') ? (
                        <span className="badge" style={{ color: 'var(--state-warning)', borderColor: 'var(--state-warning)' }}>SIMULATED</span>
                      ) : (
                        <span className="badge" style={{ color: 'var(--state-error)', borderColor: 'var(--state-error)' }}>REAL</span>
                      )}
                    </td>
                    <td><span style={{ fontFamily: 'var(--font-mono)', color: a.findings_count > 0 ? 'var(--state-error)' : 'var(--text-muted)' }}>{a.findings_count}</span></td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)', maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {a.validation_summary || 'N/A'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          className="btn btn-secondary"
                          onClick={() => navigate(`/assessments/${a.id}`)}
                          style={{ padding: '6px 12px', fontSize: 11 }}
                        >
                          TRACE
                        </button>
                        <a
                          href={api.getReportHtml(a.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-primary"
                          style={{ padding: '6px 12px', fontSize: 11 }}
                        >
                          <ExternalLink size={12} /> EXTRACT
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div style={{ marginBottom: 16, color: 'var(--border-hover)' }}><FileText size={48} strokeWidth={1} /></div>
          <div className="empty-state-title">NO ARCHIVES</div>
          <div className="empty-state-text">
            No completed assessments yet.<br />
            Complete an intelligence cycle to generate a retrievable report.
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/assessments/new')} style={{ marginTop: 24 }}>
            + NEW ASSESSMENT
          </button>
        </div>
      )}
    </div>
  );
}
