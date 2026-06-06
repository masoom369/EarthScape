import { useState } from 'react';
import type { FormEvent } from 'react';
import api from '../../services/api';
import { Button } from '../../components/Button';
import { theme } from '../../styles/theme';

export function MLTrainForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [modelType, setModelType] = useState('anomaly_detection');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/jobs/ml/train', { model_type: modelType });
      onSubmitted();
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: theme.spacing.md, alignItems: 'center' }}>
      <select value={modelType} onChange={(e) => setModelType(e.target.value)} style={{ padding: theme.spacing.sm }}>
        <option value="anomaly_detection">Anomaly Detection (Isolation Forest)</option>
        <option value="trend_prediction">Trend Prediction (Linear Regression)</option>
        <option value="correlation">Correlation Analysis (Pearson)</option>
      </select>
      <Button type="submit" disabled={loading}>{loading ? 'Training...' : 'Train Model'}</Button>
    </form>
  );
}
