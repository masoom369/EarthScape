import { useEffect, useState, useCallback } from "react";
import { Thermometer, CloudRain, Activity, Bell } from "lucide-react";
import api from "@/lib/api";
import { usePoll } from "@/hooks/usePoll";
import PageHeader from "@/components/ui/PageHeader";
import StatCard from "@/components/ui/StatCard";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import TemperatureTrendChart from "./TemperatureTrendChart";
import PrecipitationChart from "./PrecipitationChart";
import AnomalyScatterPlot from "./AnomalyScatterPlot";
import CorrelationHeatmap from "./CorrelationHeatmap";
import RealtimeFeedPanel from "./RealtimeFeedPanel";
import NotificationsPanel from "./NotificationsPanel";
import type { ClimateSummaryResponse } from "@/types/climate";
import type { MLResult } from "@/types/ml";
import { formatNumber } from "@/lib/utils";

const REALTIME_MS = Number(import.meta.env.VITE_POLL_REALTIME_MS ?? 10000);

export default function DashboardPage() {
  const [summary, setSummary] = useState<ClimateSummaryResponse | null>(null);
  const [mlAnomaly, setMlAnomaly] = useState<MLResult | null>(null);
  const [mlTrend, setMlTrend] = useState<MLResult | null>(null);
  const [mlCorr, setMlCorr] = useState<MLResult | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [sumRes, anomRes, trendRes, corrRes] = await Promise.allSettled([
        api.get<ClimateSummaryResponse>("/climate/summary"),
        api.get<MLResult>("/jobs/ml/train/latest?model_type=anomaly_detection").catch(() => null),
        api.get<MLResult>("/jobs/ml/train/latest?model_type=trend_prediction").catch(() => null),
        api.get<MLResult>("/jobs/ml/train/latest?model_type=correlation").catch(() => null),
      ]);
      if (sumRes.status === "fulfilled") setSummary(sumRes.value.data);
      if (anomRes.status === "fulfilled" && anomRes.value) setMlAnomaly(anomRes.value.data);
      if (trendRes.status === "fulfilled" && trendRes.value) setMlTrend(trendRes.value.data);
      if (corrRes.status === "fulfilled" && corrRes.value) setMlCorr(corrRes.value.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const totalRecords = summary?.items.reduce((a, b) => a + b.record_count, 0) ?? 0;
  const totalAnomalies = summary?.items.reduce((a, b) => a + b.anomaly_count, 0) ?? 0;
  const avgTemp = summary?.items.length
    ? summary.items.reduce((a, b) => a + (b.avg_temperature_c ?? 0), 0) / summary.items.length
    : null;
  const totalPrecip = summary?.items.reduce((a, b) => a + (b.total_precipitation_mm ?? 0), 0) ?? 0;

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Dashboard"
        description="Live climate analytics and monitoring overview"
      />

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <StatCard
          label="Total Records"
          value={totalRecords.toLocaleString()}
          icon={<Activity size={16} />}
          accent="var(--brand-600)"
          className="animate-fade-up animate-fade-up-delay-1"
        />
        <StatCard
          label="Avg Temperature"
          value={avgTemp != null ? `${formatNumber(avgTemp, 1)}°C` : "—"}
          icon={<Thermometer size={16} />}
          accent="var(--warning)"
          className="animate-fade-up animate-fade-up-delay-2"
        />
        <StatCard
          label="Total Precipitation"
          value={`${formatNumber(totalPrecip / 1000, 1)}k mm`}
          icon={<CloudRain size={16} />}
          accent="var(--info)"
          className="animate-fade-up animate-fade-up-delay-3"
        />
        <StatCard
          label="Anomalies Detected"
          value={totalAnomalies.toLocaleString()}
          icon={<Bell size={16} />}
          accent="var(--danger)"
          className="animate-fade-up animate-fade-up-delay-4"
        />
      </div>

      {/* Main charts grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Temperature Trend</CardTitle>
          </CardHeader>
          <TemperatureTrendChart summary={summary} forecast={mlTrend?.forecast_data ?? null} loading={loading} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Monthly Precipitation</CardTitle>
          </CardHeader>
          <PrecipitationChart summary={summary} loading={loading} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Anomaly Distribution</CardTitle>
          </CardHeader>
          <AnomalyScatterPlot mlResult={mlAnomaly} loading={loading} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Correlation Heatmap</CardTitle>
          </CardHeader>
          <CorrelationHeatmap mlResult={mlCorr} loading={loading} />
        </Card>
      </div>

      {/* Bottom panels */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Live Feed</CardTitle>
            <span className="flex items-center gap-1.5 text-xs" style={{ color: "var(--success)" }}>
              <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: "var(--success)" }} />
              Live
            </span>
          </CardHeader>
          <RealtimeFeedPanel pollMs={REALTIME_MS} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
          </CardHeader>
          <NotificationsPanel />
        </Card>
      </div>
    </div>
  );
}