import { Card } from "./Card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: { value: number; label: string };
  accent?: string;
  className?: string;
}

export default function StatCard({ label, value, icon, trend, accent, className }: StatCardProps) {
  return (
    <Card className={cn("flex flex-col gap-3", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-widest" style={{ color: "var(--text-tertiary)", fontFamily: "var(--font-display)" }}>
          {label}
        </span>
        {icon && (
          <span
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: accent ?? "var(--brand-100)", color: accent ? "white" : "var(--brand-600)" }}
          >
            {icon}
          </span>
        )}
      </div>
      <div
        className="text-2xl md:text-3xl font-bold"
        style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
      >
        {value}
      </div>
      {trend && (
        <p className="text-xs" style={{ color: trend.value >= 0 ? "var(--success)" : "var(--danger)" }}>
          {trend.value >= 0 ? "+" : ""}{trend.value}% {trend.label}
        </p>
      )}
    </Card>
  );
}