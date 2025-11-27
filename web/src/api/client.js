import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const scanFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/scan', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getScan = async (scanId) => {
  const response = await apiClient.get(`/scan/${scanId}`);
  return response.data;
};

export const listScans = async (skip = 0, limit = 100) => {
  const response = await apiClient.get('/scans', {
    params: { skip, limit },
  });
  return response.data;
};

export const submitFeedback = async (feedbackData) => {
  const response = await apiClient.post('/feedback', feedbackData);
  return response.data;
};

export const listFeedback = async (skip = 0, limit = 100) => {
  const response = await apiClient.get('/feedback', {
    params: { skip, limit },
  });
  return response.data;
};

export const getModelStatus = async () => {
  const response = await apiClient.get('/model/status');
  return response.data;
};

export const triggerRetrain = async (force = false, minSamples = 100) => {
  const response = await apiClient.post('/model/retrain', {
    force,
    min_samples: minSamples,
  });
  return response.data;
};

export const listModelVersions = async (skip = 0, limit = 10) => {
  const response = await apiClient.get('/model/versions', {
    params: { skip, limit },
  });
  return response.data;
};

export default apiClient;
