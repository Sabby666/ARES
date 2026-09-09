import { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  Search, Brain, ShieldCheck, FileText, Lock, AlertTriangle, ExternalLink, Play
} from 'lucide-react';
import { api, AssessmentDetail as AssessmentType, Finding, ActivityItem, createWebSocket } from '../services/api';
import { StatusBadge } from './Dashboard';
import AresCore from '../components/ares-core/AresCore';

const PIPELINE_STAGES = [
  { key: 'POLICY_CHECK', label: 'POLICY', icon: Lock },
  { key: 'RECON', label: 'RECON', icon: Search },
  { key: 'ANALYSIS', label: 'ANALYSIS', icon: AlertTriangle },
  { key: 'LLM_REASONING', label: 'REASONING', icon: Brain },
  { key: 'VALIDATION', label: 'VALIDATION', icon: ShieldCheck },
  { key: 'EVIDENCE', label: 'EVIDENCE', icon: FileText },
  { key: 'REPORTING', label: 'REPORT', icon: FileText },
];

function getStageState(currentStatus: string, stageKey: string): string {
  const stageOrder = PIPELINE_STAGES.map(s => s.key);
  const currentIdx = stageOrder.indexOf(currentStatus);
  const stageIdx = stageOrder.indexOf(stageKey);

  if (currentStatus === 'COMPLETED') return 'completed';
  if (currentStatus === 'FAILED') {
    if (stageIdx <= currentIdx) return stageIdx === currentIdx ? 'failed' : 'completed';
    return 'pending';
  }
  if (currentStatus === 'BLOCKED') {
    if (stageIdx === 0) return 'failed';
    return 'pending';
  }
  if (currentStatus === 'CREATED') return 'pending';

  if (stageIdx < currentIdx) return 'completed';
  if (stageIdx === currentIdx) return 'active';
  return 'pending';
}

