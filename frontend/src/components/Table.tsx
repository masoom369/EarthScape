import type { ReactNode } from 'react';
import { theme } from '../styles/theme';

interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

export function Table<T extends { id: string }>({ columns, data }: { columns: Column<T>[]; data: T[] }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: theme.fontSize.sm }}>
        <thead>
          <tr style={{ background: theme.colors.background, textAlign: 'left' }}>
            {columns.map((c) => (
              <th key={c.key} style={{ padding: theme.spacing.sm, borderBottom: `2px solid ${theme.colors.border}` }}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
              {columns.map((c) => (
                <td key={c.key} style={{ padding: theme.spacing.sm }}>{c.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
