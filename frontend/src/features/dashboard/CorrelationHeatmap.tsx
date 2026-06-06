import { theme } from '../../styles/theme';

const METRICS = ['temperature_c', 'co2_ppm', 'precipitation_mm', 'humidity_pct'];

export function CorrelationHeatmap({ matrix }: { matrix: Record<string, Record<string, number | null>> | null }) {
  if (!matrix) {
    return (
      <div style={{ background: theme.colors.surface, padding: theme.spacing.lg, borderRadius: theme.radius.lg }}>
        <h3>Correlation Heatmap</h3>
        <p style={{ color: theme.colors.textMuted }}>Run correlation ML training to populate this chart.</p>
      </div>
    );
  }

  const colorFor = (val: number | null) => {
    if (val === null) return theme.colors.border;
    const intensity = Math.abs(val);
    return val > 0
      ? `rgba(26, 107, 74, ${intensity})`
      : `rgba(192, 57, 43, ${intensity})`;
  };

  return (
    <div style={{ background: theme.colors.surface, padding: theme.spacing.lg, borderRadius: theme.radius.lg }}>
      <h3>Correlation Heatmap</h3>
      <table style={{ borderCollapse: 'collapse', fontSize: theme.fontSize.sm }}>
        <thead>
          <tr>
            <th />
            {METRICS.map((m) => <th key={m} style={{ padding: theme.spacing.sm }}>{m}</th>)}
          </tr>
        </thead>
        <tbody>
          {METRICS.map((row) => (
            <tr key={row}>
              <td style={{ padding: theme.spacing.sm, fontWeight: 600 }}>{row}</td>
              {METRICS.map((col) => {
                const val = matrix[row]?.[col] ?? null;
                return (
                  <td key={col} style={{
                    padding: theme.spacing.sm, textAlign: 'center',
                    background: colorFor(val), color: val !== null && Math.abs(val) > 0.5 ? '#fff' : theme.colors.text,
                  }}>
                    {val !== null ? val.toFixed(2) : '—'}
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
