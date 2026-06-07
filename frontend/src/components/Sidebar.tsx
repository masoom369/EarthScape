import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Upload, Cpu, Database, Bell,
  Users, HelpCircle, MessageSquare, X, Globe,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useAlertStore } from "@/stores/alertStore";

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
  roles?: string[];
  badge?: number;
}

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const { user, can } = useAuth();
  const unacknowledged = useAlertStore((s) => s.unacknowledged);

  const nav: NavItem[] = [
    { label: "Dashboard", to: "/dashboard", icon: <LayoutDashboard size={18} /> },
    {
      label: "Ingest Data",
      to: "/ingest",
      icon: <Upload size={18} />,
      roles: ["admin", "analyst"],
    },
    {
      label: "Jobs",
      to: "/jobs",
      icon: <Cpu size={18} />,
      roles: ["admin", "analyst"],
    },
    { label: "Climate Data", to: "/climate", icon: <Database size={18} /> },
    {
      label: "Alerts",
      to: "/alerts",
      icon: <Bell size={18} />,
      roles: ["admin"],
      badge: unacknowledged.length || undefined,
    },
    { label: "Users", to: "/users", icon: <Users size={18} />, roles: ["admin"] },
    { label: "Support", to: "/support", icon: <MessageSquare size={18} /> },
    { label: "Help", to: "/help", icon: <HelpCircle size={18} /> },
  ];

  const visible = nav.filter((n) => !n.roles || can(...n.roles));

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex flex-col w-60 transition-transform duration-300 lg:relative lg:translate-x-0 lg:z-auto",
        open ? "translate-x-0" : "-translate-x-full"
      )}
      style={{
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-lg)",
      }}
    >
      {/* Logo */}
      <div
        className="flex items-center justify-between px-5 py-5 shrink-0"
        style={{ borderBottom: "1px solid var(--border-subtle)" }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: "var(--brand-500)" }}
          >
            <Globe size={15} color="white" />
          </div>
          <div>
            <span
              className="text-sm font-bold tracking-tight block leading-none"
              style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
            >
              EarthScape
            </span>
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Climate Agency
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden p-1 rounded"
          style={{ color: "var(--text-tertiary)" }}
        >
          <X size={18} />
        </button>
      </div>

      {/* User pill */}
      {user && (
        <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
          <div
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg"
            style={{ background: "var(--bg-elevated)" }}
          >
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
              style={{ background: "var(--brand-500)", color: "white" }}
            >
              {user.email[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p
                className="text-xs font-medium truncate"
                style={{ color: "var(--text-primary)" }}
              >
                {user.email}
              </p>
              <p className="text-xs capitalize" style={{ color: "var(--text-tertiary)" }}>
                {user.role}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-0.5">
        {visible.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group relative",
                isActive
                  ? "text-white"
                  : "hover:bg-[var(--bg-elevated)]"
              )
            }
            style={({ isActive }) =>
              isActive
                ? { background: "var(--brand-600)", color: "white" }
                : { color: "var(--text-secondary)" }
            }
          >
            {item.icon}
            <span className="flex-1">{item.label}</span>
            {item.badge != null && item.badge > 0 && (
              <span
                className="text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[1.25rem] text-center"
                style={{ background: "var(--danger)", color: "white" }}
              >
                {item.badge > 99 ? "99+" : item.badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-3 text-xs" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--border-subtle)" }}>
        EarthScape v1.0 · Big Data Platform
      </div>
    </aside>
  );
}