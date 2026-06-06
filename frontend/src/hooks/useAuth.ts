import { useAuthStore } from '../stores/authStore';
import type { Role } from '../types/auth';

export function useAuth() {
  const { user, loading, login, logout } = useAuthStore();
  const hasRole = (...roles: Role[]) => user !== null && roles.includes(user.role);
  return { user, loading, login, logout, hasRole, isAdmin: user?.role === 'admin', isAnalyst: user?.role === 'analyst' || user?.role === 'admin' };
}
