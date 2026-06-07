import { useCallback } from "react";
import api from "@/lib/api";
import { useAlertStore } from "@/stores/alertStore";
import { usePoll } from "./usePoll";
import type { PaginatedAlertEvents } from "@/types/alert";

const INTERVAL = Number(import.meta.env.VITE_POLL_ALERTS_MS ?? 15000);

export function useAlertPoll(enabled = true) {
  const setUnacknowledged = useAlertStore((s) => s.setUnacknowledged);

  const fetch = useCallback(async () => {
    try {
      const { data } = await api.get<PaginatedAlertEvents>(
        "/alerts/events?acknowledged=false&limit=50"
      );
      setUnacknowledged(data.items);
    } catch {
      // silently ignore poll errors
    }
  }, [setUnacknowledged]);

  usePoll(fetch, INTERVAL, enabled);
}