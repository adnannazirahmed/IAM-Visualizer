import { useEffect } from 'react';
import Header from '../components/Header';
import GraphExplorer from '../components/GraphExplorer';
import demoGraph from '../data/demoGraph.json';

export default function DemoPage() {
  useEffect(() => {
    document.title = 'Demo Environment · AWS IAM Privilege-Escalation Visualizer';
  }, []);

  return (
    <div className="app-container">
      <Header metadata={demoGraph.metadata} mode="demo" />
      <GraphExplorer data={demoGraph} loading={false} error={null} />
    </div>
  );
}
