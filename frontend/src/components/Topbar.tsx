import { Menu, Sun, Moon, LogOut, Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useThemeStore } from "@/stores/themeStore";
import { useAuthStore } from "@/stores/authStore";
import { useAlertStore } from "@/stores/alertStore";
import { toast } from "sonner";

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const theme = useThemeStore((s) => s.theme);
  const toggle = useThemeStore((s) => s.toggle);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const unacknowledged = useAlertStore((s) => s.unacknowledged);

  async function handleLogout() {
    await logout();
    navigate("/login");
    toast.success("Logged out successfully");
  }

  return (
    <header
      className="flex items-center gap-3 px-4 md:px-6 h-14 shrink-0"
      style={{
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-subtle)",
        boxShadow: "var(--shadow-sm)",
      }}
    >
      <button
        onClick={onMenuClick}
        className="lg:hidden p-2 rounded-lg transition-colors"
        style={{ color: "var(--text-secondary)" }}
      >
        <Menu size={20} />
      </button>

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        {/* Alert indicator */}
        {unacknowledged.length > 0 && (
          <button
            onClick={() => navigate("/alerts")}
            className="relative p-2 rounded-lg transition-colors"
            style={{ color: "var(--text-secondary)" }}
            title="Unacknowledged alerts"
          >
            <Bell size={18} />
            <span
              className="absolute top-1 right-1 w-2 h-2 rounded-full pulse-dot"
              style={{ background: "var(--danger)" }}
            />
          </button>
        )}

        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="p-2 rounded-lg transition-all duration-200"
          style={{
            background: "var(--bg-elevated)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-subtle)",
          }}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="p-2 rounded-lg transition-all duration-200"
          style={{
            background: "var(--bg-elevated)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-subtle)",
          }}
          title="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}