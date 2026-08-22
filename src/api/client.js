import axios from 'axios';

// Create an Axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  // Let Axios automatically infer the Content-Type based on the payload (JSON vs FormData)
});

// Response interceptor for generic error handling
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    // Extract a meaningful error message
    let errorMessage = 'An unexpected server error occurred.';
    
    if (error.response) {
      if (error.response.data && error.response.data.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          // Handle FastAPI 422 Validation errors
          errorMessage = detail.map(e => e.msg).join(', ');
        } else if (typeof detail === 'object' && detail !== null) {
          // Handle structured errors
          errorMessage = detail.message || JSON.stringify(detail);
        } else {
          errorMessage = detail;
        }
      } else {
        errorMessage = `Server error: ${error.response.status}`;
      }
    } else if (error.request) {
      // The request was made but no response was received
      errorMessage = 'No response received from the server. Please check your connection.';
    } else {
      // Something happened in setting up the request that triggered an Error
      errorMessage = error.message;
    }
    
    // Return a standardized error object
    return Promise.reject({
      message: errorMessage,
      originalError: error
    });
  }
);

export default apiClient;
