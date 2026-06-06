import { useState } from 'react';
import { FilterBar, type FilterValues } from '../../components/FilterBar';
import { Spinner } from '../../components/Spinner';
import { useDashboardData } from '../../hooks/useDashboardData';
import { theme } from '../../styles/theme';
import { AnomalyScatterPlot } from './AnomalyScatterPlot';
import { CorrelationHeatmap } from './CorrelationHeatmap';
import { NotificationsPanel } from './NotificationsPanel';
import { PrecipitationChart } from './PrecipitationChart';
import { RealtimeFeedPanel } from './RealtimeFeedPanel';
import { TemperatureTrendChart } from './TemperatureTrendChart';

export function DashboardPage() {
  const [filters, setFilters] = useState<FilterValues>({});
  const { summary, anomalies, forecast, correlation, loading } = useDashboardData(
    filters.region, filters.from_date, filters.to_date,
  );

  if (loading) return <Spinner />;

  return (
    <div>
      <h1 style={{ color: theme.colors.primary }}>Climate Dashboard</h1>
      <FilterBar values={filters} onChange={setFilters} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.lg }}>
        <TemperatureTrendChart data={summary} forecast={forecast} />
        <PrecipitationChart data={summary} />
        <AnomalyScatterPlot data={anomalies} />
        <CorrelationHeatmap matrix={correlation} />
        <RealtimeFeedPanel />
        <NotificationsPanel />
      </div>
    </div>
  );
}
