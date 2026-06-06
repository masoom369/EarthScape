import { useCallback, useState } from 'react';
import api from '../../services/api';
import { theme } from '../../styles/theme';
import { usePoll } from '../../hooks/usePoll';
import type { ClimateRecord } from '../../types/climate';
import { Badge } from '../../components/Badge';

const POLL_MS = Number(import.meta.env.VITE_POLL_REALTIME_MS);

export function RealtimeFeedPanel() {
  const [records, setRecords] = useState<ClimateRecord[]>([]);

  const fetchRealtime = useCallback(async () => {
    const { data } = await api.get('/climate/realtime', { params: { n: 20 } });
    setRecords(data.items);
  }, []);

  usePoll(fetchRealtime, POLL_MS);

  return (
    <div style={{ background: theme.colors.surface, padding: theme.spacing.lg, borderRadius: theme.radius.lg }}>
      <h3>Real-time Sensor Feed</h3>
      <div style={{ maxHeight: 300, overflowY: 'auto' }}>
        {records.map((r) => (
          <div key={r.id} style={{
            padding: theme.spacing.sm, borderBottom: `1px solid ${theme.colors.border}`,
            display: 'flex', justifyContent: 'space-between', fontSize: theme.fontSize.sm,
          }}>
            <span>{r.location.region} — {r.temperature_c}°C</span>
            <span style={{ color: theme.colors.textMuted }}>{new Date(r.timestamp).toLocaleTimeString()}</span>
            {r.is_anomaly && <Badge status="high">Anomaly</Badge>}
          </div>
        ))}
        {records.length === 0 && <p style={{ color: theme.colors.textMuted }}>No sensor data yet.</p>}
      </div>
    </div>
  );
}
