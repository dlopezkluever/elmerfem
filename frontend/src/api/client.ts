import axios, { AxiosError } from 'axios';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any request modifications here (e.g., auth tokens in the future)
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;
      
      switch (status) {
        case 400:
          throw new Error(data.detail || 'Invalid request. Please check your input.');
        case 422:
          // Validation error
          if (data.detail && Array.isArray(data.detail)) {
            const messages = data.detail.map((err: any) => 
              `${err.loc.join('.')}: ${err.msg}`
            ).join(', ');
            throw new Error(`Validation error: ${messages}`);
          }
          throw new Error(data.detail || 'Validation error. Please check your input.');
        case 500:
          throw new Error('Server error. Please try again later.');
        default:
          throw new Error(data.detail || `Request failed with status ${status}`);
      }
    } else if (error.request) {
      // Request made but no response
      throw new Error('Cannot connect to simulation server. Please check your Docker setup.');
    } else {
      // Something else happened
      throw new Error(error.message || 'An unexpected error occurred.');
    }
  }
);

export default apiClient; 