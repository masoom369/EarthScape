import { useCallback, useState } from 'react';
import api from '../services/api';
import { usePoll } from './usePoll';
import type { ClimateRecord, ClimateSummaryItem } from '../types/climate';

const POLL_MS = Number(import.meta.env.VITE_POLL_REALTIME_MS);

interface DashboardData {
  summary: ClimateSummaryItem[];
  records: ClimateRecord[];
  forecast: Array<{ region: string; date: string; forecast_temp_c: number }>;
  correlation: Record<string, Record<string, number | null>> | null;
  anomalies: ClimateRecord[];
}

export function useDashboardData(region?: string, fromDate?: string, toDate?: string) {
  const [data, setData] = useState<DashboardData>({
    summary: [], records: [], forecast: [], correlation: null, anomalies: [],
  });
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const params = { region, from_date: fromDate, to_date: toDate };
      const [summaryRes, climateRes, anomalyRes] = await Promise.all([
        api.get('/climate/summary', { params }),
        api.get('/climate', { params: { ...params, limit: 200 } }),
        api.get('/climate', { params: { ...params, is_anomaly: true, limit: 100 } }),
      ]);

      let forecast: DashboardData['forecast'] = [];
      let correlation: DashboardData['correlation'] = null;

      setData({
        summary: summaryRes.data.items,
        records: climateRes.data.items,
        forecast,
        correlation,
        anomalies: anomalyRes.data.items,
      });
    } finally {
      setLoading(false);
    }
  }, [region, fromDate, toDate]);

  usePoll(fetchData, POLL_MS);

  return { ...data, loading, refresh: fetchData };
}
