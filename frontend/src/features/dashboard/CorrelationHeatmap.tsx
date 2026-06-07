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

function getColor(val: number | null): string {
  if (val == null) return "var(--bg-elevated)";
  const abs = Math.abs(val);
  if (val > 0) return `rgba(34, 197, 94, ${0.2 + abs * 0.8})`;
  return `rgba(239, 68, 68, ${0.2 + abs * 0.8})`;
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
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="p-2" />
            {METRICS.map((m) => (
              <th
                key={m}
                className="p-2 text-center font-medium"
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
                className="p-2 font-medium pr-3 text-right"
                style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}
              >
                {LABELS[row]}
              </td>
              {METRICS.map((col) => {
                const val = matrix[row]?.[col] ?? null;
                return (
                  <td
                    key={col}
                    className="p-2 text-center rounded font-medium"
                    style={{
                      background: getColor(val),
                      color: val != null && Math.abs(val) > 0.5 ? "white" : "var(--text-primary)",
                      minWidth: "3.5rem",
                    }}
                  >
                    {val != null ? val.toFixed(2) : "—"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}