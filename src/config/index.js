/**
 * InsightFlow Application Configuration & Constants
 * Centralizes environment variables, API endpoints, and design tokens.
 */

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  appName: import.meta.env.VITE_APP_NAME || 'InsightFlow',
  appEnv: import.meta.env.VITE_APP_ENV || 'development',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
};

export const VIEWS = {
  OVERVIEW: 'overview',
  STUDIO: 'studio',
  RADAR: 'radar',
  EXPLORER: 'explorer',
  TERMINAL: 'terminal',
};

export const SENTIMENT_LABELS = {
  CRITICAL: 'CRITICAL',
  NEGATIVE: 'NEGATIVE',
  NEUTRAL: 'NEUTRAL',
  POSITIVE: 'POSITIVE',
};

export const CATEGORIES = [
  'Operational Issues',
  'Fraud and Scam',
  'Product Feedback',
  'Customer Service',
];
