import React, { useState } from 'react';

export default function PolicyViewer({ policy }) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(true);

  if (!policy) return null;

  const policyName = policy.PolicyName || 'Unnamed Policy';
  const doc = policy.PolicyDocument || policy;
  const jsonString = JSON.stringify(doc, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="policy-card">
      <div className="policy-header" onClick={() => setExpanded(!expanded)}>
        <div className="policy-title">
          <span className="policy-icon">📜</span>
          <span className="policy-name">{policyName}</span>
        </div>
        <div className="policy-actions">
          <button
            className="policy-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleCopy();
            }}
            title="Copy Policy JSON"
          >
            {copied ? '✓ Copied' : '📋 Copy'}
          </button>
          <span className="expand-icon">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div className="policy-body">
          <pre className="json-code">
            {jsonString.split('\n').map((line, idx) => {
              // Highlight key policy terms
              let formattedLine = line;
              const isAllow = line.includes('"Effect": "Allow"');
              const isDeny = line.includes('"Effect": "Deny"');
              const isAction = line.includes('"Action"');

              return (
                <div
                  key={idx}
                  className={`json-line ${isAllow ? 'effect-allow' : ''} ${isDeny ? 'effect-deny' : ''} ${isAction ? 'action-line' : ''}`}
                >
                  {formattedLine}
                </div>
              );
            })}
          </pre>
        </div>
      )}
    </div>
  );
}
