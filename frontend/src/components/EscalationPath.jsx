import React from 'react';

export default function EscalationPath({ pathData, onNodeSelect }) {
  if (!pathData) return null;

  const { id, technique, risk = 'critical', path = [], required_permissions = [], description } = pathData;

  const getRiskClass = (r) => {
    switch (r?.toLowerCase()) {
      case 'critical': return 'risk-critical';
      case 'high': return 'risk-high';
      case 'medium': return 'risk-medium';
      case 'low': return 'risk-low';
      default: return 'risk-none';
    }
  };

  return (
    <div className="escalation-card">
      <div className="escalation-header">
        <div className="escalation-title-row">
          <span className="escalation-badge-icon">⚠️</span>
          <span className="escalation-technique">{technique || id}</span>
          <span className={`risk-badge ${getRiskClass(risk)}`}>{risk}</span>
        </div>
        {description && <p className="escalation-description">{description}</p>}
      </div>

      <div className="escalation-flow">
        <div className="flow-title">Privilege Escalation Chain</div>
        <div className="flow-steps">
          {path.map((nodeId, idx) => {
            const isLast = idx === path.length - 1;
            const nodeParts = nodeId.split('::');
            const type = nodeParts[0] || 'node';
            const name = nodeParts[1] || nodeId;

            return (
              <React.Fragment key={idx}>
                <div
                  className={`flow-step ${isLast ? 'target-step' : ''}`}
                  onClick={() => onNodeSelect && onNodeSelect(nodeId)}
                  title={`Click to view ${nodeId}`}
                >
                  <span className="step-num">{idx + 1}</span>
                  <div className="step-info">
                    <span className="step-name">{name}</span>
                    <span className="step-type">{type}</span>
                  </div>
                </div>

                {!isLast && (
                  <div className="flow-connector">
                    <div className="connector-line" />
                    <div className="connector-arrow">➔</div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {required_permissions.length > 0 && (
        <div className="required-permissions-section">
          <span className="perm-label">Required Exploitation Permissions:</span>
          <div className="perm-chips">
            {required_permissions.map((perm, pIdx) => (
              <code key={pIdx} className="perm-chip">{perm}</code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
