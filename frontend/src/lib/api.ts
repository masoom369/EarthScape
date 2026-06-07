import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      // Let each page/hook decide how to handle 401 — no global redirect here
      // to avoid redirect loops on the login page itself
    }
    return Promise.reject(err instanceof Error ? err : new Error(String(err)));
  }
);

export default api;