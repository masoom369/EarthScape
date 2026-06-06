import { useCallback, useEffect, useState } from 'react';
import api from '../../services/api';
import { theme } from '../../styles/theme';
import { FileUploadZone } from './FileUploadZone';
import { IngestionLogTable } from './IngestionLogTable';

export function IngestionPage() {
  const [logs, setLogs] = useState<Array<{ id: string; filename: string; status: string; record_count: number; hdfs_path?: string; created_at: string }>>([]);

  const fetchLogs = useCallback(async () => {
    const { data } = await api.get('/ingest/logs', { params: { limit: 50 } });
    setLogs(data.items);
  }, []);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  return (
    <div>
      <h1 style={{ color: theme.colors.primary }}>Data Ingestion</h1>
      <FileUploadZone onUploaded={fetchLogs} />
      <h2 style={{ marginTop: theme.spacing.xl }}>Ingestion Logs</h2>
      <IngestionLogTable logs={logs} />
    </div>
  );
}
