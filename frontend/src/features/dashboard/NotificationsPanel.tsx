import { useAlertStore } from '../../stores/alertStore';
import { usePoll } from '../../hooks/usePoll';
import { theme } from '../../styles/theme';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';

const POLL_MS = Number(import.meta.env.VITE_POLL_ALERTS_MS);

export function NotificationsPanel() {
  const { events, fetchEvents, acknowledge } = useAlertStore();
  usePoll(fetchEvents, POLL_MS);

  return (
    <div style={{ background: theme.colors.surface, padding: theme.spacing.lg, borderRadius: theme.radius.lg }}>
      <h3>Alert Notifications</h3>
      {events.length === 0 && <p style={{ color: theme.colors.textMuted }}>No unacknowledged alerts.</p>}
      {events.map((e) => (
        <div key={e.id} style={{
          padding: theme.spacing.sm, borderBottom: `1px solid ${theme.colors.border}`,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div>
            <Badge status={e.severity}>{e.severity}</Badge>
            <span style={{ marginLeft: theme.spacing.sm, fontSize: theme.fontSize.sm }}>
              Value: {e.triggered_value} — {new Date(e.triggered_at).toLocaleString()}
            </span>
          </div>
          <Button variant="secondary" onClick={() => acknowledge(e.id)}>Acknowledge</Button>
        </div>
      ))}
    </div>
  );
}
