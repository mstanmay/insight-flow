/**
 * InsightFlow HTTP Client
 * Provides robust error handling, JSON parsing, and request abstraction.
 */
import { config } from '../config';

export class ApiError extends Error {
  constructor(message, status, code = 'api_error', data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.data = data;
  }
}

/**
 * Standard fetch wrapper with error interception
 */
export async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${config.apiBaseUrl}${endpoint}`;
  
  const headers = {
    ...options.headers,
  };

  // Only set application/json if body is not FormData
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    // Handle HTTP error statuses
    if (!res.ok) {
      let errMessage = `Request failed with status ${res.status}`;
      let errCode = 'http_error';
      let errData = null;

      try {
        const json = await res.json();
        errMessage = json.message || json.detail || errMessage;
        errCode = json.code || errCode;
        errData = json;
      } catch (_) {
        // Fallback for non-JSON error bodies
        const text = await res.text();
        if (text) errMessage = text;
      }

      throw new ApiError(errMessage, res.status, errCode, errData);
    }

    // Return JSON or empty if 204 No Content
    if (res.status === 204) return null;
    return await res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Network connection failed', 0, 'network_error');
  }
}
