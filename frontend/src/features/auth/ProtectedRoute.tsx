import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import Spinner from "@/components/ui/Spinner";

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: string[];
}

export default function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-dvh items-center justify-center" style={{ background: "var(--bg-base)" }}>
        <Spinner size={32} />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}