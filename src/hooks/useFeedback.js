import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';
import { useWorkspace } from '../context/WorkspaceContext';

/**
 * Custom hook to fetch and filter customer feedback records with debounce
 */
export function useFeedback(initialFilters = {}) {
  const { activeDataset } = useWorkspace();
  const [feedback, setFeedback] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(initialFilters);

  const debounceTimer = useRef(null);

  const fetchFeedback = useCallback(async (currentFilters = filters, currentPage = page) => {
    if (!activeDataset?.id) return;

    try {
      setLoading(true);
      setError(null);
      const res = await api.getFeedback({
        dataset_id: activeDataset.id,
        search: currentFilters.search || undefined,
        sentiment: currentFilters.sentiment !== 'ALL' ? currentFilters.sentiment : undefined,
        category: currentFilters.category !== 'ALL' ? currentFilters.category : undefined,
        page: currentPage,
        pageSize,
      });

      setFeedback(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.warn('Failed to fetch feedback records:', err);
      setError(err.message || 'Failed to load feedback');
    } finally {
      setLoading(false);
    }
  }, [activeDataset?.id, pageSize, filters, page]);

  const updateFilters = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setPage(1);

    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      fetchFeedback({ ...filters, ...newFilters }, 1);
    }, 250);
  }, [filters, fetchFeedback]);

  useEffect(() => {
    fetchFeedback();
    return () => clearTimeout(debounceTimer.current);
  }, [activeDataset?.id, page]);

  return {
    feedback,
    total,
    page,
    setPage,
    pageSize,
    setPageSize,
    loading,
    error,
    filters,
    updateFilters,
    refresh: () => fetchFeedback(filters, page),
  };
}
