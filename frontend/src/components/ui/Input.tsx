import { cn } from "@/lib/utils";
import { forwardRef } from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-medium"
            style={{ color: "var(--text-secondary)" }}
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "w-full px-3 py-2 rounded-lg text-sm transition-all duration-150",
            "placeholder:text-[var(--text-tertiary)]",
            "focus:outline-none focus:ring-2 focus:ring-[var(--brand-500)] focus:ring-offset-1",
            "focus:ring-offset-[var(--bg-surface)]",
            className
          )}
          style={{
            background: "var(--bg-elevated)",
            border: `1px solid ${error ? "var(--danger)" : "var(--border-default)"}`,
            color: "var(--text-primary)",
          }}
          {...props}
        />
        {error && (
          <p className="text-xs" style={{ color: "var(--danger)" }}>
            {error}
          </p>
        )}
        {hint && !error && (
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            {hint}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";
export default Input;