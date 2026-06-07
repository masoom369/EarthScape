import { cn } from "@/lib/utils";
import { forwardRef } from "react";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, className, children, ...props }, ref) => (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
          {label}
        </label>
      )}
      <select
        ref={ref}
        className={cn("w-full px-3 py-2 rounded-lg text-sm transition-all duration-150 cursor-pointer", className)}
        style={{
          background: "var(--bg-elevated)",
          border: `1px solid ${error ? "var(--danger)" : "var(--border-default)"}`,
          color: "var(--text-primary)",
        }}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-xs" style={{ color: "var(--danger)" }}>{error}</p>}
    </div>
  )
);
Select.displayName = "Select";
export default Select;