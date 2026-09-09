import { useEffect, useState, useRef } from 'react';
import { api, DashboardData } from '../services/api';
import { Activity } from 'lucide-react';

export default function SystemFeed({ activities }: { activities?: any[] }) {
  const [feed, setFeed] = useState<any[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initialize with some dummy feed data if backend doesn't have websockets firing right away
  useEffect(() => {
    if (activities && activities.length > 0) {
      setFeed(activities);
    } else {
      setFeed([
        { id: 1, timestamp: new Date(Date.now() - 4000).toISOString(), agent_name: 'System', message: 'All modules online', status: 'completed' },
        { id: 2, timestamp: new Date(Date.now() - 3000).toISOString(), agent_name: 'System', message: 'Control plane ready', status: 'running' },
        { id: 3, timestamp: new Date(Date.now() - 2000).toISOString(), agent_name: 'System', message: 'Waiting for assessment', status: 'running' },
        { id: 4, timestamp: new Date(Date.now() - 1000).toISOString(), agent_name: 'System', message: 'ARES Engine initialized', status: 'running' },
      ]);
    }
  }, [activities]);

  // Connect to websocket to append real activities
  useEffect(() => {
    // In a real app we'd subscribe to the websocket here. 
    // Since this is a UI layer refactor, we rely on props or polling if needed.
    // Assuming props will update if we poll in Dashboard.
  }, []);

  return (
    <div className="panel" style={{ flex: 1 }}>
      <div className="panel-header" style={{ marginBottom: 12 }}>
        <span className="panel-title">SYSTEM FEED</span>
      </div>
      
      <div 
        ref={scrollRef}
        className="activity-stream" 
        style={{ height: 160, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 0 }}
      >
        {feed.map((log) => {
          const time = new Date(log.timestamp).toLocaleTimeString([], { hour12: false });
          let dotColor = 'var(--accent-primary)';
          if (log.status === 'completed') dotColor = 'var(--state-success)';
          if (log.status === 'failed') dotColor = 'var(--state-error)';
          if (log.status === 'blocked') dotColor = 'var(--state-warning)';

          return (
            <div key={log.id} className="activity-log-line" style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: 11, width: 64 }}>{time}</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 11, width: 80, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Activity size={10} style={{ color: 'var(--text-muted)' }} />
                {log.agent_name || 'System'}
              </div>
              <div style={{ color: 'var(--text-primary)', fontSize: 12, flex: 1 }}>{log.message}</div>
              <div style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: dotColor, marginLeft: 'auto' }} />
            </div>
          );
        })}
      </div>
      
      <div style={{ marginTop: 'auto', paddingTop: 16, borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>
        <Activity size={12} />
        LIVE FEED
      </div>
    </div>
  );
}
