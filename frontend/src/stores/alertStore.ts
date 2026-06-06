import { create } from 'zustand';
import api from '../services/api';
import type { AlertEvent } from '../types/alert';

interface AlertState {
  events: AlertEvent[];
  fetchEvents: () => Promise<void>;
  acknowledge: (id: string) => Promise<void>;
}

export const useAlertStore = create<AlertState>((set) => ({
  events: [],
  fetchEvents: async () => {
    const { data } = await api.get('/alerts/events', { params: { acknowledged: false, limit: 50 } });
    set({ events: data.items });
  },
  acknowledge: async (id) => {
    await api.patch(`/alerts/events/${id}/acknowledge`);
    set((s) => ({ events: s.events.filter((e) => e.id !== id) }));
  },
}));
