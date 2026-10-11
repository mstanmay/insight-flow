import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import { useWorkspace } from '../context/WorkspaceContext';

/**
 * Custom hook to fetch dataset analytics aggregates and metrics
 */
export function useAnalytics() {
  const { activeDataset } = useWorkspace();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    if (!activeDataset?.id) return;

    try {
      setLoading(true);
      setError(null);
      const data = await api.getAnalytics(activeDataset.id);
      setAnalytics(data);
    } catch (err) {
      console.warn('Failed to fetch dataset analytics:', err);
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [activeDataset?.id]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return {
    analytics,
    loading,
    error,
    refresh: fetchAnalytics,
  };
}
