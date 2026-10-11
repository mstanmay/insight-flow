/**
 * Issues & Friction Clusters API Endpoints
 */
import { request } from '../client';

export const issuesApi = {
  /**
   * List friction issues with filtering and sorting
   */
  list(params = {}) {
    const query = new URLSearchParams();
    if (params.dataset_id) query.append('dataset_id', params.dataset_id);
    if (params.category && params.category !== 'ALL') query.append('category', params.category);
    if (params.status) query.append('status', params.status);
    if (params.kind) query.append('kind', params.kind);
    if (params.page) query.append('page', params.page);
    if (params.pageSize) query.append('page_size', params.pageSize);

    const queryString = query.toString();
    return request(`/issues${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get single issue detail with verbatim citations & recommendations
   */
  getById(issueId) {
    return request(`/issues/${issueId}`);
  },

  /**
   * Update issue status or workflow state
   */
  updateStatus(issueId, status, note = null, owner = null) {
    return request(`/issues/${issueId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, note, owner }),
    });
  },
};
