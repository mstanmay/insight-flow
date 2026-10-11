import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import { useWorkspace } from '../context/WorkspaceContext';

/**
 * Custom hook to fetch and manage friction cluster issues
 */
export function useIssues(filters = {}) {
  const { activeDataset } = useWorkspace();
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchIssues = useCallback(async () => {
    if (!activeDataset?.id) return;

    try {
      setLoading(true);
      setError(null);
      const res = await api.getIssues({
        dataset_id: activeDataset.id,
        ...filters,
      });
      setIssues(res.items || []);
    } catch (err) {
      console.warn('Failed to fetch issues:', err);
      setError(err.message || 'Failed to load issues');
    } finally {
      setLoading(false);
    }
  }, [activeDataset?.id, JSON.stringify(filters)]);

  useEffect(() => {
    fetchIssues();
  }, [fetchIssues]);

  return {
    issues,
    loading,
    error,
    refresh: fetchIssues,
  };
}
