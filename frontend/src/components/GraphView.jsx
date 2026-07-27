import React, { useRef, useState, useEffect, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

const RISK_COLORS = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#eab308',
  low: '#3b82f6',
  none: '#6b7280',
};

export default function GraphView({ data, onNodeClick, selectedNode }) {
  const fgRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState(null);

  // Resize handling
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateDimensions();
    const observer = new ResizeObserver(updateDimensions);
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Format graph data for ForceGraph2D
  const formattedData = useMemo(() => {
    if (!data || !data.nodes) return { nodes: [], links: [] };

    // Deep clone nodes and links so d3 doesn't mutate props directly in weird ways
    const nodes = data.nodes.map((n) => ({ ...n }));
    const links = (data.links || []).map((l) => ({
      ...l,
      source: typeof l.source === 'object' ? l.source.id : l.source,
      target: typeof l.target === 'object' ? l.target.id : l.target,
    }));

    return { nodes, links };
  }, [data]);

  // Recenter when node selected
  useEffect(() => {
    if (selectedNode && fgRef.current) {
      const nodeObj = formattedData.nodes.find((n) => n.id === selectedNode.id);
      if (nodeObj && nodeObj.x !== undefined && nodeObj.y !== undefined) {
        fgRef.current.centerAt(nodeObj.x, nodeObj.y, 800);
        fgRef.current.zoom(2.5, 800);
      }
    }
  }, [selectedNode, formattedData]);

  // Draw shapes per node type
  const drawNodeShape = useCallback((node, ctx, size, color, isSelected, isHovered) => {
    const { type = 'user' } = node;

    ctx.fillStyle = color;
    ctx.strokeStyle = isSelected ? '#ffffff' : isHovered ? '#f87171' : 'rgba(255,255,255,0.4)';
    ctx.lineWidth = isSelected ? 3 : isHovered ? 2 : 1;

    // Glowing aura for critical nodes or selected node
    if (isSelected || node.risk_level === 'critical') {
      ctx.shadowColor = color;
      ctx.shadowBlur = isSelected ? 15 : 10;
    } else {
      ctx.shadowBlur = 0;
    }

    ctx.beginPath();
    switch (type.toLowerCase()) {
      case 'user':
        // Circle
        ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
        break;

      case 'role':
        // Diamond
        ctx.moveTo(node.x, node.y - size * 1.3);
        ctx.lineTo(node.x + size * 1.3, node.y);
        ctx.lineTo(node.x, node.y + size * 1.3);
        ctx.lineTo(node.x - size * 1.3, node.y);
        ctx.closePath();
        break;

      case 'group':
        // Square
        ctx.rect(node.x - size, node.y - size, size * 2, size * 2);
        break;

      case 'policy':
        // Hexagon
        for (let i = 0; i < 6; i++) {
          const angle = (Math.PI / 3) * i;
          const px = node.x + size * 1.1 * Math.cos(angle);
          const py = node.y + size * 1.1 * Math.sin(angle);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        break;

      case 'resource':
      default:
        // Octagon
        for (let i = 0; i < 8; i++) {
          const angle = (Math.PI / 4) * i;
          const px = node.x + size * Math.cos(angle);
          const py = node.y + size * Math.sin(angle);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        break;
    }

    ctx.fill();
    ctx.stroke();

    // Reset shadow
    ctx.shadowBlur = 0;
  }, []);

  // Custom node rendering
  const handleNodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      const isSelected = selectedNode && selectedNode.id === node.id;
      const isHovered = hoveredNode && hoveredNode.id === node.id;

      const riskColor = RISK_COLORS[node.risk_level] || RISK_COLORS.none;
      const size = 8 + (node.risk_score || 0) * 0.4;

      drawNodeShape(node, ctx, size, riskColor, isSelected, isHovered);

      // Render Label under node
      const label = node.name || node.id;
      const fontSize = Math.max(10 / globalScale, 3);
      ctx.font = `600 ${fontSize}px Inter, sans-serif`;

      // Text background glow / pill for readability
      const textWidth = ctx.measureText(label).width;
      const bckgDimensions = [textWidth + 6, fontSize + 4];

      ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
      ctx.beginPath();
      ctx.roundRect(
        node.x - bckgDimensions[0] / 2,
        node.y + size + 4,
        bckgDimensions[0],
        bckgDimensions[1],
        3
      );
      ctx.fill();

      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isSelected ? '#60a5fa' : '#f8fafc';
      ctx.fillText(label, node.x, node.y + size + 4 + fontSize / 2);
    },
    [selectedNode, hoveredNode, drawNodeShape]
  );

  // Pointer Area Paint for accurate hit testing
  const handleNodePointerAreaPaint = useCallback((node, color, ctx) => {
    const size = 12;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fill();
  }, []);

  // Controls handlers
  const handleZoomIn = () => fgRef.current && fgRef.current.zoom(fgRef.current.zoom() * 1.3, 400);
  const handleZoomOut = () => fgRef.current && fgRef.current.zoom(fgRef.current.zoom() * 0.7, 400);
  const handleFit = () => fgRef.current && fgRef.current.zoomToFit(400, 50);

  return (
    <div className="graph-wrapper" ref={containerRef}>
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={formattedData}
        nodeCanvasObject={handleNodeCanvasObject}
        nodePointerAreaPaint={handleNodePointerAreaPaint}
        nodeLabel={(node) => `
          <div style="background: rgba(15, 23, 42, 0.9); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); font-family: Inter, sans-serif;">
            <strong style="color: #f9fafb; display: block;">${node.name || node.id}</strong>
            <span style="color: #9ca3af; font-size: 0.8rem; text-transform: uppercase;">${node.type}</span>
            <div style="margin-top: 4px; font-size: 0.8rem;">Risk Level: <strong style="color: ${RISK_COLORS[node.risk_level]};">${node.risk_level}</strong></div>
          </div>
        `}
        linkColor={(link) => (link.is_escalation ? '#ef4444' : 'rgba(156, 163, 175, 0.3)')}
        linkWidth={(link) => (link.is_escalation ? 2.5 : 1)}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={0.95}
        linkDirectionalArrowColor={(link) => (link.is_escalation ? '#ef4444' : '#9ca3af')}
        linkDirectionalParticles={(link) => (link.is_escalation ? 4 : 0)}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleSpeed={0.006}
        linkDirectionalParticleColor={() => '#ef4444'}
        linkLabel={(link) => link.label || link.relationship || ''}
        onNodeClick={(node) => onNodeClick && onNodeClick(node)}
        onNodeHover={(node) => setHoveredNode(node)}
        cooldownTicks={100}
        d3VelocityDecay={0.3}
      />

      {/* Canvas Overlay Controls */}
      <div className="graph-controls glass-panel">
        <button onClick={handleZoomIn} title="Zoom In">+</button>
        <button onClick={handleZoomOut} title="Zoom Out">−</button>
        <button onClick={handleFit} title="Fit Graph">⛶</button>
      </div>

      {/* Legend Overlay */}
      <div className="graph-legend glass-panel">
        <div className="legend-title">Node Types</div>
        <div className="legend-items">
          <div className="legend-item"><span className="legend-shape shape-circle" /> User</div>
          <div className="legend-item"><span className="legend-shape shape-diamond" /> Role</div>
          <div className="legend-item"><span className="legend-shape shape-square" /> Group</div>
          <div className="legend-item"><span className="legend-shape shape-hexagon" /> Policy</div>
          <div className="legend-item"><span className="legend-shape shape-octagon" /> Resource</div>
        </div>
        <div className="legend-title" style={{ marginTop: '8px' }}>Links</div>
        <div className="legend-items">
          <div className="legend-item"><span className="legend-line line-escalation" /> Escalation Vector</div>
          <div className="legend-item"><span className="legend-line line-normal" /> Standard Permission</div>
        </div>
      </div>
    </div>
  );
}
