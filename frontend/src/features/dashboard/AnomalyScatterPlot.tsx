import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts';
import { theme } from '../../styles/theme';
import type { ClimateRecord } from '../../types/climate';

export function AnomalyScatterPlot({ data }: { data: ClimateRecord[] }) {
  const points = data.map((r) => ({
    x: new Date(r.timestamp).getTime(),
    y: r.temperature_c || 0,
    anomaly: r.is_anomaly,
    region: r.location.region,
  }));

  const normal = points.filter((p) => !p.anomaly);
  const anomalies = points.filter((p) => p.anomaly);

  return (
    <div style={{ background: theme.colors.surface, padding: theme.spacing.lg, borderRadius: theme.radius.lg }}>
      <h3>Anomaly Scatter Plot</h3>
      <ResponsiveContainer width="100%" height={280}>
        <ScatterChart>
          <CartesianGrid />
          <XAxis dataKey="x" type="number" domain={['auto', 'auto']} tickFormatter={(v) => new Date(v).toLocaleDateString()} />
          <YAxis dataKey="y" name="Temp °C" />
          <ZAxis range={[40, 40]} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} labelFormatter={(v) => new Date(Number(v)).toLocaleString()} />
          <Scatter name="Normal" data={normal} fill={theme.chartPalette[0]} />
          <Scatter name="Anomaly" data={anomalies} fill={theme.colors.anomaly} shape="triangle" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
