interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      {icon && (
        <span
          className="w-12 h-12 rounded-2xl flex items-center justify-center mb-1"
          style={{ background: "var(--bg-elevated)", color: "var(--text-tertiary)" }}
        >
          {icon}
        </span>
      )}
      <p className="font-semibold text-base" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
        {title}
      </p>
      {description && (
        <p className="text-sm max-w-xs" style={{ color: "var(--text-tertiary)" }}>
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}