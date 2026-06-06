import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Table } from '../../components/Table';
import type { AlertEvent } from '../../types/alert';

export function AlertEventLog({ events, onAcknowledge }: {
  events: AlertEvent[]; onAcknowledge: (id: string) => void;
}) {
  return (
    <Table
      data={events}
      columns={[
        { key: 'severity', header: 'Severity', render: (r) => <Badge status={r.severity}>{r.severity}</Badge> },
        { key: 'value', header: 'Value', render: (r) => r.triggered_value },
        { key: 'time', header: 'Triggered', render: (r) => new Date(r.triggered_at).toLocaleString() },
        { key: 'ack', header: 'Acknowledged', render: (r) => r.acknowledged ? 'Yes' : (
          <Button variant="secondary" onClick={() => onAcknowledge(r.id)}>Acknowledge</Button>
        )},
      ]}
    />
  );
}
