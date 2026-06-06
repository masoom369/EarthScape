import { theme } from '../styles/theme';

export interface FilterValues {
  region?: string;
  source_type?: string;
  from_date?: string;
  to_date?: string;
  is_anomaly?: string;
  is_archived?: string;
}

interface FilterBarProps {
  values: FilterValues;
  onChange: (values: FilterValues) => void;
}

const inputStyle = {
  padding: theme.spacing.sm,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: theme.radius.md,
  fontSize: theme.fontSize.sm,
};

export function FilterBar({ values, onChange }: FilterBarProps) {
  const set = (key: keyof FilterValues, val: string) => onChange({ ...values, [key]: val || undefined });

  return (
    <div style={{ display: 'flex', gap: theme.spacing.md, flexWrap: 'wrap', marginBottom: theme.spacing.lg }}>
      <input style={inputStyle} placeholder="Region" value={values.region || ''} onChange={(e) => set('region', e.target.value)} />
      <select style={inputStyle} value={values.source_type || ''} onChange={(e) => set('source_type', e.target.value)}>
        <option value="">All sources</option>
        <option value="satellite">Satellite</option>
        <option value="weather_station">Weather Station</option>
        <option value="sensor">Sensor</option>
      </select>
      <input style={inputStyle} type="date" value={values.from_date || ''} onChange={(e) => set('from_date', e.target.value)} />
      <input style={inputStyle} type="date" value={values.to_date || ''} onChange={(e) => set('to_date', e.target.value)} />
      <select style={inputStyle} value={values.is_anomaly || ''} onChange={(e) => set('is_anomaly', e.target.value)}>
        <option value="">All records</option>
        <option value="true">Anomalies only</option>
        <option value="false">Normal only</option>
      </select>
    </div>
  );
}
