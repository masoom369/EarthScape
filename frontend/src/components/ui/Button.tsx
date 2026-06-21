import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline" | "success-soft";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
}

const variantStyles: Record<Variant, React.CSSProperties> = {
  primary: { background: "var(--brand-600)", color: "white", border: "1px solid var(--brand-700)" },
  secondary: { background: "var(--bg-elevated)", color: "var(--text-primary)", border: "1px solid var(--border-default)" },
  // Ghost now carries a subtle resting border instead of fully transparent —
  // previously invisible against bg-surface (table action buttons read as
  // near-blank text). Border + bg-elevated give it presence at rest, not just on hover.
  ghost: { background: "var(--bg-elevated)", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)" },
  danger: { background: "var(--danger)", color: "white", border: "1px solid var(--danger)" },
  outline: { background: "transparent", color: "var(--brand-500)", border: "1px solid var(--brand-500)" },
  // Dedicated treatment for affirmative row actions (Ack, Approve, Resolve) —
  // filled success tint reads as "the thing to click" instead of a ghost link.
  "success-soft": { background: "var(--success-bg)", color: "var(--success)", border: "1px solid var(--success)" },
};

const sizeClasses: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs gap-1.5",
  md: "px-4 py-2 text-sm gap-2",
  lg: "px-5 py-2.5 text-base gap-2",
};

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "hover:brightness-110 active:scale-[0.98]",
        sizeClasses[size],
        className
      )}
      style={variantStyles[variant]}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 size={14} className="animate-spin" /> : icon}
      {children}
    </button>
  );
}