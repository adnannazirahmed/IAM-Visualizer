import { useState, useEffect } from 'react';
import smallOrgData from '../data/samples/small_org.json';
import overpermissionedData from '../data/samples/overpermissioned.json';
import fullEscalationData from '../data/samples/full_escalation.json';

const SAMPLES = {
  small_org: smallOrgData,
  overpermissioned: overpermissionedData,
  full_escalation: fullEscalationData,
};

export function useGraphData(dataSourceKey = 'small_org') {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    if (dataSourceKey === 'live') {
      fetch('http://localhost:8000/api/graph?source=live')
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Live API server returned status ${res.status}`);
          }
          return res.json();
        })
        .then((json) => {
          if (isMounted) {
            setData(json);
            setLoading(false);
          }
        })
        .catch((err) => {
          console.warn('Live API unavailable, falling back to sample:', err);
          if (isMounted) {
            setData(fullEscalationData);
            setError('Live backend unreachable. Displaying fallback escalation sample.');
            setLoading(false);
          }
        });
    } else {
      const sample = SAMPLES[dataSourceKey] || smallOrgData;
      const timer = setTimeout(() => {
        if (isMounted) {
          setData(sample);
          setLoading(false);
        }
      }, 150);

      return () => {
        isMounted = false;
        clearTimeout(timer);
      };
    }

    return () => {
      isMounted = false;
    };
  }, [dataSourceKey]);

  return { data, loading, error };
}
