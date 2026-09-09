import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, DashboardData } from '../services/api';
import AresCore from '../components/ares-core/AresCore';
import IntelligenceFlow from '../components/IntelligenceFlow';
import ThreatGauge from '../components/ThreatGauge';
import SystemFeed from '../components/SystemFeed';
import { Target, Activity, Database, ShieldAlert, CheckCircle, Crosshair } from 'lucide-react';

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    
    // Create a timeout promise to reject after 5 seconds if backend hangs
    const fetchWithTimeout = async () => {
      const timeoutId = setTimeout(() => {
        if (isMounted && loading) {
          setError('CONTROL SERVICE OFFLINE');
          setLoading(false);
        }
      }, 5000);
      
      try {
        const d = await api.getDashboard();
        if (isMounted) setData(d);
      } catch (e: any) {
        if (isMounted) {
          console.error(e);
          setError('CONTROL SERVICE OFFLINE');
        }
      } finally {
        clearTimeout(timeoutId);
        if (isMounted) setLoading(false);
      }
    };
    
    fetchWithTimeout();
    
    const interval = setInterval(() => {
      api.getDashboard().then(d => {
        if (isMounted) {
          setData(d);
          setError(null);
        }
      }).catch(console.error);
    }, 5000);
    
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (error) return (
    <div className="empty-state" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ color: 'var(--state-error)', marginBottom: 16 }}>
        <ShieldAlert size={48} />
      </div>
      <div className="empty-state-title">{error}</div>
      <div className="empty-state-text">The backend API is unreachable or hanging.</div>
    </div>
  );

  const s = data?.stats;
  
  // Determine overall core state from recent assessments
  let coreState = 'IDLE';
  let activeAssessment = data?.recent_assessments?.[0];
  if (s?.running && s.running > 0 && activeAssessment) {
    // Map backend status to UI CoreState
    const st = activeAssessment.status;
    if (st === 'POLICY_CHECK') coreState = 'POLICY_CHECK';
    else if (st === 'RECON') coreState = 'RECON';
    else if (st === 'ANALYSIS' || st === 'LLM_REASONING') coreState = 'ANALYSIS';
    else if (st === 'VALIDATION' || st === 'EVIDENCE' || st === 'REPORTING') coreState = 'EVIDENCE';
    else coreState = 'TOOL_EXECUTION'; // Fallback for active state
  } else {
    coreState = 'IDLE';
  }


  return (
    <div className="dashboard-layout">
      {/* ────────────────────────────────────────────────────────
          MAIN COLUMN (Left/Center)
          ──────────────────────────────────────────────────────── */}
      <div className="dashboard-main-col">
        {/* ARES Core Panel */}
        <div className="panel" style={{ padding: 0, border: 'none', background: 'transparent' }}>
          <div style={{ padding: '0 0 24px 0', display: 'flex', flexDirection: 'column', gap: 4 }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, letterSpacing: 1 }}>INTELLIGENCE CORE</h2>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: 8 }}>
              AI-DRIVEN SECURITY ORCHESTRATION
              <div className="topbar-pill" style={{ color: 'var(--state-success)', borderColor: 'rgba(16,185,129,0.2)', marginLeft: 16 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'var(--state-success)' }} />
                SYSTEM ONLINE
              </div>
            </div>
          </div>
          
          <div className="core-container" style={{ height: 480, border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)' }}>
            <AresCore status={coreState as any} />
            <div style={{ position: 'absolute', bottom: 24, left: 24, zIndex: 10 }}>
              <div className="topbar-pill" style={{ color: 'var(--accent-primary)', borderColor: 'rgba(37,99,235,0.2)', background: 'rgba(10,14,23,0.8)', backdropFilter: 'blur(4px)' }}>
                <Crosshair size={10} />
                CORE STATUS: {coreState}
              </div>
            </div>
          </div>
        </div>

        {/* Lower Core Band (Metrics) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          <div className="panel" style={{ padding: '16px 20px', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>OPERATIONS</span>
              <Target size={14} style={{ color: 'var(--accent-primary)' }} />
            </div>
            <div>
              <div style={{ fontSize: 28, fontFamily: 'var(--font-sans)', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1 }}>{s?.total_assessments ?? 0}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, textTransform: 'uppercase' }}>TOTAL LAUNCHED</div>
            </div>
          </div>
          
          <div className="panel" style={{ padding: '16px 20px', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>ACTIVE AGENTS</span>
              <Activity size={14} style={{ color: 'var(--state-info)' }} />
            </div>
            <div>
              <div style={{ fontSize: 28, fontFamily: 'var(--font-sans)', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1 }}>{s?.running ?? 0}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, textTransform: 'uppercase' }}>CURRENTLY RUNNING</div>
            </div>
          </div>

          <div className="panel" style={{ padding: '16px 20px', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>FINDINGS</span>
              <ShieldAlert size={14} style={{ color: 'var(--state-error)' }} />
            </div>
            <div>
              <div style={{ fontSize: 28, fontFamily: 'var(--font-sans)', fontWeight: 600, color: 'var(--state-error)', lineHeight: 1 }}>{s?.total_findings ?? 0}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, textTransform: 'uppercase' }}>IDENTIFIED VULNS</div>
            </div>
          </div>

          <div className="panel" style={{ padding: '16px 20px', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>EVIDENCE</span>
              <Database size={14} style={{ color: 'var(--state-success)' }} />
            </div>
            <div>
              <div style={{ fontSize: 28, fontFamily: 'var(--font-sans)', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1 }}>{s?.total_evidence ?? 0}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, textTransform: 'uppercase' }}>COLLECTED</div>
            </div>
          </div>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────
          SIDE COLUMN (Right)
          ──────────────────────────────────────────────────────── */}
      <div className="dashboard-side-col">
        
        {/* Active Assessment */}
        <div className="panel">
          <div className="panel-header" style={{ marginBottom: 16 }}>
            <span className="panel-title">ACTIVE ASSESSMENT</span>
            <Crosshair size={14} style={{ color: 'var(--accent-primary)' }} />
          </div>
          
          {activeAssessment && ['CREATED', 'POLICY_CHECK', 'RECON', 'ANALYSIS', 'LLM_REASONING', 'VALIDATION'].includes(activeAssessment.status) ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{activeAssessment.name || activeAssessment.target}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>TARGET: {activeAssessment.target}</div>
              <div style={{ marginTop: 8 }}>
                <StatusBadge status={activeAssessment.status} />
              </div>
              <button className="btn btn-primary" style={{ marginTop: 16, width: '100%' }} onClick={() => navigate(`/assessments/${activeAssessment.id}`)}>
                VIEW DETAILS
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>No Active Assessment</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Create or start an assessment to initialize the engine.</div>
              <button className="btn btn-primary" style={{ marginTop: 16, width: '100%', background: 'rgba(37,99,235,0.1)', color: 'var(--accent-primary)', border: '1px solid rgba(37,99,235,0.3)' }} onClick={() => navigate('/assessments/new')}>
                + New Assessment
              </button>
            </div>
          )}
        </div>

        {/* Intelligence Flow */}
        <IntelligenceFlow status={coreState} />

      </div>

      {/* ────────────────────────────────────────────────────────
          BOTTOM ROW
          ──────────────────────────────────────────────────────── */}
      <div className="dashboard-bottom-row">
        {/* Live System Feed */}
        <SystemFeed />

        {/* Threat Level Gauge */}
        <ThreatGauge findings={data?.recent_assessments?.flatMap(() => [
          ...Array(s?.critical_findings ?? 0).fill({ severity: 'CRITICAL' }),
          ...Array(s?.high_findings ?? 0).fill({ severity: 'HIGH' }),
          ...Array(s?.medium_findings ?? 0).fill({ severity: 'MEDIUM' }),
          ...Array(s?.low_findings ?? 0).fill({ severity: 'LOW' }),
        ]) ?? []} />

        {/* Recent Assessments Archive */}
        <div className="panel">
          <div className="panel-header" style={{ marginBottom: 0 }}>
            <span className="panel-title">RECENT ASSESSMENTS</span>
            <button style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)', padding: '4px 8px', borderRadius: 4, fontSize: 10, cursor: 'pointer' }} onClick={() => navigate('/assessments')}>View All</button>
          </div>
          
          {data?.recent_assessments && data.recent_assessments.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {data.recent_assessments.slice(0, 5).map(a => (
                <div
                  key={a.id}
                  onClick={() => navigate(`/assessments/${a.id}`)}
                  style={{ padding: '10px 0', borderBottom: '1px solid var(--border-primary)', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{a.name}</div>
                    <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{a.target}</div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                    <StatusBadge status={a.status} />
                    {a.findings_count > 0 && (
                      <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--state-error)' }}>{a.findings_count} findings</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '32px 0', opacity: 0.5 }}>
               <Crosshair size={32} style={{ color: 'var(--border-hover)', marginBottom: 12 }} strokeWidth={1} />
               <div style={{ fontSize: 12, color: 'var(--text-primary)', marginBottom: 4 }}>No assessments yet</div>
               <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Create your first assessment</div>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const running = ['policy_check', 'recon', 'analysis', 'llm_reasoning', 'validation', 'evidence', 'reporting'];
  let cls = 'badge ';
  let icon = null;

  if (s === 'completed') {
    cls += 'badge-status-completed';
    icon = <CheckCircle size={10} />;
  }
  else if (running.includes(s)) {
    cls += 'badge-status-running';
    icon = <Activity size={10} />;
  }
  else if (s === 'created') {
    cls += 'badge-status-created';
  }
  else if (s === 'failed') {
    cls += 'badge-status-failed';
  }
  else if (s === 'blocked') {
    cls += 'badge-status-blocked';
  }
  else {
    cls += 'badge-status-created';
  }

  return (
    <span className={cls} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      {icon}
      {status.replace(/_/g, ' ')}
    </span>
  );
}
