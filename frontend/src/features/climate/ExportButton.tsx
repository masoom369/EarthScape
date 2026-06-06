import api from '../../services/api';
import { Button } from '../../components/Button';
import type { FilterValues } from '../../components/FilterBar';

export function ExportButton({ filters }: { filters: FilterValues }) {
  const handleExport = async () => {
    const params: Record<string, string> = {};
    if (filters.region) params.region = filters.region;
    if (filters.source_type) params.source_type = filters.source_type;
    if (filters.from_date) params.from_date = filters.from_date;
    if (filters.to_date) params.to_date = filters.to_date;
    if (filters.is_anomaly) params.is_anomaly = filters.is_anomaly;

    const response = await api.get('/climate/export', { params, responseType: 'blob' });
    const url = URL.createObjectURL(new Blob([response.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'climate_export.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return <Button onClick={handleExport}>Export CSV</Button>;
}
