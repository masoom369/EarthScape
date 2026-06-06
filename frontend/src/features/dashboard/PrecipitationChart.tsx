import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { theme } from '../../styles/theme';
import type { ClimateSummaryItem } from '../../types/climate';

export function PrecipitationChart({ data }: { data: ClimateSummaryItem[] }) {
  const chartData = data.map((d) => ({
    label: `${d.region} ${d.period}`,
    precipitation: d.total_precipitation_mm || 0,
  }));

  return (
    <div style={{ background: theme.colors.surface, padding: theme.spacing.lg, borderRadius: theme.radius.lg }}>
      <h3>Precipitation by Region</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData}>
          <XAxis dataKey="label" tick={{ fontSize: 10 }} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="precipitation" fill={theme.chartPalette[1]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
