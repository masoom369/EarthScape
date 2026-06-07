import { cn } from "@/lib/utils";

export default function Spinner({ className, size = 20 }: { className?: string; size?: number }) {
  return (
    <svg
      className={cn("animate-spin", className)}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="12" cy="12" r="10" stroke="var(--border-default)" strokeWidth="3" />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="var(--brand-500)"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}