import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ValueType } from "recharts/types/component/DefaultTooltipContent";
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
    const precip = item.total_precipitation_mm;
    if (precip === null || precip === undefined) continue;
    const num = Number(precip);
    if (!isFinite(num)) continue;
    byPeriod[item.period] = (byPeriod[item.period] ?? 0) + num;
  }

  const data = Object.entries(byPeriod)
    .map(([period, total]) => ({
      period,
      total: Math.round(total * 10) / 10,
    }))
    .sort((a, b) => a.period.localeCompare(b.period))
    .slice(-12);

  if (!data.length) {
    return <EmptyState icon={<CloudRain size={22} />} title="No precipitation data" />;
  }

  function formatTooltip(value: ValueType | undefined): [string, string] {
    if (value === undefined) return ["— mm", "Precipitation"];
    const num = Number(value);
    return [`${isFinite(num) ? num : "—"} mm`, "Precipitation"];
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
        <XAxis
          dataKey="period"
          tick={{ fontSize: 11, fill: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--text-tertiary)" }}
          unit=" mm"
          domain={[0, "auto"]}
        />
        <Tooltip
          contentStyle={{
            background: "var(--bg-elevated)",
            border: "1px solid var(--border-default)",
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={formatTooltip}
        />
        <Bar
          dataKey="total"
          name="Precipitation mm"
          fill="var(--chart-2)"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}