import { create } from "zustand";
import type { UserProfile } from "@/types/auth";
import api from "@/lib/api";

interface AuthStore {
  user: UserProfile | null;
  loading: boolean;
  init: () => Promise<void>;
  setUser: (u: UserProfile | null) => void;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  loading: true,

  init: async () => {
    try {
      const { data } = await api.get<UserProfile>("/auth/me");
      set({ user: data, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },

  setUser: (user) => set({ user }),

  logout: async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      set({ user: null });
    }
  },
}));