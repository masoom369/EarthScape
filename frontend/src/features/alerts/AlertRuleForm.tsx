import { useState } from 'react';
import type { FormEvent } from 'react';
import api from '../../services/api';
import { Button } from '../../components/Button';
import { theme } from '../../styles/theme';

export function AlertRuleForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState('');
  const [metric, setMetric] = useState('temperature_c');
  const [operator, setOperator] = useState('>');
  const [threshold, setThreshold] = useState(35);
  const [severity, setSeverity] = useState('medium');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await api.post('/alerts/rules', { name, metric, operator, threshold, severity });
    setName('');
    onCreated();
  };

  const inputStyle = { padding: theme.spacing.sm, marginRight: theme.spacing.sm };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexWrap: 'wrap', gap: theme.spacing.sm, marginBottom: theme.spacing.lg }}>
      <input style={inputStyle} placeholder="Rule name" value={name} onChange={(e) => setName(e.target.value)} required />
      <select style={inputStyle} value={metric} onChange={(e) => setMetric(e.target.value)}>
        <option value="temperature_c">Temperature</option>
        <option value="precipitation_mm">Precipitation</option>
        <option value="co2_ppm">CO₂</option>
        <option value="humidity_pct">Humidity</option>
      </select>
      <select style={inputStyle} value={operator} onChange={(e) => setOperator(e.target.value)}>
        <option value=">">&gt;</option><option value="<">&lt;</option>
        <option value="=">=</option><option value=">=">&gt;=</option><option value="<=">&lt;=</option>
      </select>
      <input style={inputStyle} type="number" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
      <select style={inputStyle} value={severity} onChange={(e) => setSeverity(e.target.value)}>
        <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
      </select>
      <Button type="submit">Create Rule</Button>
    </form>
  );
}
