import { useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { LoginPage } from './features/auth/LoginPage';
import { ProtectedRoute } from './features/auth/ProtectedRoute';
import { AlertsPage } from './features/alerts/AlertsPage';
import { ClimateExplorerPage } from './features/climate/ClimateExplorerPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { HelpPage } from './features/help/HelpPage';
import { IngestionPage } from './features/ingestion/IngestionPage';
import { JobsPage } from './features/jobs/JobsPage';
import { SupportPage } from './features/support/SupportPage';
import { UsersPage } from './features/users/UsersPage';
import { useAuthStore } from './stores/authStore';

export default function App() {
  const fetchMe = useAuthStore((s) => s.fetchMe);

  useEffect(() => {
    if (import.meta.env.DEV) {
      const start = performance.now();
      window.addEventListener('load', () => {
        console.debug(`[Perf] Page load: ${(performance.now() - start).toFixed(0)}ms`);
      });
    }
    fetchMe();
  }, [fetchMe]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/climate" element={<ClimateExplorerPage />} />
            <Route path="/support" element={<SupportPage />} />
            <Route path="/help" element={<HelpPage />} />
            <Route element={<ProtectedRoute roles={['admin', 'analyst']} />}>
              <Route path="/ingest" element={<IngestionPage />} />
              <Route path="/jobs" element={<JobsPage />} />
            </Route>
            <Route element={<ProtectedRoute roles={['admin']} />}>
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/users" element={<UsersPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
