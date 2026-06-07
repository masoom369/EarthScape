import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "neutral";

const styles: Record<BadgeVariant, React.CSSProperties> = {
  default: { background: "var(--brand-100)", color: "var(--brand-700)" },
  success: { background: "var(--success-bg)", color: "var(--success)" },
  warning: { background: "var(--warning-bg)", color: "var(--warning)" },
  danger: { background: "var(--danger-bg)", color: "var(--danger)" },
  info: { background: "var(--info-bg)", color: "var(--info)" },
  neutral: { background: "var(--bg-elevated)", color: "var(--text-secondary)" },
};

export default function Badge({
  variant = "default",
  className,
  children,
}: {
  variant?: BadgeVariant;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn("inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium", className)}
      style={styles[variant]}
    >
      {children}
    </span>
  );
}