import { Badge } from '../../components/Badge';
import { Table } from '../../components/Table';
import type { JobLog } from '../../types/job';

export function JobStatusList({ jobs }: { jobs: JobLog[] }) {
  return (
    <Table
      data={jobs}
      columns={[
        { key: 'name', header: 'Name', render: (r) => r.job_name },
        { key: 'type', header: 'Type', render: (r) => r.job_type },
        { key: 'status', header: 'Status', render: (r) => <Badge status={r.status}>{r.status}</Badge> },
        { key: 'duration', header: 'Duration', render: (r) => r.duration_seconds != null ? `${r.duration_seconds}s` : '—' },
        { key: 'started', header: 'Started', render: (r) => new Date(r.started_at).toLocaleString() },
      ]}
    />
  );
}
