import type { ReactNode } from 'react';
import { theme } from '../styles/theme';

const statusColors: Record<string, string> = {
  open: theme.colors.warning,
  'in-progress': theme.colors.secondary,
  resolved: theme.colors.success,
  completed: theme.colors.success,
  failed: theme.colors.danger,
  running: theme.colors.secondary,
  queued: theme.colors.textMuted,
  pending: theme.colors.warning,
  success: theme.colors.success,
  low: theme.colors.success,
  medium: theme.colors.warning,
  high: theme.colors.danger,
};

export function Badge({ status, children }: { status: string; children?: ReactNode }) {
  return (
    <span style={{
      background: statusColors[status] || theme.colors.textMuted,
      color: '#fff',
      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
      borderRadius: theme.radius.full,
      fontSize: theme.fontSize.xs,
      fontWeight: 600,
    }}>
      {children || status}
    </span>
  );
}
