import api from '../../services/api';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Table } from '../../components/Table';

interface UserRow { id: string; email: string; role: string; is_active: boolean; }

export function UserTable({ users, onChanged }: { users: UserRow[]; onChanged: () => void }) {
  const deactivate = async (id: string) => {
    await api.delete(`/users/${id}`);
    onChanged();
  };

  return (
    <Table
      data={users}
      columns={[
        { key: 'email', header: 'Email', render: (r) => r.email },
        { key: 'role', header: 'Role', render: (r) => r.role },
        { key: 'active', header: 'Status', render: (r) => (
          <Badge status={r.is_active ? 'success' : 'failed'}>{r.is_active ? 'Active' : 'Inactive'}</Badge>
        )},
        { key: 'actions', header: 'Actions', render: (r) => (
          r.is_active ? <Button variant="danger" onClick={() => deactivate(r.id)}>Deactivate</Button> : '—'
        )},
      ]}
    />
  );
}
