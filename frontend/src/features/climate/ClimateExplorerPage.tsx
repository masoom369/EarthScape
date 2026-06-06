import { useCallback, useEffect, useState } from 'react';
import api from '../../services/api';
import { FilterBar, type FilterValues } from '../../components/FilterBar';
import { Pagination } from '../../components/Pagination';
import { useAuth } from '../../hooks/useAuth';
import { theme } from '../../styles/theme';
import type { ClimateRecord } from '../../types/climate';
import { ClimateTable } from './ClimateTable';
import { ExportButton } from './ExportButton';

export function ClimateExplorerPage() {
  const [filters, setFilters] = useState<FilterValues>({});
  const [records, setRecords] = useState<ClimateRecord[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const { isAnalyst } = useAuth();
  const limit = 50;

  const fetchData = useCallback(async () => {
    const params: Record<string, string | number | boolean> = { page, limit };
    if (filters.region) params.region = filters.region;
    if (filters.source_type) params.source_type = filters.source_type;
    if (filters.from_date) params.from_date = filters.from_date;
    if (filters.to_date) params.to_date = filters.to_date;
    if (filters.is_anomaly) params.is_anomaly = filters.is_anomaly === 'true';
    const { data } = await api.get('/climate', { params });
    setRecords(data.items);
    setTotal(data.total);
  }, [page, filters]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ color: theme.colors.primary }}>Climate Explorer</h1>
        {isAnalyst && <ExportButton filters={filters} />}
      </div>
      <FilterBar values={filters} onChange={(f) => { setFilters(f); setPage(1); }} />
      <ClimateTable records={records} />
      <Pagination page={page} total={total} limit={limit} onChange={setPage} />
    </div>
  );
}
