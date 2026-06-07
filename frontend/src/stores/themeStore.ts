import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark";

interface ThemeStore {
  theme: Theme;
  toggle: () => void;
  set: (t: Theme) => void;
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: "dark",
      toggle: () => set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),
      set: (theme) => set({ theme }),
    }),
    { name: "earthscape-theme" }
  )
);