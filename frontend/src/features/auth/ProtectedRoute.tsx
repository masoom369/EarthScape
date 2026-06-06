import { Navigate, Outlet } from 'react-router-dom';
import { Spinner } from '../../components/Spinner';
import { useAuth } from '../../hooks/useAuth';
import type { Role } from '../../types/auth';

export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Spinner /></div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
