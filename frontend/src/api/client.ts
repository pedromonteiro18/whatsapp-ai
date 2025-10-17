import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

/**
 * Centralized Axios instance with interceptors for authentication and error handling
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

/**
 * Request interceptor to attach Bearer token to all requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from localStorage
    const token = localStorage.getItem('auth_token');

    // Attach token to request if it exists
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for centralized error handling
 */
apiClient.interceptors.response.use(
  // Pass through successful responses
  (response) => response,

  // Handle errors
  (error: AxiosError) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Clear authentication tokens from localStorage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_phone');

      // Redirect to login page
      // Use window.location to force a full page reload and reset React state
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    // Format error message for better UX
    const errorMessage = getErrorMessage(error);

    // Attach formatted message to error object
    const enhancedError = {
      ...error,
      message: errorMessage,
    };

    return Promise.reject(enhancedError);
  }
);

/**
 * Extract user-friendly error message from axios error
 */
function getErrorMessage(error: AxiosError): string {
  // Network error (no response received)
  if (!error.response) {
    if (error.code === 'ECONNABORTED') {
      return 'Request timeout. Please check your connection and try again.';
    }
    return 'Network error. Please check your connection.';
  }

  // Server responded with error
  const { status, data } = error.response;

  // Handle specific status codes
  switch (status) {
    case 400:
      // Bad request - try to extract validation errors
      if (data && typeof data === 'object') {
        const errorData = data as Record<string, unknown>;
        if (errorData.detail) {
          return String(errorData.detail);
        }
        // Format validation errors
        const errors = Object.entries(errorData)
          .map(([field, messages]) => {
            if (Array.isArray(messages)) {
              return `${field}: ${messages.join(', ')}`;
            }
            return `${field}: ${String(messages)}`;
          })
          .join('; ');
        return errors || 'Invalid request data.';
      }
      return 'Invalid request data.';

    case 401:
      return 'Authentication required. Please log in.';

    case 403:
      return 'You do not have permission to perform this action.';

    case 404:
      return 'Resource not found.';

    case 409:
      return 'Conflict. The resource already exists or the action cannot be completed.';

    case 429:
      return 'Too many requests. Please try again later.';

    case 500:
      return 'Server error. Please try again later.';

    case 503:
      return 'Service temporarily unavailable. Please try again later.';

    default:
      // Try to extract error message from response data
      if (data && typeof data === 'object') {
        const errorData = data as Record<string, unknown>;
        if (errorData.detail) {
          return String(errorData.detail);
        }
        if (errorData.message) {
          return String(errorData.message);
        }
      }
      return `Request failed with status ${status}.`;
  }
}

export default apiClient;
