import { useEffect, useState, useCallback } from 'react';
import { api, AppSettings, ServiceHealth } from '../services/api';
import { RefreshCw, CheckCircle, XCircle, Clock, Shield } from 'lucide-react';

function StatusDot({ status }: { status: string }) {
  const color =
    status === 'ONLINE' ? 'var(--state-success)' :
    status === 'OFFLINE' ? 'var(--state-error)' :
    status === 'TIMEOUT' ? 'var(--state-warning)' :
    status === 'DISABLED' ? 'var(--text-muted)' :
    'var(--text-muted)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
      <span style={{ fontSize: 12, color, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{status}</span>
    </div>
  );
}

function ConfigRow({ label, value, masked }: { label: string; value: string | number | boolean | string[]; masked?: boolean }) {
  let display: string;
  if (masked) {
    display = value ? '••••••••  [CONFIGURED]' : 'NOT CONFIGURED';
  } else if (Array.isArray(value)) {
    display = value.join(', ');
  } else {
    display = String(value);
  }
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '10px 0', borderBottom: '1px solid var(--border-primary)' }}>
      <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', minWidth: 220, flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: 12, color: masked ? 'var(--text-muted)' : 'var(--text-secondary)', fontFamily: 'var(--font-mono)', textAlign: 'right', wordBreak: 'break-all' }}>
        {display}
      </span>
    </div>
  );
}

