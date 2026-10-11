/**
 * Datasets API Endpoints
 */
import { request } from '../client';

export const datasetsApi = {
  /**
   * List ingested datasets with pagination
   */
  list(page = 1, pageSize = 20) {
    return request(`/datasets?page=${page}&page_size=${pageSize}`);
  },

  /**
   * Get single dataset by ID
   */
  getById(datasetId) {
    return request(`/datasets/${datasetId}`);
  },

  /**
   * Upload CSV file for batch ingestion
   */
  upload(file, name) {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);

    return request('/datasets/imports', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Delete dataset
   */
  delete(datasetId) {
    return request(`/datasets/${datasetId}`, {
      method: 'DELETE',
    });
  },
};
