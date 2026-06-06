import { useCallback, useEffect, useState } from 'react';
import api from '../../services/api';
import { theme } from '../../styles/theme';
import type { AlertEvent, AlertRule } from '../../types/alert';
import { AlertEventLog } from './AlertEventLog';
import { AlertRuleForm } from './AlertRuleForm';
import { AlertRuleList } from './AlertRuleList';

export function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);

  const fetchAll = useCallback(async () => {
    const [rulesRes, eventsRes] = await Promise.all([
      api.get('/alerts/rules'),
      api.get('/alerts/events', { params: { limit: 50 } }),
    ]);
    setRules(rulesRes.data);
    setEvents(eventsRes.data.items);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const acknowledge = async (id: string) => {
    await api.patch(`/alerts/events/${id}/acknowledge`);
    fetchAll();
  };

  return (
    <div>
      <h1 style={{ color: theme.colors.primary }}>Alert Management</h1>
      <h2>Rules</h2>
      <AlertRuleForm onCreated={fetchAll} />
      <AlertRuleList rules={rules} onChanged={fetchAll} />
      <h2 style={{ marginTop: theme.spacing.xl }}>Event Log</h2>
      <AlertEventLog events={events} onAcknowledge={acknowledge} />
    </div>
  );
}
