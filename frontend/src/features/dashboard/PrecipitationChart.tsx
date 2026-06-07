import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ClimateSummaryResponse } from "@/types/climate";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import { CloudRain } from "lucide-react";

interface Props {
  summary: ClimateSummaryResponse | null;
  loading: boolean;
}

export default function PrecipitationChart({ summary, loading }: Props) {
  if (loading) return <div className="h-64 flex items-center justify-center"><Spinner /></div>;
  if (!summary?.items.length) {
    return <EmptyState icon={<CloudRain size={22} />} title="No precipitation data" />;
  }

  const byPeriod: Record<string, number> = {};
  for (const item of summary.items) {
    byPeriod[item.period] = (byPeriod[item.period] ?? 0) + (item.total_precipitation_mm ?? 0);
  }
  const data = Object.entries(byPeriod)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-12)
    .map(([period, total]) => ({ period, total: Math.round(total) }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
        <XAxis dataKey="period" tick={{ fontSize: 11, fill: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }} />
        <YAxis tick={{ fontSize: 11, fill: "var(--text-tertiary)" }} unit=" mm" />
        <Tooltip
          contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", borderRadius: 8, fontSize: 12 }}
        />
        <Bar dataKey="total" name="Precipitation mm" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}