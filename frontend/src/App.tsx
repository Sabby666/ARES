import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Search, Bug, Bot, FileText,
  Network, Settings, Bell, Command, ShieldAlert, Database
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Assessments from './pages/Assessments';
import NewAssessment from './pages/NewAssessment';
import AssessmentDetail from './pages/AssessmentDetail';
import Findings from './pages/Findings';
import EvidencePage from './pages/Evidence';
import ThreatIntel from './pages/ThreatIntel';
import Agents from './pages/Agents';
import Reports from './pages/Reports';
import Architecture from './pages/Architecture';
import SettingsPage from './pages/Settings';

import { useState, useEffect } from 'react';
import { api } from './services/api';

const NAV_GROUPS = [
  {
    title: 'COMMAND',
    items: [
      { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/assessments', icon: Search, label: 'Assessments' },
    ]
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { to: '/findings', icon: Bug, label: 'Findings' },
      { to: '/evidence', icon: Database, label: 'Evidence' },
      { to: '/threats', icon: ShieldAlert, label: 'Threat Intel' },
    ]
  },
  {
    title: 'OPERATIONS',
    items: [
      { to: '/agents', icon: Bot, label: 'Agents' },
      { to: '/reports', icon: FileText, label: 'Reports' },
      { to: '/architecture', icon: Network, label: 'Architecture' },
    ]
  },
  {
    title: 'SYSTEM',
    items: [
      { to: '/settings', icon: Settings, label: 'Settings' },
    ]
  }
];

function CommandRail() {
  return (
    <nav className="command-rail">
      <div className="rail-logo">
        <div className="rail-logo-icon">A</div>
        <div className="rail-logo-text">
          <strong>ARES</strong>
          <span>AI-Driven Security</span>
        </div>
      </div>
      <div className="rail-nav">
        {NAV_GROUPS.map(group => (
          <div key={group.title} className="rail-group">
            <div className="rail-group-title">{group.title}</div>
            {group.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `rail-link ${isActive ? 'active' : ''}`}
                title={item.label}
              >
                <item.icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </div>
    </nav>
  );
}

function TopBar() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const check = async () => {
      const online = await api.checkHealth();
      setIsOnline(online);
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="topbar">
      <div className="topbar-search">
        <Search size={14} style={{ color: 'var(--text-muted)' }} />
        <input type="search" placeholder="Search anything..." />
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)', fontSize: 10, fontFamily: 'var(--font-display)', background: 'rgba(255,255,255,0.05)', padding: '2px 4px', borderRadius: 4 }}>
          <Command size={10} /> K
        </div>
      </div>
      <div className="topbar-actions">
        <div className="topbar-pill" style={{ color: isOnline ? 'var(--state-success)' : 'var(--state-error)', borderColor: isOnline ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)' }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: isOnline ? 'var(--state-success)' : 'var(--state-error)' }} />
          {isOnline === null ? 'CHECKING...' : (isOnline ? 'SYSTEM ONLINE' : 'LINK FAILED')}
        </div>
        <div className="topbar-pill" style={{ color: 'var(--accent-primary)', borderColor: 'rgba(37,99,235,0.2)' }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', border: '1px solid var(--accent-primary)' }} />
          LOCAL MODE
        </div>
        <Bell size={18} style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} />
        <div className="topbar-avatar">A</div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="app-layout">
      <CommandRail />
      <main className="main-content">
        <TopBar />
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/assessments" element={<Assessments />} />
            <Route path="/assessments/new" element={<NewAssessment />} />
            <Route path="/assessments/:id" element={<AssessmentDetail />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/threats" element={<ThreatIntel />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/architecture" element={<Architecture />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
