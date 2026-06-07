import { useState, useCallback } from "react";
import api from "@/lib/api";
import { usePoll } from "@/hooks/usePoll";
import type { ClimateRecord } from "@/types/climate";
import { formatDateTime, formatNumber } from "@/lib/utils";
import Spinner from "@/components/ui/Spinner";

interface Props {
  pollMs: number;
}

export default function RealtimeFeedPanel({ pollMs }: Props) {
  const [records, setRecords] = useState<ClimateRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const { data } = await api.get<{ items: ClimateRecord[] }>("/climate/realtime?n=10");
      setRecords(data.items);
    } finally {
      setLoading(false);
    }
  }, []);

  usePoll(fetch, pollMs);

  if (loading) return <div className="h-32 flex items-center justify-center"><Spinner /></div>;
  if (!records.length) {
    return <p className="text-sm py-4 text-center" style={{ color: "var(--text-tertiary)" }}>No sensor data yet</p>;
  }

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {records.map((r) => (
        <div
          key={r.id}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs"
          style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full shrink-0 pulse-dot"
            style={{ background: "var(--success)" }}
          />
          <span className="font-medium shrink-0" style={{ color: "var(--text-primary)" }}>
            {r.location.region}
          </span>
          <span style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>
            {formatNumber(r.temperature_c, 1)}°C
          </span>
          <span style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>
            {formatNumber(r.humidity_pct, 0)}%
          </span>
          <span className="ml-auto shrink-0" style={{ color: "var(--text-tertiary)" }}>
            {formatDateTime(r.timestamp)}
          </span>
        </div>
      ))}
    </div>
  );
}