import { useEffect, useState } from 'react';
import { api, AgentInfo, ToolInfo } from '../services/api';

const AGENT_ORDER = [
  'Controller',
  'PolicyAgent',
  'ReconAgent',
  'AnalyzerAgent',
  'LLMReasoner',
  'ValidationAgent'
];

export default function Agents() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [toolProvider, setToolProvider] = useState<string>('MOCK');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.listAgents(), api.listTools(), api.getSettings().catch(() => null)])
      .then(([a, t, s]) => { 
        const sorted = [...a].sort((x, y) => {
          const ix = AGENT_ORDER.indexOf(x.name);
          const iy = AGENT_ORDER.indexOf(y.name);
          return (ix > -1 ? ix : 99) - (iy > -1 ? iy : 99);
        });
        setAgents(sorted);
        setTools(t);
        if (s) setToolProvider(s.tool_provider);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <h1 className="page-title">Orchestration Topology</h1>
        <p className="page-description">ARES Multi-Agent Control Structure & Tool Gateway</p>
      </div>

      <div className="grid-2">
        {/* Agent Topology Panel */}
        <div className="panel" style={{ padding: 0 }}>
          <div className="panel-header" style={{ padding: '20px 20px 12px 20px', marginBottom: 0 }}>
            <span className="panel-title">Active Node Topology</span>
          </div>
          <div style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 0, position: 'relative' }}>
            {/* A simple vertical topological tree */}
            {agents.map((agent, i) => (
              <div key={agent.name} style={{ display: 'flex', gap: 24, position: 'relative' }}>
                
                {/* Connecting Line */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                  <div style={{ 
                    width: 12, height: 12, borderRadius: '50%', 
                    background: 'var(--bg-panel)', border: '2px solid var(--accent-primary)',
                    zIndex: 2, position: 'relative'
                  }} />
                  {i < agents.length - 1 && (
                    <div style={{ width: 2, flex: 1, background: 'var(--border-primary)', margin: '-2px 0' }} />
                  )}
                </div>

                {/* Node Details */}
                <div style={{ flex: 1, paddingBottom: i < agents.length - 1 ? 32 : 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{agent.name.toUpperCase()}</div>
                      <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)', marginTop: 2 }}>{agent.role}</div>
                    </div>
                    <span className="badge" style={{ color: 'var(--state-success)', borderColor: 'var(--state-success)' }}>{agent.status.toUpperCase()}</span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    {agent.description}
                  </div>
                </div>

              </div>
            ))}
          </div>
        </div>

        {/* Tools Panel */}
        <div className="panel" style={{ padding: 0 }}>
          <div className="panel-header" style={{ padding: '20px 20px 12px 20px', marginBottom: 0 }}>
            <span className="panel-title">Tool Gateway Interface</span>
            {toolProvider === 'HEXSTRIKE' ? (
              <span className="badge" style={{ color: 'var(--state-success)', borderColor: 'var(--state-success)' }}>HEXSTRIKE / LIVE</span>
            ) : (
              <span className="badge" style={{ color: 'var(--state-warning)', borderColor: 'var(--state-warning)' }}>SIMULATED / MOCK</span>
            )}
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: 20 }}>Executable</th>
                  <th>Capability</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {tools.map((tool, idx) => (
                  <tr key={tool.id || tool.name || idx}>
                    <td style={{ paddingLeft: 20, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                      {tool.name}
                    </td>
                    <td style={{ fontSize: 12 }}>{tool.description}</td>
                    <td><span className="badge" style={{ color: 'var(--text-muted)', borderColor: 'var(--border-primary)' }}>{tool.tool_type}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
