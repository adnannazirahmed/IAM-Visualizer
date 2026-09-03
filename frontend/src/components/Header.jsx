import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Header({ metadata, mode = 'live' }) {
  const isDemo = mode === 'demo';

  return (
    <header className="header glass-panel">
      <div className="header-brand">
        <div className="brand-icon-wrapper">
          <svg className="shield-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="M12 8v4" strokeLinecap="round" />
            <path d="M12 16h.01" strokeLinecap="round" />
          </svg>
        </div>
        <div className="brand-text">
          <h1 className="header-title">AWS IAM Privilege Escalation Visualizer</h1>
          <div className="header-subtitle">
            <span className={isDemo ? 'demo-indicator-dot' : 'live-indicator-dot'} />
            {isDemo ? 'Demo Environment · Fictional Data' : 'Graph Security Analyzer'}
            {metadata?.account_id && (
              <span className={`account-tag ${isDemo ? 'account-tag-demo' : ''}`}>
                Account: <code>{metadata.account_id}</code>
              </span>
            )}
          </div>
        </div>
      </div>

      <nav className="header-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}>
          My Account
        </NavLink>
        <NavLink to="/demo" className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}>
          Demo
        </NavLink>
      </nav>
    </header>
  );
}
