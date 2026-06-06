import { theme } from '../styles/theme';
import { Button } from './Button';

export function Pagination({ page, total, limit, onChange }: {
  page: number; total: number; limit: number; onChange: (p: number) => void;
}) {
  const pages = Math.ceil(total / limit) || 1;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.md, marginTop: theme.spacing.md }}>
      <Button disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</Button>
      <span style={{ fontSize: theme.fontSize.sm }}>Page {page} of {pages} ({total} records)</span>
      <Button disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</Button>
    </div>
  );
}
