import apiClient from './client';

export const api = {
  /**
   * Check the health of the backend service.
   * @returns {Promise<{status: str, service: str, version: str}>}
   */
  checkHealth: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  getDatasetStatus: async () => {
    const response = await apiClient.get('/dataset-status');
    return response.data;
  },

  /**
   * Get the latest benchmark results.
   * @returns {Promise<Object>}
   */
  getBenchmarkResults: async () => {
    const response = await apiClient.get('/benchmark-results');
    return response.data;
  },

  submitQuery: async (query) => {
    return await apiClient.post('/query', { query });
  },

  /**
   * Submit an audio recording for processing.
   * @param {Blob} audioBlob - The recorded audio blob
   * @returns {Promise<{status: str, message: str, content_type: str, file_size: int, filename: str}>}
   */
  submitVoiceQuery: async (audioBlob) => {
    console.log("Voice Query Upload Debug:", {
      size: audioBlob.size,
      type: audioBlob.type,
      filename: 'recording.webm'
    });

    const formData = new FormData();
    // Use a default filename; the content-type is determined by the Blob
    formData.append('audio', audioBlob, 'recording.webm');
    
    // Axios will automatically set the correct Content-Type with the generated boundary
    return await apiClient.post('/voice-query', formData);
  },
};
