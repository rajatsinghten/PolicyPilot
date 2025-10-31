// API Configuration for different environments
// This file centralizes API endpoints for easy deployment

// Determine the API base URL based on environment
const getApiBaseUrl = () => {
  // Production URLs - update these after deployment
  const PRODUCTION_URLS = {
    render: 'https://policypilot-backend.onrender.com',
    railway: 'https://policypilot-backend.railway.app',
    heroku: 'https://your-heroku-app.herokuapp.com',
    azure: 'https://policypilot-backend.azurecontainerapps.io'
  };

  // Check if we're in development
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000';
  }

  // For production, use the environment variable or default to Render
  return process.env.REACT_APP_API_URL || PRODUCTION_URLS.render;
};

export const API_BASE_URL = getApiBaseUrl();

// API endpoints
export const API_ENDPOINTS = {
  upload: '/upload',
  process: '/process',
  documents: '/documents',
  search: '/search',
  health: '/health'
};

// Full API URLs
export const API = {
  upload: `${API_BASE_URL}${API_ENDPOINTS.upload}`,
  process: `${API_BASE_URL}${API_ENDPOINTS.process}`,
  documents: `${API_BASE_URL}${API_ENDPOINTS.documents}`,
  search: (query) => `${API_BASE_URL}${API_ENDPOINTS.search}/${encodeURIComponent(query)}`,
  health: `${API_BASE_URL}${API_ENDPOINTS.health}`
};

console.log('API Configuration:', {
  environment: process.env.NODE_ENV,
  apiBaseUrl: API_BASE_URL
});
