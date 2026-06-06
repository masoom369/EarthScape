import { useCallback, useEffect, useState } from 'react';
import api from '../../services/api';
import { theme } from '../../styles/theme';
import { CreateUserForm } from './CreateUserForm';
import { UserTable } from './UserTable';

export function UsersPage() {
  const [users, setUsers] = useState<Array<{ id: string; email: string; role: string; is_active: boolean }>>([]);

  const fetchUsers = useCallback(async () => {
    const { data } = await api.get('/users', { params: { limit: 100 } });
    setUsers(data.items);
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  return (
    <div>
      <h1 style={{ color: theme.colors.primary }}>User Management</h1>
      <CreateUserForm onCreated={fetchUsers} />
      <UserTable users={users} onChanged={fetchUsers} />
    </div>
  );
}
