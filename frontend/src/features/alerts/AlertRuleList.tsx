import api from '../../services/api';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Table } from '../../components/Table';
import type { AlertRule } from '../../types/alert';

export function AlertRuleList({ rules, onChanged }: { rules: AlertRule[]; onChanged: () => void }) {
  const toggle = async (id: string, active: boolean) => {
    await api.patch(`/alerts/rules/${id}`, { is_active: !active });
    onChanged();
  };

  const remove = async (id: string) => {
    await api.delete(`/alerts/rules/${id}`);
    onChanged();
  };

  return (
    <Table
      data={rules}
      columns={[
        { key: 'name', header: 'Name', render: (r) => r.name },
        { key: 'metric', header: 'Metric', render: (r) => `${r.metric} ${r.operator} ${r.threshold}` },
        { key: 'severity', header: 'Severity', render: (r) => <Badge status={r.severity}>{r.severity}</Badge> },
        { key: 'active', header: 'Active', render: (r) => r.is_active ? 'Yes' : 'No' },
        { key: 'actions', header: 'Actions', render: (r) => (
          <span style={{ display: 'flex', gap: 8 }}>
            <Button variant="secondary" onClick={() => toggle(r.id, r.is_active)}>Toggle</Button>
            <Button variant="danger" onClick={() => remove(r.id)}>Delete</Button>
          </span>
        )},
      ]}
    />
  );
}
