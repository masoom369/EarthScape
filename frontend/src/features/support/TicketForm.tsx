import { useState } from 'react';
import type { FormEvent } from 'react';
import api from '../../services/api';
import { Button } from '../../components/Button';
import { theme } from '../../styles/theme';

export function TicketForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [screenshotUrl, setScreenshotUrl] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await api.post('/support/tickets', {
      subject, description,
      screenshot_url: screenshotUrl || undefined,
    });
    setSubject('');
    setDescription('');
    setScreenshotUrl('');
    onSubmitted();
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.md, maxWidth: 600, marginBottom: theme.spacing.xl }}>
      <input placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} required style={{ padding: theme.spacing.sm }} />
      <textarea placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} required rows={4} style={{ padding: theme.spacing.sm }} />
      <input placeholder="Screenshot URL (optional)" value={screenshotUrl} onChange={(e) => setScreenshotUrl(e.target.value)} style={{ padding: theme.spacing.sm }} />
      <Button type="submit">Submit Ticket</Button>
    </form>
  );
}
