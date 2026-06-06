import { useState } from 'react';
import type { FormEvent } from 'react';
import api from '../../services/api';
import { Button } from '../../components/Button';
import { theme } from '../../styles/theme';

export function MapReduceJobForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [jobName, setJobName] = useState('temperature_agg_job');
  const [jobType, setJobType] = useState('temperature_agg');
  const [hdfsPath, setHdfsPath] = useState('/earthscape/raw/weather_station/');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/jobs/mapreduce', { job_name: jobName, job_type: jobType, hdfs_input_path: hdfsPath });
      onSubmitted();
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.md, maxWidth: 500 }}>
      <input value={jobName} onChange={(e) => setJobName(e.target.value)} placeholder="Job name" required
        style={{ padding: theme.spacing.sm }} />
      <select value={jobType} onChange={(e) => setJobType(e.target.value)} style={{ padding: theme.spacing.sm }}>
        <option value="temperature_agg">Temperature Aggregation</option>
        <option value="precipitation_totals">Precipitation Totals</option>
        <option value="anomaly_scores">Anomaly Scoring</option>
      </select>
      <input value={hdfsPath} onChange={(e) => setHdfsPath(e.target.value)} placeholder="HDFS input path" required
        style={{ padding: theme.spacing.sm }} />
      <Button type="submit" disabled={loading}>{loading ? 'Submitting...' : 'Trigger MapReduce Job'}</Button>
    </form>
  );
}
