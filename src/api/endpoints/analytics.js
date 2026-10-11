/**
 * Analytics, Jobs, and Reporting API Endpoints
 */
import { request } from '../client';
import { config } from '../../config';

export const analyticsApi = {
  /**
   * Get analytics aggregates for a dataset
   */
  getDatasetAnalytics(datasetId) {
    return request(`/datasets/${datasetId}/analytics`);
  },

  /**
   * Poll asynchronous analysis job status
   */
  getJobStatus(jobId) {
    return request(`/jobs/${jobId}`);
  },

  /**
   * Get system integrations and provider status
   */
  getIntegrationsStatus() {
    return request('/integrations/status');
  },

  /**
   * Get absolute or relative export report download URL
   */
  getReportExportUrl(datasetId) {
    return `${config.apiBaseUrl}/reports/${datasetId}/export.csv`;
  },
};
