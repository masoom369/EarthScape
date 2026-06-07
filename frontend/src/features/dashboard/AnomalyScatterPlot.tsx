import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import type { MLResult } from "@/types/ml";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import { Activity } from "lucide-react";

interface Props {
  mlResult: MLResult | null;
  loading: boolean;
}

export default function AnomalyScatterPlot({ mlResult, loading }: Props) {
  if (loading) return <div className="h-64 flex items-center justify-center"><Spinner /></div>;
  if (!mlResult?.predictions.length) {
    return (
      <EmptyState
        icon={<Activity size={22} />}
        title="No anomaly data"
        description="Train the anomaly detection model to see results"
      />
    );
  }

  const data = (mlResult.predictions as Array<{ record_id: string; score: number; is_anomaly: boolean }>)
    .slice(0, 200)
    .map((p, i) => ({ x: i, y: p.score, anomaly: p.is_anomaly }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ScatterChart margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
        <XAxis dataKey="x" name="Index" tick={{ fontSize: 11, fill: "var(--text-tertiary)" }} />
        <YAxis dataKey="y" name="Score" tick={{ fontSize: 11, fill: "var(--text-tertiary)" }} />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", borderRadius: 8, fontSize: 12 }}
        />
        <Scatter data={data}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.anomaly ? "var(--chart-4)" : "var(--chart-1)"}
              fillOpacity={entry.anomaly ? 0.9 : 0.5}
            />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}