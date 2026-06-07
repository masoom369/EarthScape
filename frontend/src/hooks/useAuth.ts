import { useAuthStore } from "@/stores/authStore";

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const loading = useAuthStore((s) => s.loading);
  const logout = useAuthStore((s) => s.logout);

  return {
    user,
    loading,
    logout,
    isAdmin: user?.role === "admin",
    isAnalyst: user?.role === "analyst",
    can: (...roles: string[]) => !!user && roles.includes(user.role),
  };
}