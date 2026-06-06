import { create } from 'zustand';
import api from '../services/api';
import type { User } from '../types/auth';

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,
  login: async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password });
    set({ user: data });
  },
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      set({ user: null });
    }
  },
  fetchMe: async () => {
    try {
      const { data } = await api.get('/auth/me');
      set({ user: data, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },
}));