export default function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const [assessment, setAssessment] = useState<AssessmentType | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const activityEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const [starting, setStarting] = useState(false);

  const fetchData = async () => {
    if (!id) return;
    try {
      const [a, f, act] = await Promise.all([
        api.getAssessment(id),
        api.getFindings(id).catch(() => []),
        api.getActivity(id).catch(() => []),
      ]);
      setAssessment(a);
      setFindings(f);
      setActivity(act);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAssessment = async () => {
    if (!id) return;
    setStarting(true);
    try {
      await api.startAssessment(id);
      setAssessment(prev => prev ? { ...prev, status: 'POLICY_CHECK' } : prev);
      fetchData();
    } catch (err: any) {
      console.error(err);
    } finally {
      setStarting(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    const ws = createWebSocket(id);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === 'activity') {
        setActivity(prev => [...prev, {
          id: Date.now().toString(),
          assessment_id: id,
          agent: data.agent,
          message: data.message,
          log_type: data.log_type,
          timestamp: data.timestamp,
        }]);
      }
      if (data.event === 'status') {
        setAssessment(prev => prev ? { ...prev, status: data.status } : prev);
        if (data.status === 'COMPLETED' || data.status === 'FAILED' || data.status === 'BLOCKED') {
          fetchData();
        }
      }
    };

    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 15000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [id]);

  useEffect(() => {
    activityEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activity]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!assessment) return <div className="empty-state"><div className="empty-state-title">ASSESSMENT NOT FOUND</div></div>;

  const isRunning = !['COMPLETED', 'FAILED', 'BLOCKED', 'CREATED'].includes(assessment.status);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, height: '100%' }}>
      {/* Top Section: Overview & Core */}
      <div className="grid-2" style={{ alignItems: 'start' }}>
        
        {/* Left: Meta & Status */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div className="panel">
            <div className="panel-header" style={{ marginBottom: 8 }}>
              <span className="panel-title">Assessment Target</span>
              <StatusBadge status={assessment.status} />
            </div>
            <h1 style={{ fontFamily: 'var(--font-mono)', fontSize: 24, color: 'var(--accent-primary)', wordBreak: 'break-all' }}>
              {assessment.target}
            </h1>
            <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
              <span>ID: <code style={{ color: 'var(--text-secondary)' }}>{assessment.id.slice(0,8)}</code></span>
              {assessment.duration_ms && <span>DURATION: {(assessment.duration_ms / 1000).toFixed(1)}s</span>}
            </div>
            {['CREATED', 'FAILED', 'BLOCKED'].includes(assessment.status) && (
              <button
                className="btn btn-primary"
                onClick={handleStartAssessment}
                disabled={starting}
                style={{ marginTop: 16, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '12px 16px', fontSize: 13, fontWeight: 700 }}
              >
                <Play size={14} /> {starting ? 'STARTING PIPELINE...' : 'START ASSESSMENT'}
              </button>
            )}
          </div>

          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Execution State</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {PIPELINE_STAGES.map((stage) => {
                const state = getStageState(assessment.status, stage.key);
                let color = 'var(--text-muted)';
                let bg = 'transparent';
                let border = 'var(--border-primary)';
                
                if (state === 'active') { color = 'var(--accent-primary)'; border = 'var(--accent-primary)'; bg = 'rgba(37, 99, 235, 0.1)'; }
                if (state === 'completed') { color = 'var(--state-success)'; border = 'var(--state-success)'; bg = 'rgba(16, 185, 129, 0.1)'; }
                if (state === 'failed') { color = 'var(--state-error)'; border = 'var(--state-error)'; bg = 'rgba(239, 68, 68, 0.1)'; }

                return (
                  <div key={stage.key} style={{
                    display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px',
                    border: `1px solid ${border}`, borderRadius: 'var(--radius-xs)', background: bg,
                    color: color, fontSize: 11, fontWeight: 600, fontFamily: 'var(--font-display)'
                  }}>
                    <stage.icon size={12} />
                    {stage.label}
                  </div>
                );
              })}
            </div>
          </div>
          
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Findings Summary</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 16, color: 'var(--state-error)' }}>{findings.length}</span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {['Critical', 'High', 'Medium', 'Low', 'Info'].map(sev => {
                const count = findings.filter(f => f.severity === sev).length;
                return (
                  <div key={sev} style={{ flex: 1, textAlign: 'center', padding: '8px 0', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-xs)' }}>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{sev}</div>
                    <div style={{ fontSize: 14, fontFamily: 'var(--font-mono)', color: count > 0 ? severityColor(sev) : 'var(--text-muted)' }}>{count}</div>
                  </div>
                );
              })}
            </div>
            {assessment.status === 'COMPLETED' && (
              <a href={api.getReportHtml(assessment.id)} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ marginTop: 16, width: '100%' }}>
                <ExternalLink size={14} /> EXTRACT REPORT
              </a>
            )}
          </div>
        </div>

        {/* Right: Core Visualization */}
        <div className="panel" style={{ padding: 0, height: 400, overflow: 'hidden' }}>
          <AresCore status={assessment.status} />
        </div>
      </div>

      {/* Bottom Section: Activity Stream & Detailed Findings */}
      <div className="grid-2">
        <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', maxHeight: 600 }}>
          <div className="panel-header" style={{ marginBottom: 0 }}>
            <span className="panel-title">Live Intelligence Stream</span>
            {isRunning && <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
          </div>
          <div className="activity-stream" style={{ flex: 1, overflowY: 'auto', padding: '16px 0' }}>
            {activity.map(a => (
              <div key={a.id} className="activity-log-line">
                <span className="log-time">{new Date(a.timestamp).toLocaleTimeString([], { hour12: false })}</span>
                <span className="log-agent">[{a.agent}]</span>
                <span className="log-message" style={{ color: a.log_type === 'error' ? 'var(--state-error)' : 'var(--text-secondary)' }}>
                  {a.message}
                </span>
              </div>
            ))}
            <div ref={activityEndRef} />
            {activity.length === 0 && (
              <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>WAITING FOR TELEMETRY...</div>
            )}
          </div>
        </div>

        <div className="panel" style={{ flex: 1, maxHeight: 600, overflowY: 'auto', padding: '0' }}>
          <div className="panel-header" style={{ position: 'sticky', top: 0, background: 'var(--bg-panel)', zIndex: 10, padding: '20px', borderBottom: '1px solid var(--border-primary)' }}>
            <span className="panel-title">Detailed Intelligence</span>
          </div>
          <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
            {findings.length > 0 ? findings.map(f => (
              <FindingItem key={f.id} finding={f} />
            )) : (
              <div className="empty-state" style={{ border: 'none' }}>
                <div className="empty-state-text">NO FINDINGS RECORDED</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function FindingItem({ finding }: { finding: Finding }) {
  return (
    <div style={{ border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', background: 'var(--bg-primary)' }}>
      <div style={{ padding: 12, borderBottom: '1px solid var(--border-primary)', display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{finding.title}</span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{finding.category} • {finding.endpoint}</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <span style={{ color: severityColor(finding.severity), fontSize: 10, fontFamily: 'var(--font-display)', fontWeight: 800 }}>{finding.severity.toUpperCase()}</span>
          <span style={{ color: 'var(--text-muted)', fontSize: 10, fontFamily: 'var(--font-mono)' }}>CONF: {(finding.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
      <div style={{ padding: 12, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
        {finding.description}
        <details style={{ marginTop: 8 }}>
          <summary style={{ color: 'var(--accent-primary)', cursor: 'pointer', outline: 'none' }}>+ PROVENANCE & RECOMMENDATION</summary>
          <div style={{ marginTop: 8, paddingLeft: 8, borderLeft: '2px solid var(--border-primary)' }}>
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>REASONING:</span> {finding.reasoning}
            </div>
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>FIX:</span> {finding.recommendation}
            </div>
            {finding.evidence && finding.evidence.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>EVIDENCE:</span>
                {finding.evidence.map(ev => (
                  <div key={ev.id} style={{ marginTop: 4, background: 'var(--bg-input)', padding: 8, borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-hover)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 4 }}>
                      <span>{ev.source}</span>
                      {ev.source_type === 'MOCK' && <span style={{ color: 'var(--state-warning)' }}>[SIMULATED]</span>}
                    </div>
                    <pre style={{ margin: 0, overflowX: 'auto', maxHeight: 150, fontSize: 11 }}>{ev.content}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        </details>
      </div>
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
