import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useThemeStore } from "@/stores/themeStore";
import { useAuthStore } from "@/stores/authStore";
import ProtectedRoute from "@/features/auth/ProtectedRoute";
import AppShell from "@/components/AppShell";
import LoginPage from "@/features/auth/LoginPage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import IngestionPage from "@/features/ingestion/IngestionPage";
import JobsPage from "@/features/jobs/JobsPage";
import ClimateExplorerPage from "@/features/climate/ClimateExplorerPage";
import AlertsPage from "@/features/alerts/AlertsPage";
import UsersPage from "@/features/users/UsersPage";
import SupportPage from "@/features/support/SupportPage";
import HelpPage from "@/features/help/HelpPage";

export default function App() {
  const theme = useThemeStore((s) => s.theme);
  const initAuth = useAuthStore((s) => s.init);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route
          path="ingest"
          element={
            <ProtectedRoute roles={["admin", "analyst"]}>
              <IngestionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="jobs"
          element={
            <ProtectedRoute roles={["admin", "analyst"]}>
              <JobsPage />
            </ProtectedRoute>
          }
        />
        <Route path="climate" element={<ClimateExplorerPage />} />
        <Route
          path="alerts"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AlertsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="users"
          element={
            <ProtectedRoute roles={["admin"]}>
              <UsersPage />
            </ProtectedRoute>
          }
        />
        <Route path="support" element={<SupportPage />} />
        <Route path="help" element={<HelpPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