export default function Settings() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [health, setHealth] = useState<ServiceHealth | null>(null);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [healthRefreshing, setHealthRefreshing] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);

  const loadSettings = useCallback(() => {
    setLoadingSettings(true);
    api.getSettings()
      .then(setSettings)
      .catch(e => setSettingsError(e.message))
      .finally(() => setLoadingSettings(false));
  }, []);

  const loadHealth = useCallback(() => {
    setLoadingHealth(true);
    api.getSystemHealth()
      .then(setHealth)
      .catch(console.error)
      .finally(() => setLoadingHealth(false));
  }, []);

  const refreshHealth = useCallback(async () => {
    setHealthRefreshing(true);
    try {
      const h = await api.getSystemHealth();
      setHealth(h);
    } catch (e) {
      console.error(e);
    } finally {
      setHealthRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
    loadHealth();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 24 }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div>
          <h1 className="page-title">System Settings</h1>
          <p className="page-description">Read-only system configuration — safe observable state</p>
        </div>
        <div className="panel" style={{ padding: '6px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={12} style={{ color: 'var(--state-success)' }} />
          <span style={{ fontSize: 11, color: 'var(--state-success)', fontFamily: 'var(--font-mono)' }}>
            SECRETS MASKED
          </span>
        </div>
      </div>

      {/* Service Health */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Service Health</span>
          <button
            className="btn btn-secondary"
            style={{ fontSize: 10, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 6 }}
            onClick={refreshHealth}
            disabled={healthRefreshing}
          >
            <RefreshCw size={10} style={{ animation: healthRefreshing ? 'spin 1s linear infinite' : 'none' }} />
            {healthRefreshing ? 'CHECKING…' : 'REFRESH'}
          </button>
        </div>

        {loadingHealth ? (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
            <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Checking services…
          </div>
        ) : health ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            {[
              { name: 'ARES Backend', key: 'backend', info: health.backend },
              { name: 'HexStrike', key: 'hexstrike', info: health.hexstrike, note: `Provider: ${health.tool_provider}` },
              { name: 'OmniRoute', key: 'omniroute', info: health.omniroute, note: `Provider: ${health.llm_provider}` },
            ].map(svc => (
              <div key={svc.key} style={{ padding: '16px', background: 'var(--bg-input)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: 11, fontFamily: 'var(--font-display)', color: 'var(--text-muted)', marginBottom: 10, textTransform: 'uppercase' }}>{svc.name}</div>
                <StatusDot status={(svc.info as any)?.status || 'UNKNOWN'} />
                {svc.note && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, fontFamily: 'var(--font-mono)' }}>{svc.note}</div>}
                {(svc.info as any)?.error && (
                  <div style={{ fontSize: 10, color: 'var(--state-error)', marginTop: 6, fontFamily: 'var(--font-mono)' }}>{(svc.info as any).error}</div>
                )}
                {(svc.info as any)?.note && (
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6, fontFamily: 'var(--font-mono)' }}>{(svc.info as any).note}</div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>Unable to fetch service health.</div>
        )}
      </div>

      {settingsError && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)', color: 'var(--state-error)', fontSize: 12 }}>
          {settingsError}
        </div>
      )}

      {loadingSettings ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : settings ? (
        <div className="grid-2">
          {/* Application */}
          <div className="panel">
            <div className="panel-header"><span className="panel-title">Application</span></div>
            <div>
              <ConfigRow label="app_name" value={settings.app_name} />
              <ConfigRow label="app_version" value={settings.app_version} />
              <ConfigRow label="app_env" value={settings.app_env} />
              <ConfigRow label="database_type" value={settings.database_type} />
              <ConfigRow label="database_path" value={settings.database_path} />
            </div>
          </div>

          {/* Execution */}
          <div className="panel">
            <div className="panel-header"><span className="panel-title">Execution Configuration</span></div>
            <div>
              <ConfigRow label="tool_provider" value={settings.tool_provider} />
              <ConfigRow label="llm_provider" value={settings.llm_provider} />
              <ConfigRow label="llm_model" value={settings.llm_model} />
              <ConfigRow label="tool_timeout_seconds" value={settings.tool_timeout_seconds} />
              <ConfigRow label="llm_timeout_seconds" value={settings.llm_timeout_seconds} />
            </div>
          </div>

          {/* HexStrike */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">HexStrike Integration</span>
              <span className="badge" style={{ color: 'var(--state-success)', borderColor: 'var(--state-success)' }}>LIVE VERIFIED</span>
            </div>
            <div>
              <ConfigRow label="hexstrike_base_url" value={settings.hexstrike_base_url} />
              <ConfigRow label="hexstrike_api_key" value={settings.hexstrike_api_key_configured} masked />
            </div>
            <div style={{ marginTop: 16, padding: '10px 12px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 'var(--radius-xs)' }}>
              <div style={{ fontSize: 11, color: 'var(--state-success)', fontFamily: 'var(--font-mono)', marginBottom: 4 }}>PHASE 14 — LIVE VERIFIED</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                HexStrike-AI (v6.0.0) bound to 127.0.0.1:8888. Full pipeline verified against DVWA.
              </div>
            </div>
          </div>

          {/* LLM / OmniRoute */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">LLM / OmniRoute</span>
              <span className="badge" style={{ color: 'var(--state-success)', borderColor: 'var(--state-success)' }}>LIVE VERIFIED</span>
            </div>
            <div>
              <ConfigRow label="llm_base_url" value={settings.llm_base_url} />
              <ConfigRow label="llm_api_key" value={settings.llm_api_key_configured} masked />
            </div>
            <div style={{ marginTop: 16, padding: '10px 12px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 'var(--radius-xs)' }}>
              <div style={{ fontSize: 11, color: 'var(--state-success)', fontFamily: 'var(--font-mono)', marginBottom: 4 }}>PHASE 11 — LIVE VERIFIED</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                OmniRoute local proxy at localhost:20128/v1. OpenAI-compatible interface.
              </div>
            </div>
          </div>

          {/* Policy / Scope */}
          <div className="panel">
            <div className="panel-header"><span className="panel-title">Policy Enforcement</span></div>
            <div style={{ marginBottom: 16 }}>
              <ConfigRow label="execution_boundary" value={settings.execution_boundary} />
              <ConfigRow label="scope_constraint" value={settings.scope_constraint} />
            </div>
            <div style={{ fontSize: 11, fontFamily: 'var(--font-display)', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Allowed Targets</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {settings.allowed_targets.map(t => (
                <span key={t} style={{ fontSize: 11, padding: '3px 8px', border: '1px solid var(--border-hover)', borderRadius: 'var(--radius-xs)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{t}</span>
              ))}
            </div>
          </div>

          {/* Database stats */}
          <div className="panel">
            <div className="panel-header"><span className="panel-title">Runtime Statistics</span></div>
            <div>
              {[
                ['Total Assessments', settings.total_assessments],
                ['Total Findings', settings.total_findings],
                ['Total Evidence Records', settings.total_evidence],
              ].map(([k, v]) => (
                <div key={String(k)} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border-primary)' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{k}</span>
                  <span style={{ fontSize: 14, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}

      {/* Security note */}
      <div style={{ padding: '16px 20px', background: 'rgba(37,99,235,0.04)', border: '1px solid rgba(37,99,235,0.15)', borderRadius: 'var(--radius-sm)' }}>
        <div style={{ fontSize: 11, fontFamily: 'var(--font-display)', color: 'var(--accent-primary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
          Security Notice
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
          This page displays read-only configuration metadata. API keys and credentials are never rendered.
          Configuration modifications must be made via the backend <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>.env</code> file.
          No dangerous configuration changes are possible through this interface.
        </p>
      </div>
    </div>
  );
}
