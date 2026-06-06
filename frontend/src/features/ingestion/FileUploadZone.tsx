import { useCallback, useState } from 'react';
import api from '../../services/api';
import { Button } from '../../components/Button';
import { theme } from '../../styles/theme';

interface FileUploadZoneProps {
  onUploaded: () => void;
}

export function FileUploadZone({ onUploaded }: FileUploadZoneProps) {
  const [file, setFile] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState('weather_station');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    const form = new FormData();
    form.append('file', file);
    form.append('source_type', sourceType);
    try {
      await api.post('/ingest/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      setFile(null);
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        style={{
          border: `2px dashed ${theme.colors.border}`, borderRadius: theme.radius.lg,
          padding: theme.spacing.xxl, textAlign: 'center', marginBottom: theme.spacing.md,
        }}
      >
        <p>Drag & drop a CSV, JSON, or GeoJSON file here</p>
        <input type="file" accept=".csv,.json,.geojson" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        {file && <p style={{ marginTop: theme.spacing.sm }}>Selected: {file.name}</p>}
      </div>
      <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}
        style={{ padding: theme.spacing.sm, marginRight: theme.spacing.md }}>
        <option value="weather_station">Weather Station (CSV)</option>
        <option value="sensor">Sensor (JSON)</option>
        <option value="satellite">Satellite (JSON)</option>
      </select>
      <Button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </Button>
      {error && <p style={{ color: theme.colors.danger, marginTop: theme.spacing.sm }}>{error}</p>}
    </div>
  );
}
