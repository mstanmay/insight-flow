/**
 * Central API Gateway
 * Exports typed endpoint modules and convenience methods.
 */
import { datasetsApi } from './endpoints/datasets';
import { issuesApi } from './endpoints/issues';
import { feedbackApi } from './endpoints/feedback';
import { analyticsApi } from './endpoints/analytics';
import { ApiError } from './client';

export { ApiError, datasetsApi, issuesApi, feedbackApi, analyticsApi };

// Unified API object
export const api = {
  // Datasets
  getDatasets: (page, pageSize) => datasetsApi.list(page, pageSize),
  getDatasetById: (id) => datasetsApi.getById(id),
  uploadDataset: (file, name) => datasetsApi.upload(file, name),
  deleteDataset: (id) => datasetsApi.delete(id),

  // Issues
  getIssues: (params) => issuesApi.list(params),
  getIssueDetail: (id) => issuesApi.getById(id),
  updateIssueStatus: (id, status, note, owner) => issuesApi.updateStatus(id, status, note, owner),

  // Feedback
  getFeedback: (params) => feedbackApi.list(params),
  createFeedback: (payload) => feedbackApi.create(payload),

  // Analytics & Jobs
  getAnalytics: (datasetId) => analyticsApi.getDatasetAnalytics(datasetId),
  getJobStatus: (jobId) => analyticsApi.getJobStatus(jobId),
  getIntegrationsStatus: () => analyticsApi.getIntegrationsStatus(),
  getExportUrl: (datasetId) => analyticsApi.getReportExportUrl(datasetId),
};

export default api;
