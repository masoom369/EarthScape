import { theme } from '../styles/theme';

export function Spinner() {
  return (
    <div style={{
      width: 32, height: 32,
      border: `3px solid ${theme.colors.border}`,
      borderTopColor: theme.colors.primary,
      borderRadius: '50%',
      animation: 'spin 0.8s linear infinite',
    }} />
  );
}
