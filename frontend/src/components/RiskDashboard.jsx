import React, { useState } from 'react';

export default function RiskDashboard({ data, onSelectNode, selectedNodeId }) {
  const [collapsed, setCollapsed] = useState(false);

  if (!data) return null;

  const nodes = data.nodes || [];
  const escalationPaths = data.escalation_paths || [];

  const counts = {
    critical: nodes.filter((n) => n.risk_level === 'critical').length,
    high: nodes.filter((n) => n.risk_level === 'high').length,
    medium: nodes.filter((n) => n.risk_level === 'medium').length,
    low: nodes.filter((n) => n.risk_level === 'low').length,
    total: nodes.length,
    escalations: escalationPaths.length,
  };

  // Top 5 riskiest identities sorted by risk_score desc
  const topRiskiest = [...nodes]
    .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
    .filter((n) => (n.risk_score || 0) > 0 || n.risk_level !== 'none')
    .slice(0, 5);

  const getRiskBadgeClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'risk-critical';
      case 'high': return 'risk-high';
      case 'medium': return 'risk-medium';
      case 'low': return 'risk-low';
      default: return 'risk-none';
    }
  };

  return (
    <div className={`dashboard-overlay glass-panel ${collapsed ? 'collapsed' : ''}`}>
      <div className="dashboard-header" onClick={() => setCollapsed(!collapsed)}>
        <div className="dashboard-title">
          <span className="dash-icon">📊</span>
          <span>Security Risk Overview</span>
          {counts.critical > 0 && (
            <span className="critical-pulse-pill">{counts.critical} Critical Alert{counts.critical > 1 ? 's' : ''}</span>
          )}
        </div>
        <button className="collapse-btn">{collapsed ? '▲ Show' : '▼ Hide'}</button>
      </div>

      {!collapsed && (
        <div className="dashboard-body">
          {/* Summary Metric Cards */}
          <div className="risk-metrics-grid">
            <div className="metric-card metric-critical">
              <span className="metric-value">{counts.critical}</span>
              <span className="metric-label">Critical</span>
            </div>
            <div className="metric-card metric-high">
              <span className="metric-value">{counts.high}</span>
              <span className="metric-label">High</span>
            </div>
            <div className="metric-card metric-medium">
              <span className="metric-value">{counts.medium}</span>
              <span className="metric-label">Medium</span>
            </div>
            <div className="metric-card metric-low">
              <span className="metric-value">{counts.low}</span>
              <span className="metric-label">Low</span>
            </div>
            <div className="metric-card metric-total">
              <span className="metric-value">{counts.total}</span>
              <span className="metric-label">Total Nodes</span>
            </div>
            <div className="metric-card metric-escalations">
              <span className="metric-value">{counts.escalations}</span>
              <span className="metric-label">Escalations</span>
            </div>
          </div>

          {/* Top 5 Riskiest Identities */}
          <div className="riskiest-section">
            <div className="section-subtitle">Top Riskiest Identities</div>
            {topRiskiest.length === 0 ? (
              <div className="no-risk-msg">No high-risk identities detected in this environment.</div>
            ) : (
              <div className="riskiest-list">
                {topRiskiest.map((node) => {
                  const isSelected = selectedNodeId === node.id;
                  return (
                    <div
                      key={node.id}
                      className={`riskiest-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => onSelectNode && onSelectNode(node)}
                    >
                      <div className="risk-item-info">
                        <span className="risk-item-name">{node.name}</span>
                        <span className="risk-item-type">{node.type}</span>
                      </div>
                      <div className="risk-item-score">
                        <span className={`risk-badge ${getRiskBadgeClass(node.risk_level)}`}>
                          {node.risk_score?.toFixed(1) || node.risk_level}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
