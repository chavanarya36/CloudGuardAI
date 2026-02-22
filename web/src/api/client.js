import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// ---------------------------------------------------------------------------
// Request interceptor — attach auth token if available
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cg_api_key') || localStorage.getItem('cg_jwt');
    if (token) {
      if (token.startsWith('cg_')) {
        config.headers['X-API-Key'] = token;
      } else {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---------------------------------------------------------------------------
// Response interceptor — global error handling + retry on 5xx
// ---------------------------------------------------------------------------
const MAX_RETRIES = 2;
const RETRY_DELAY = 1000;

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    const status = error.response?.status;

    if (status && status >= 502 && status <= 504 && (!config._retryCount || config._retryCount < MAX_RETRIES)) {
      config._retryCount = (config._retryCount || 0) + 1;
      await new Promise((r) => setTimeout(r, RETRY_DELAY * config._retryCount));
      return apiClient(config);
    }

    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('api-error', { detail: { status, message, url: config?.url } }));
    }

    return Promise.reject({ status, message, original: error });
  }
);

// Scan
export const scanFile = async (file, scanMode = 'all') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('scan_mode', scanMode);
  const response = await apiClient.post('/scan', formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000 });
  return response.data;
};

export const getScan = async (scanId) => { const r = await apiClient.get(`/scan/${scanId}`); return r.data; };
export const listScans = async (skip = 0, limit = 100) => { const r = await apiClient.get('/scans', { params: { skip, limit } }); return r.data; };
export const deleteScan = async (scanId) => { const r = await apiClient.delete(`/scans/${scanId}`); return r.data; };

// Stats
export const getScanStats = async () => { const r = await apiClient.get('/scans/stats'); return r.data; };
export const getFeedbackStats = async () => { const r = await apiClient.get('/feedback/stats'); return r.data; };

// Feedback
export const submitFeedback = async (feedbackData) => { const r = await apiClient.post('/feedback', feedbackData); return r.data; };
export const listFeedback = async (skip = 0, limit = 100) => { const r = await apiClient.get('/feedback', { params: { skip, limit } }); return r.data; };

// Model
export const getModelStatus = async () => { const r = await apiClient.get('/model/status'); return r.data; };
export const triggerRetrain = async (force = false, minSamples = 100) => { const r = await apiClient.post('/model/retrain', { force, min_samples: minSamples }); return r.data; };
export const listModelVersions = async (skip = 0, limit = 10) => { const r = await apiClient.get('/model/versions', { params: { skip, limit } }); return r.data; };

// Adaptive Learning
export const getLearningStatus = async () => { const r = await apiClient.get('/learning/status'); return r.data; };
export const getDiscoveredPatterns = async () => { const r = await apiClient.get('/learning/patterns'); return r.data; };
export const getPatternDetail = async (signature) => { const r = await apiClient.get(`/learning/patterns/${signature}`); return r.data; };
export const getDriftStatus = async () => { const r = await apiClient.get('/learning/drift'); return r.data; };
export const getRuleWeights = async () => { const r = await apiClient.get('/learning/rule-weights'); return r.data; };
export const getLearningTelemetry = async (limit = 50) => { const r = await apiClient.get('/learning/telemetry', { params: { limit } }); return r.data; };
export const triggerPatternDiscovery = async () => { const r = await apiClient.post('/learning/discover'); return r.data; };

// Auth
export const getToken = async (subject = 'web_user') => { const fd = new FormData(); fd.append('subject', subject); const r = await apiClient.post('/auth/token', fd); return r.data; };
export const getMetrics = async () => { const r = await apiClient.get('/metrics'); return r.data; };

// Settings helpers
export const setApiKey = (key) => localStorage.setItem('cg_api_key', key);
export const clearAuth = () => { localStorage.removeItem('cg_api_key'); localStorage.removeItem('cg_jwt'); };

export default apiClient;
