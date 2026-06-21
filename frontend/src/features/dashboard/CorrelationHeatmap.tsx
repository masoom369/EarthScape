import type { MLResult } from "@/types/ml";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import { BarChart2 } from "lucide-react";

const METRICS = ["temperature_c", "co2_ppm", "precipitation_mm", "humidity_pct"];
const LABELS: Record<string, string> = {
  temperature_c: "Temp",
  co2_ppm: "CO₂",
  precipitation_mm: "Precip",
  humidity_pct: "Humid",
};

// Theme-aware cell color: blends toward brand green (positive) or danger red
// (negative) using the same CSS custom properties as the rest of the app,
// instead of hardcoded rgba() that ignored light/dark contrast.
function getCellStyle(val: number | null): React.CSSProperties {
  if (val == null) {
    return { background: "var(--bg-elevated)", color: "var(--text-tertiary)" };
  }
  const abs = Math.abs(val);
  const intensity = Math.round(20 + abs * 70); // 20%-90% mix
  const tint = val >= 0 ? "var(--success)" : "var(--danger)";
  return {
    background: `color-mix(in srgb, ${tint} ${intensity}%, var(--bg-elevated))`,
    color: abs > 0.45 ? "white" : "var(--text-primary)",
    fontWeight: abs > 0.45 ? 600 : 500,
  };
}

interface Props {
  mlResult: MLResult | null;
  loading: boolean;
}

export default function CorrelationHeatmap({ mlResult, loading }: Props) {
  if (loading) return <div className="h-64 flex items-center justify-center"><Spinner /></div>;
  const matrix = mlResult?.correlation_matrix;
  if (!matrix) {
    return (
      <EmptyState
        icon={<BarChart2 size={22} />}
        title="No correlation data"
        description="Train the correlation model to see the matrix"
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse" style={{ borderSpacing: "6px" }}>
        <thead>
          <tr>
            <th className="p-2 w-16" />
            {METRICS.map((m) => (
              <th
                key={m}
                className="pb-3 text-center text-xs font-semibold"
                style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}
              >
                {LABELS[m]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {METRICS.map((row) => (
            <tr key={row}>
              <td
                className="pr-3 text-right text-xs font-semibold whitespace-nowrap"
                style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}
              >
                {LABELS[row]}
              </td>
              {METRICS.map((col) => {
                const val = matrix[row]?.[col] ?? null;
                return (
                  <td key={col} className="p-1">
                    <div
                      className="flex items-center justify-center rounded-lg text-sm transition-transform duration-150 hover:scale-[1.04]"
                      style={{
                        ...getCellStyle(val),
                        minWidth: "3.75rem",
                        height: "2.75rem",
                        fontFamily: "var(--font-mono)",
                      }}
                      title={`${LABELS[row]} × ${LABELS[col]}: ${val != null ? val.toFixed(4) : "insufficient data"}`}
                    >
                      {val != null ? val.toFixed(2) : "—"}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-4 mt-4 text-xs" style={{ color: "var(--text-tertiary)" }}>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ background: "var(--danger)" }} />
          Negative
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }} />
          Weak
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded" style={{ background: "var(--success)" }} />
          Positive
        </span>
      </div>
    </div>
  );
}