import { ShieldAlert } from 'lucide-react';

export default function ThreatGauge({ findings }: { findings: any[] }) {
  const critical = findings.filter(f => f.severity === 'CRITICAL').length;
  const high = findings.filter(f => f.severity === 'HIGH').length;
  const medium = findings.filter(f => f.severity === 'MEDIUM').length;
  const low = findings.filter(f => f.severity === 'LOW').length;

  const total = critical + high + medium + low;
  const hasThreats = total > 0;

  return (
    <div className="panel" style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <div className="panel-header" style={{ width: '100%', marginBottom: 32 }}>
        <span className="panel-title">THREAT LEVEL</span>
      </div>

      <div style={{ position: 'relative', width: 200, height: 100, display: 'flex', justifyContent: 'center' }}>
        {/* SVG Semi-circle gauge */}
        <svg width="200" height="100" viewBox="0 0 200 100" style={{ position: 'absolute', top: 0 }}>
          {/* Background arc */}
          <path d="M 10 100 A 90 90 0 0 1 190 100" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
          
          {/* Colored arcs based on threat level */}
          {hasThreats ? (
            <path d="M 10 100 A 90 90 0 0 1 190 100" fill="none" stroke={critical > 0 ? 'var(--state-error)' : high > 0 ? 'var(--state-warning)' : 'var(--state-warning)'} strokeWidth="4" strokeDasharray="283" strokeDashoffset="141" />
          ) : (
            <path d="M 10 100 A 90 90 0 0 1 190 100" fill="none" stroke="var(--state-success)" strokeWidth="4" />
          )}
          
          {/* Tick marks */}
          <line x1="100" y1="10" x2="100" y2="15" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
          <line x1="36" y1="36" x2="40" y2="40" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
          <line x1="164" y1="36" x2="160" y2="40" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
        </svg>

        <div style={{ position: 'absolute', top: 40, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <ShieldAlert size={20} style={{ color: hasThreats ? (critical > 0 ? 'var(--state-error)' : 'var(--state-warning)') : 'var(--state-success)' }} />
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, marginTop: 8, letterSpacing: 0.5, color: 'var(--text-primary)' }}>
            {hasThreats ? (critical > 0 ? 'CRITICAL THREAT' : 'ELEVATED RISK') : 'NO ACTIVE THREATS'}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
            {hasThreats ? `${total} Vulnerabilities` : 'System is in normal state'}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', width: '100%', justifyContent: 'space-around', marginTop: 24 }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 9, fontFamily: 'var(--font-display)', color: 'var(--text-muted)' }}>CRITICAL</div>
          <div style={{ fontSize: 16, fontFamily: 'var(--font-mono)', color: critical > 0 ? 'var(--state-error)' : 'var(--text-secondary)' }}>{critical}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 9, fontFamily: 'var(--font-display)', color: 'var(--text-muted)' }}>HIGH</div>
          <div style={{ fontSize: 16, fontFamily: 'var(--font-mono)', color: high > 0 ? 'var(--state-warning)' : 'var(--text-secondary)' }}>{high}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 9, fontFamily: 'var(--font-display)', color: 'var(--text-muted)' }}>MEDIUM</div>
          <div style={{ fontSize: 16, fontFamily: 'var(--font-mono)', color: medium > 0 ? 'var(--state-warning)' : 'var(--text-secondary)' }}>{medium}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 9, fontFamily: 'var(--font-display)', color: 'var(--text-muted)' }}>LOW</div>
          <div style={{ fontSize: 16, fontFamily: 'var(--font-mono)', color: low > 0 ? 'var(--state-success)' : 'var(--text-secondary)' }}>{low}</div>
        </div>
      </div>
    </div>
  );
}
