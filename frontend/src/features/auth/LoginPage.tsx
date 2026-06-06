import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/Button';
import { useAuth } from '../../hooks/useAuth';
import { theme } from '../../styles/theme';

export function LoginPage() {
  const [email, setEmail] = useState('admin@earthscape.com');
  const [password, setPassword] = useState('Admin123!');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `linear-gradient(135deg, ${theme.colors.primary} 0%, ${theme.colors.secondary} 100%)`,
    }}>
      <form onSubmit={handleSubmit} style={{
        background: theme.colors.surface, padding: theme.spacing.xxl,
        borderRadius: theme.radius.lg, width: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
      }}>
        <h1 style={{ color: theme.colors.primary, marginTop: 0 }}>EarthScape</h1>
        <p style={{ color: theme.colors.textMuted, marginBottom: theme.spacing.xl }}>Climate Analytics Platform</p>
        {error && <p style={{ color: theme.colors.danger }}>{error}</p>}
        <label style={{ display: 'block', marginBottom: theme.spacing.md }}>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
            style={{ display: 'block', width: '100%', padding: theme.spacing.sm, marginTop: theme.spacing.xs, boxSizing: 'border-box' }} />
        </label>
        <label style={{ display: 'block', marginBottom: theme.spacing.lg }}>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
            style={{ display: 'block', width: '100%', padding: theme.spacing.sm, marginTop: theme.spacing.xs, boxSizing: 'border-box' }} />
        </label>
        <Button type="submit" style={{ width: '100%' }}>Sign In</Button>
      </form>
    </div>
  );
}
