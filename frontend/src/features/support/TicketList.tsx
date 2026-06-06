import { Badge } from '../../components/Badge';
import { Table } from '../../components/Table';
import type { SupportTicket } from '../../types/support';

export function TicketList({ tickets }: { tickets: SupportTicket[] }) {
  return (
    <Table
      data={tickets}
      columns={[
        { key: 'subject', header: 'Subject', render: (r) => r.subject },
        { key: 'status', header: 'Status', render: (r) => <Badge status={r.status}>{r.status}</Badge> },
        { key: 'created', header: 'Created', render: (r) => new Date(r.created_at).toLocaleString() },
        { key: 'response', header: 'Response', render: (r) => r.response || '—' },
      ]}
    />
  );
}
