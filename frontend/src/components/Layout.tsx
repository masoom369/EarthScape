import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { theme } from '../styles/theme';
import { Button } from './Button';

const navLinkStyle = ({ isActive }: { isActive: boolean }) => ({
  display: 'block',
  padding: `${theme.spacing.sm} ${theme.spacing.md}`,
  color: isActive ? theme.colors.primary : theme.colors.text,
  textDecoration: 'none',
  fontWeight: isActive ? 600 : 400,
  borderLeft: isActive ? `3px solid ${theme.colors.primary}` : '3px solid transparent',
});

export function Layout() {
  const { user, logout, isAdmin, isAnalyst } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', minWidth: 1280, background: theme.colors.background }}>
      <aside style={{
        width: 240, background: theme.colors.surface,
        borderRight: `1px solid ${theme.colors.border}`, padding: theme.spacing.lg,
      }}>
        <h2 style={{ color: theme.colors.primary, fontSize: theme.fontSize.lg, margin: `0 0 ${theme.spacing.xl}` }}>
          EarthScape
        </h2>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.xs }}>
          <NavLink to="/dashboard" style={navLinkStyle}>Dashboard</NavLink>
          {isAnalyst && <NavLink to="/ingest" style={navLinkStyle}>Ingestion</NavLink>}
          {isAnalyst && <NavLink to="/jobs" style={navLinkStyle}>Jobs</NavLink>}
          <NavLink to="/climate" style={navLinkStyle}>Climate Explorer</NavLink>
          {isAdmin && <NavLink to="/alerts" style={navLinkStyle}>Alerts</NavLink>}
          {isAdmin && <NavLink to="/users" style={navLinkStyle}>Users</NavLink>}
          <NavLink to="/support" style={navLinkStyle}>Support</NavLink>
          <NavLink to="/help" style={navLinkStyle}>Help</NavLink>
        </nav>
        <div style={{ marginTop: theme.spacing.xxl, fontSize: theme.fontSize.sm, color: theme.colors.textMuted }}>
          {user?.email}<br />{user?.role}
          <div style={{ marginTop: theme.spacing.sm }}>
            <Button variant="secondary" onClick={() => logout()}>Logout</Button>
          </div>
        </div>
      </aside>
      <main style={{ flex: 1, padding: theme.spacing.xl, overflow: 'auto' }}>
        <Outlet />
      </main>
    </div>
  );
}
