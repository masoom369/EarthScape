import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { useAlertPoll } from "@/hooks/useAlertPoll";
import { useAuth } from "@/hooks/useAuth";

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();
  useAlertPoll(!!user);

  return (
    <div className="flex h-dvh overflow-hidden" style={{ background: "var(--bg-base)" }}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 lg:hidden"
          style={{ background: "var(--bg-overlay)" }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex flex-col flex-1 min-w-0">
        <Topbar onMenuClick={() => setSidebarOpen(true)} />
        <main
          className="flex-1 overflow-y-auto p-4 md:p-6"
          style={{ background: "var(--bg-base)" }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}