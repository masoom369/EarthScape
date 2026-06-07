import axios from "axios";
import type { AxiosRequestConfig } from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      // Let each page/hook handle 401 — no global redirect to avoid login-page loops
    }
    return Promise.reject(err instanceof Error ? err : new Error(String(err)));
  }
);

/**
 * Like api.get but returns null instead of throwing on 404.
 * Use for optional data that may not exist yet (e.g. ML results before first training run).
 * Avoids noisy browser console errors for an expected missing-data state.
 */
export async function getOrNull<T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T | null> {
  const res = await api.get<T>(url, {
    ...config,
    validateStatus: (s) => (s >= 200 && s < 300) || s === 404,
  });
  return res.status === 404 ? null : res.data;
}

export default api;