import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function NewAssessment() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [target, setTarget] = useState('http://localhost/DVWA/');
  const [scope, setScope] = useState('Full application scan');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.createAssessment({ name: name || 'DVWA Security Assessment', target, scope, description });
      navigate(`/assessments/${res.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize intelligence cycle');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24, maxWidth: 800 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <h1 className="page-title">Initialize Core</h1>
        <p className="page-description">Configure targeting parameters for multi-agent execution</p>
      </div>

      <div className="panel" style={{ padding: 0 }}>
        <div className="panel-header" style={{ padding: '20px 20px 12px 20px', marginBottom: 0 }}>
          <span className="panel-title">System Constraint</span>
          <span className="badge" style={{ color: 'var(--state-warning)', borderColor: 'var(--state-warning)' }}>RESTRICTED</span>
        </div>
        <div style={{ padding: '20px', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          This system uses <strong>simulated tools only</strong>.
          All scanning is mocked — no real network requests, exploits, or attacks are performed.
          Only <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>localhost</code>,{' '}
          <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>127.0.0.1</code>, and{' '}
          <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>demo.local</code> targets are authorized by the Policy Gateway.
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        <div className="panel" style={{ padding: 32 }}>
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Task Name</label>
              <input
                className="form-input"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g., LOCAL_VALIDATION_01"
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Target Origin</label>
              <input
                className="form-input"
                value={target}
                onChange={e => setTarget(e.target.value)}
                placeholder="http://localhost:3000"
                required
              />
              <span style={{ fontSize: 11, color: 'var(--state-error)', marginTop: 8, display: 'block', fontFamily: 'var(--font-mono)' }}>
                MUST MATCH LOCALHOST POLICY
              </span>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Execution Scope</label>
            <input
              className="form-input"
              value={scope}
              onChange={e => setScope(e.target.value)}
              placeholder="Full application scan"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mission Brief (Optional)</label>
            <textarea
              className="form-textarea"
              style={{ minHeight: 100 }}
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Provide context for the LLM Reasoner..."
            />
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid var(--state-error)',
              borderRadius: 'var(--radius-sm)', padding: '12px 16px', marginBottom: 24,
              color: 'var(--state-error)', fontSize: 12, fontFamily: 'var(--font-mono)'
            }}>
              [ERROR] {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: 16, marginTop: 16 }}>
            <button type="submit" className="btn btn-primary" disabled={loading || !name || !target}>
              {loading ? 'INITIALIZING...' : 'LAUNCH CORE'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}>
              ABORT
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
