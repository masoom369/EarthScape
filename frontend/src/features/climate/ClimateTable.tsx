import { Badge } from '../../components/Badge';
import { Table } from '../../components/Table';
import type { ClimateRecord } from '../../types/climate';

export function ClimateTable({ records }: { records: ClimateRecord[] }) {
  return (
    <Table
      data={records}
      columns={[
        { key: 'region', header: 'Region', render: (r) => r.location.region },
        { key: 'source', header: 'Source', render: (r) => r.source_type },
        { key: 'time', header: 'Timestamp', render: (r) => new Date(r.timestamp).toLocaleString() },
        { key: 'temp', header: 'Temp °C', render: (r) => r.temperature_c ?? '—' },
        { key: 'precip', header: 'Precip mm', render: (r) => r.precipitation_mm ?? '—' },
        { key: 'humidity', header: 'Humidity %', render: (r) => r.humidity_pct ?? '—' },
        { key: 'co2', header: 'CO₂ ppm', render: (r) => r.co2_ppm ?? '—' },
        { key: 'anomaly', header: 'Anomaly', render: (r) => r.is_anomaly ? <Badge status="high">Yes</Badge> : '—' },
      ]}
    />
  );
}
