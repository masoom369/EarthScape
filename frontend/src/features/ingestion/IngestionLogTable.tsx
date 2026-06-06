import { Badge } from '../../components/Badge';
import { Table } from '../../components/Table';

interface IngestionLog {
  id: string;
  filename: string;
  status: string;
  record_count: number;
  hdfs_path?: string;
  created_at: string;
}

export function IngestionLogTable({ logs }: { logs: IngestionLog[] }) {
  return (
    <Table
      data={logs}
      columns={[
        { key: 'filename', header: 'File', render: (r) => r.filename },
        { key: 'status', header: 'Status', render: (r) => <Badge status={r.status}>{r.status}</Badge> },
        { key: 'count', header: 'Records', render: (r) => r.record_count },
        { key: 'hdfs', header: 'HDFS Path', render: (r) => r.hdfs_path || '—' },
        { key: 'date', header: 'Date', render: (r) => new Date(r.created_at).toLocaleString() },
      ]}
    />
  );
}
