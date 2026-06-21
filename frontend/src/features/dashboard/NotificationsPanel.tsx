import { useAlertStore } from "@/stores/alertStore";
import api from "@/lib/api";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { Bell, CheckCheck } from "lucide-react";
import { formatDateTime } from "@/lib/utils";
import { toast } from "sonner";

const SEVERITY_VARIANT: Record<string, "danger" | "warning" | "info"> = {
  high: "danger",
  medium: "warning",
  low: "info",
};

export default function NotificationsPanel() {
  const events = useAlertStore((s) => s.unacknowledged);
  const acknowledge = useAlertStore((s) => s.acknowledge);

  async function ack(id: string) {
    try {
      await api.patch(`/alerts/events/${id}/acknowledge`);
      acknowledge(id);
    } catch {
      toast.error("Failed to acknowledge");
    }
  }

  if (!events.length) {
    return (
      <EmptyState
        icon={<Bell size={20} />}
        title="No active alerts"
        description="All clear — no unacknowledged events"
      />
    );
  }

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {events.slice(0, 20).map((e) => (
        <div
          key={e.id}
          className="flex items-start gap-3 px-3 py-2.5 rounded-lg"
          style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
        >
          <Badge variant={SEVERITY_VARIANT[e.severity] ?? "neutral"} className="shrink-0 mt-0.5">
            {e.severity}
          </Badge>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>
              {(e.notification_log as Record<string, string> | null)?.rule_name ?? "Alert"}
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
              Value: {e.triggered_value} · {formatDateTime(e.triggered_at)}
            </p>
          </div>
          <Button
            variant="success-soft"
            size="sm"
            icon={<CheckCheck size={13} />}
            onClick={() => ack(e.id)}
            className="shrink-0"
          >
            Ack
          </Button>
        </div>
      ))}
    </div>
  );
}