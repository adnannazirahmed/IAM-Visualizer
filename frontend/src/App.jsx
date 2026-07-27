import { useState } from 'react';
import Header from './components/Header';
import GraphView from './components/GraphView';
import NodeDetail from './components/NodeDetail';
import RiskDashboard from './components/RiskDashboard';
import { useGraphData } from './hooks/useGraphData';

function App() {
  const [dataSource, setDataSource] = useState('full_escalation');
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const { data, loading, error } = useGraphData(dataSource);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const handleSourceChange = (source) => {
    setDataSource(source);
    setSelectedNode(null);
  };

  const handleSelectNodeFromList = (node) => {
    setSelectedNode(node);
  };

  // Filtered nodes for search dropdown
  const filteredNodes = data?.nodes
    ? data.nodes.filter(
        (n) =>
          n.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          n.arn?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          n.type?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  return (
    <div className="app-container">
      <Header
        currentSource={dataSource}
        onSourceChange={handleSourceChange}
        metadata={data?.metadata}
      />

      <div className="main-content">
        {/* Search Bar Overlay */}
        <div className="search-bar-overlay glass-panel">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search nodes by name, ARN, or type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="clear-search" onClick={() => setSearchQuery('')}>✕</button>
          )}
          {searchQuery && filteredNodes.length > 0 && (
            <div className="search-results-dropdown glass-panel">
              {filteredNodes.map((node) => (
                <div
                  key={node.id}
                  className="search-result-item"
                  onClick={() => {
                    setSelectedNode(node);
                    setSearchQuery('');
                  }}
                >
                  <span className="res-name">{node.name}</span>
                  <span className="res-type">{node.type}</span>
                  <span className={`risk-badge risk-${node.risk_level}`}>{node.risk_level}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Loading Overlay */}
        {loading && (
          <div className="loading-overlay">
            <div className="spinner" />
            <span>Analyzing AWS IAM Graph...</span>
          </div>
        )}

        {/* Error Toast */}
        {error && !loading && (
          <div className="error-toast glass-panel">
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* Top-Left Risk Dashboard */}
        {!loading && data && (
          <RiskDashboard
            data={data}
            onSelectNode={handleSelectNodeFromList}
            selectedNodeId={selectedNode?.id}
          />
        )}

        {/* Main Graph Visualization Area */}
        {!loading && data && (
          <div className="graph-container">
            <GraphView
              data={data}
              onNodeClick={handleNodeClick}
              selectedNode={selectedNode}
            />
          </div>
        )}

        {/* Right Sidebar Detail Panel */}
        <div className={`sidebar glass-panel ${!selectedNode ? 'hidden' : ''}`}>
          {selectedNode && (
            <NodeDetail
              node={selectedNode}
              graphData={data}
              onClose={() => setSelectedNode(null)}
              onSelectNode={handleSelectNodeFromList}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
