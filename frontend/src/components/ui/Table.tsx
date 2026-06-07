import { cn } from "@/lib/utils";

export function Table({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl" style={{ border: "1px solid var(--border-subtle)" }}>
      <table className={cn("w-full text-sm border-collapse", className)}>
        {children}
      </table>
    </div>
  );
}

export function Thead({ children }: { children: React.ReactNode }) {
  return (
    <thead style={{ background: "var(--bg-elevated)", borderBottom: "1px solid var(--border-subtle)" }}>
      {children}
    </thead>
  );
}

export function Th({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <th
      className={cn("px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider", className)}
      style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-display)" }}
    >
      {children}
    </th>
  );
}

export function Tbody({ children }: { children: React.ReactNode }) {
  return <tbody>{children}</tbody>;
}

export function Tr({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <tr
      className={cn("transition-colors hover:bg-[var(--bg-elevated)]", className)}
      style={{ borderBottom: "1px solid var(--border-subtle)" }}
    >
      {children}
    </tr>
  );
}

export function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <td
      className={cn("px-4 py-3", className)}
      style={{ color: "var(--text-primary)" }}
    >
      {children}
    </td>
  );
}