import React, { useState } from 'react';
import PolicyViewer from './PolicyViewer';
import EscalationPath from './EscalationPath';

export default function NodeDetail({ node, graphData, onClose, onSelectNode }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (!node) return null;

  const {
    id,
    type = 'user',
    name = id,
    arn = '',
    risk_level = 'none',
    risk_score = 0,
    policies = [],
    effective_permissions = [],
    escalation_paths = []
  } = node;

  const getRiskBadgeClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'risk-critical';
      case 'high': return 'risk-high';
      case 'medium': return 'risk-medium';
      case 'low': return 'risk-low';
      default: return 'risk-none';
    }
  };

  const getTypeIcon = (t) => {
    switch (t?.toLowerCase()) {
      case 'user': return '👤';
      case 'role': return '🔐';
      case 'group': return '👥';
      case 'policy': return '📜';
      case 'resource': return '📦';
      default: return '🔷';
    }
  };

  // Find full escalation path details from graphData if available
  const allEscalationPaths = graphData?.escalation_paths || [];
  const nodeEscalations = allEscalationPaths.filter(ep =>
    escalation_paths.includes(ep.id) || (ep.path && ep.path.includes(id))
  );

  return (
    <div className="node-detail-content">
      {/* Header */}
      <div className="detail-header">
        <div className="title-area">
          <span className="node-type-icon">{getTypeIcon(type)}</span>
          <div>
            <h2 className="node-name">{name}</h2>
            <span className="node-type-tag">{type.toUpperCase()}</span>
          </div>
        </div>
        <button className="close-btn" onClick={onClose} title="Close Panel">✕</button>
      </div>

      {/* Risk Summary Banner */}
      <div className="risk-summary-card">
        <div className="risk-score-badge-group">
          <span className={`risk-badge ${getRiskBadgeClass(risk_level)}`}>
            {risk_level.toUpperCase()} RISK
          </span>
          {risk_score > 0 && (
            <span className="risk-score-value">
              Score: {(risk_score * 10).toFixed(1)} / 10
            </span>
          )}
        </div>
        {arn && (
          <div className="arn-container">
            <span className="arn-label">ARN:</span>
            <code className="arn-text" title={arn}>{arn}</code>
          </div>
        )}
      </div>

      {/* Detail Tabs */}
      <div className="detail-tabs">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Permissions ({effective_permissions.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'policies' ? 'active' : ''}`}
          onClick={() => setActiveTab('policies')}
        >
          Policies ({policies.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'escalations' ? 'active' : ''}`}
          onClick={() => setActiveTab('escalations')}
        >
          Escalations ({nodeEscalations.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-body">
        {activeTab === 'overview' && (
          <div className="tab-pane">
            <div className="section-title">Effective Permissions</div>
            {effective_permissions.length === 0 ? (
              <div className="empty-state">No explicit permissions attached to this identity.</div>
            ) : (
              <div className="permission-grid">
                {effective_permissions.map((perm, idx) => {
                  const isWildcard = perm.includes('*');
                  const isCritical = perm.includes('CreatePolicyVersion') || perm.includes('PassRole') || perm.includes('Attach');
                  return (
                    <div
                      key={idx}
                      className={`permission-badge ${isCritical ? 'perm-critical' : isWildcard ? 'perm-wildcard' : ''}`}
                    >
                      {perm}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'policies' && (
          <div className="tab-pane">
            <div className="section-title">Attached Policies & Documents</div>
            {policies.length === 0 ? (
              <div className="empty-state">No policies defined or attached directly.</div>
            ) : (
              <div className="policies-list">
                {policies.map((policy, idx) => (
                  <PolicyViewer key={idx} policy={policy} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'escalations' && (
          <div className="tab-pane">
            <div className="section-title">Privilege Escalation Vectors</div>
            {nodeEscalations.length === 0 ? (
              <div className="empty-state">
                <span style={{ fontSize: '1.5rem', display: 'block', marginBottom: '8px' }}>🛡️</span>
                No known privilege escalation paths detected for this node.
              </div>
            ) : (
              <div className="escalations-list">
                {nodeEscalations.map((esc, idx) => (
                  <EscalationPath
                    key={idx}
                    pathData={esc}
                    onNodeSelect={(nodeId) => {
                      if (onSelectNode && graphData?.nodes) {
                        const targetNode = graphData.nodes.find(n => n.id === nodeId);
                        if (targetNode) onSelectNode(targetNode);
                      }
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
