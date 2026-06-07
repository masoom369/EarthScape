import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import type { ClimateSummaryResponse } from "@/types/climate";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import { Thermometer } from "lucide-react";

interface Props {
  summary: ClimateSummaryResponse | null;
  forecast: Array<{ region: string; date: string; forecast_temp_c: number }> | null;
  loading: boolean;
}

export default function TemperatureTrendChart({ summary, forecast, loading }: Props) {
  if (loading) return <div className="h-64 flex items-center justify-center"><Spinner /></div>;

  if (!summary?.items.length) {
    return <EmptyState icon={<Thermometer size={22} />} title="No temperature data" description="Ingest data to see trends" />;
  }

  // Aggregate by period across regions
  const byPeriod: Record<string, { period: string; actual: number | null; forecast?: number }> = {};
  for (const item of summary.items) {
    if (!byPeriod[item.period]) {
      byPeriod[item.period] = { period: item.period, actual: item.avg_temperature_c };
    } else {
      const prev = byPeriod[item.period].actual ?? 0;
      byPeriod[item.period].actual = ((prev + (item.avg_temperature_c ?? 0)) / 2);
    }
  }

  // Attach forecast
  if (forecast) {
    for (const f of forecast) {
      const key = f.date.slice(0, 7);
      if (!byPeriod[key]) byPeriod[key] = { period: key, actual: null };
      byPeriod[key].forecast = f.forecast_temp_c;
    }
  }

  const data = Object.values(byPeriod).sort((a, b) => a.period.localeCompare(b.period)).slice(-18);

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
        <XAxis dataKey="period" tick={{ fontSize: 11, fill: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }} />
        <YAxis tick={{ fontSize: 11, fill: "var(--text-tertiary)" }} unit="°C" />
        <Tooltip
          contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "var(--text-primary)" }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="actual" name="Actual °C" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="forecast" name="Forecast °C" stroke="var(--chart-3)" strokeWidth={2} strokeDasharray="5 3" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}