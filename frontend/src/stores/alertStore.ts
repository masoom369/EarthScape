import { create } from "zustand";
import type { AlertEvent } from "@/types/alert";

interface AlertStore {
  unacknowledged: AlertEvent[];
  setUnacknowledged: (events: AlertEvent[]) => void;
  acknowledge: (id: string) => void;
}

export const useAlertStore = create<AlertStore>((set) => ({
  unacknowledged: [],
  setUnacknowledged: (events) => set({ unacknowledged: events }),
  acknowledge: (id) =>
    set((s) => ({
      unacknowledged: s.unacknowledged.filter((e) => e.id !== id),
    })),
}));