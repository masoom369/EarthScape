import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterBarProps {
  children: React.ReactNode;
  className?: string;
}

export function FilterBar({ children, className }: FilterBarProps) {
  return (
    <div
      className={cn("flex flex-wrap items-end gap-3 p-4 rounded-xl mb-4", className)}
      style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)" }}
    >
      {children}
    </div>
  );
}

interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  containerClassName?: string;
}

export function SearchInput({ containerClassName, className, ...props }: SearchInputProps) {
  return (
    <div className={cn("relative", containerClassName)}>
      <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: "var(--text-tertiary)" }} />
      <input
        className={cn("pl-9 pr-3 py-2 rounded-lg text-sm w-full", className)}
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-default)",
          color: "var(--text-primary)",
        }}
        {...props}
      />
    </div>
  );
}