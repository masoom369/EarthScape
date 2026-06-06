import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { theme } from '../styles/theme';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  children: ReactNode;
}

export function Button({ variant = 'primary', children, style, ...props }: ButtonProps) {
  const bg = variant === 'primary' ? theme.colors.primary
    : variant === 'danger' ? theme.colors.danger
    : theme.colors.secondary;
  return (
    <button
      style={{
        background: bg,
        color: '#fff',
        border: 'none',
        borderRadius: theme.radius.md,
        padding: `${theme.spacing.sm} ${theme.spacing.md}`,
        fontSize: theme.fontSize.sm,
        cursor: props.disabled ? 'not-allowed' : 'pointer',
        opacity: props.disabled ? 0.6 : 1,
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  );
}
