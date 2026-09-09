import { Target, Search, ShieldCheck, Cpu, Database } from 'lucide-react';

export default function IntelligenceFlow({ status }: { status: string }) {
  const steps = [
    { id: 'RECON', label: 'RECON', icon: Target },
    { id: 'ANALYSIS', label: 'ANALYZE', icon: Search },
    { id: 'POLICY_CHECK', label: 'POLICY', icon: ShieldCheck },
    { id: 'TOOL_EXECUTION', label: 'TOOLS', icon: Cpu },
    { id: 'EVIDENCE', label: 'EVIDENCE', icon: Database },
  ];

  const currentIdx = steps.findIndex(s => s.id === status);
  
  return (
    <div className="panel" style={{ flex: 1 }}>
      <div className="panel-header">
        <span className="panel-title">INTELLIGENCE FLOW</span>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{status}</span>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '12px 0' }}>
        {steps.map((step, idx) => {
          const isCompleted = currentIdx > idx;
          const isActive = currentIdx === idx;
          
          let color = 'var(--text-muted)';
          let dotBg = 'transparent';
          let border = '1px dashed var(--border-hover)';
          
          if (isCompleted) {
            color = 'var(--state-success)';
            dotBg = 'var(--state-success)';
            border = '1px solid var(--state-success)';
          } else if (isActive) {
            color = 'var(--accent-primary)';
            dotBg = 'var(--accent-primary)';
            border = '1px solid var(--accent-primary)';
          }

          return (
            <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 16, position: 'relative' }}>
              {/* Vertical connector line */}
              {idx < steps.length - 1 && (
                <div style={{
                  position: 'absolute',
                  left: 11,
                  top: 24,
                  bottom: -16,
                  width: 1,
                  background: isCompleted ? 'var(--state-success)' : 'var(--border-hover)',
                  borderRight: isCompleted ? 'none' : '1px dashed var(--bg-panel)'
                }} />
              )}
              
              <div style={{
                width: 24, height: 24, borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border, background: isActive ? 'rgba(37,99,235,0.1)' : 'var(--bg-panel)',
                color, zIndex: 2
              }}>
                <step.icon size={12} />
              </div>
              
              <div style={{
                fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 600, letterSpacing: 1, color: isActive || isCompleted ? 'var(--text-primary)' : 'var(--text-muted)'
              }}>
                {step.label}
              </div>
              
              <div style={{ marginLeft: 'auto', fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                {isActive ? 'Processing...' : isCompleted ? 'Complete' : 'Waiting...'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
