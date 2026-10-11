/**
 * Feedback Records API Endpoints
 */
import { request } from '../client';

export const feedbackApi = {
  /**
   * List customer feedback records with search and filters
   */
  list(params = {}) {
    const query = new URLSearchParams();
    if (params.dataset_id) query.append('dataset_id', params.dataset_id);
    if (params.search) query.append('search', params.search);
    if (params.sentiment && params.sentiment !== 'ALL') query.append('sentiment', params.sentiment.toLowerCase());
    if (params.category && params.category !== 'ALL') query.append('category', params.category);
    if (params.canonical_only !== undefined) query.append('canonical_only', params.canonical_only);
    if (params.page) query.append('page', params.page);
    if (params.pageSize) query.append('page_size', params.pageSize);

    const queryString = query.toString();
    return request(`/feedback${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Submit single feedback record
   */
  create(payload) {
    return request('/feedback', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
