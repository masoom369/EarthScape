import { useState } from 'react';
import type { FormEvent } from 'react';
import api from '../../services/api';
import { Button } from '../../components/Button';
import { theme } from '../../styles/theme';

export function CreateUserForm({ onCreated }: { onCreated: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('viewer');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await api.post('/users', { email, password, role });
    setEmail('');
    setPassword('');
    onCreated();
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: theme.spacing.sm, marginBottom: theme.spacing.lg, flexWrap: 'wrap' }}>
      <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ padding: theme.spacing.sm }} />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ padding: theme.spacing.sm }} />
      <select value={role} onChange={(e) => setRole(e.target.value)} style={{ padding: theme.spacing.sm }}>
        <option value="admin">Admin</option>
        <option value="analyst">Analyst</option>
        <option value="viewer">Viewer</option>
      </select>
      <Button type="submit">Create User</Button>
    </form>
  );
}
