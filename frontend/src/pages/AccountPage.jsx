import { useEffect } from 'react';
import Header from '../components/Header';
import GraphExplorer from '../components/GraphExplorer';
import { useGraphData } from '../hooks/useGraphData';

export default function AccountPage() {
  const { data, loading, error } = useGraphData();

  useEffect(() => {
    document.title = 'My Account · AWS IAM Privilege-Escalation Visualizer';
  }, []);

  return (
    <div className="app-container">
      <Header metadata={data?.metadata} mode="live" />
      <GraphExplorer data={data} loading={loading} error={error} />
    </div>
  );
}
