import React from 'react';

export default function DataSourceToggle({ currentSource, onSourceChange }) {
  const options = [
    { id: 'small_org', label: 'Clean Org', badge: '5 Nodes' },
    { id: 'overpermissioned', label: 'Over-Permissioned', badge: 'Wildcards' },
    { id: 'full_escalation', label: 'Escalation Chain', badge: 'Critical' },
    { id: 'live', label: 'Live AWS API', badge: 'Real-time' },
  ];

  return (
    <div className="data-source-container">
      <span className="source-label">Data Source:</span>
      <div className="source-options">
        {options.map((opt) => {
          const isActive = currentSource === opt.id;
          return (
            <button
              key={opt.id}
              className={`source-pill ${isActive ? 'active' : ''} ${opt.id === 'live' ? 'live-pill' : ''}`}
              onClick={() => onSourceChange(opt.id)}
              title={`Switch to ${opt.label}`}
            >
              <span className="pill-dot" />
              <span className="pill-title">{opt.label}</span>
              <span className="pill-badge">{opt.badge}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
