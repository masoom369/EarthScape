import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts';
import { theme } from '../../styles/theme';
import type { ClimateSummaryItem } from '../../types/climate';

export function TemperatureTrendChart({ data, forecast }: {
  data: ClimateSummaryItem[];
  forecast?: Array<{ region: string; date: string; forecast_temp_c: number }>;
}) {
  const chartData = data.map((d) => ({
    period: `${d.region} ${d.period}`,
    temperature: d.avg_temperature_c,
  }));

  const forecastData = (forecast || []).map((f) => ({
    period: f.date.slice(0, 10),
    forecast: f.forecast_temp_c,
  }));

  const merged = [...chartData, ...forecastData.map((f) => ({ period: f.period, temperature: undefined, forecast: f.forecast }))];

  return (
    <div style={{ background: theme.colors.surface, padding: theme.spacing.lg, borderRadius: theme.radius.lg }}>
      <h3>Temperature Trend</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={merged.length ? merged : chartData}>
          <XAxis dataKey="period" tick={{ fontSize: 11 }} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="temperature" stroke={theme.chartPalette[0]} name="Historical" dot={false} />
          <Line type="monotone" dataKey="forecast" stroke={theme.colors.forecast} strokeDasharray="5 5" name="Forecast" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
