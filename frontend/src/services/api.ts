import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      const duration = response.config.metadata?.duration;
      if (duration !== undefined) {
        console.debug(`[API] ${response.config.method?.toUpperCase()} ${response.config.url} — ${duration}ms`);
      }
    }
    return response;
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Request failed';
    return Promise.reject(new Error(typeof message === 'string' ? message : JSON.stringify(message)));
  },
);

api.interceptors.request.use((config) => {
  config.metadata = { start: performance.now() };
  return config;
});

api.interceptors.response.use((response) => {
  if (response.config.metadata?.start) {
    response.config.metadata.duration = performance.now() - response.config.metadata.start;
  }
  return response;
});

declare module 'axios' {
  export interface AxiosRequestConfig {
    metadata?: { start?: number; duration?: number };
  }
}

export default api;
