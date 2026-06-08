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
    // Only reject non-404 errors — 404s are handled by getOrNull via validateStatus.
    // Never swallow 404s here: doing so breaks validateStatus contract and causes
    // getOrNull to receive a resolved response it can't inspect for status code.
    if (err.response?.status === 401) {
      // Let each page/hook handle 401 — no global redirect to avoid login-page loops
    }
    return Promise.reject(err instanceof Error ? err : new Error(String(err)));
  }
);

/**
 * Fetch a resource that may not exist yet (e.g. ML results before first training run).
 * Returns null on 404 without logging a console error.
 * Uses validateStatus so axios never rejects on 404 — no interceptor conflict.
 */
export async function getOrNull<T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T | null> {
  try {
    const res = await api.get<T>(url, {
      ...config,
      // Accept both success and 404 — axios will not throw, interceptor won't fire
      validateStatus: (s) => (s >= 200 && s < 300) || s === 404,
    });
    return res.status === 404 ? null : res.data;
  } catch {
    // Network error or non-404 failure — return null silently for optional data
    return null;
  }
}

export default api;