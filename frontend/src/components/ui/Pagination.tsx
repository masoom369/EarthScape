import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  total: number;
  limit: number;
  onChange: (p: number) => void;
}

export default function Pagination({ page, total, limit, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / limit));
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between pt-3">
      <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
        Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total}
      </span>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          className="p-1.5 rounded-lg disabled:opacity-40 transition-colors hover:bg-[var(--bg-elevated)]"
          style={{ color: "var(--text-secondary)" }}
        >
          <ChevronLeft size={16} />
        </button>
        <span className="px-3 text-sm" style={{ color: "var(--text-primary)" }}>
          {page} / {totalPages}
        </span>
        <button
          onClick={() => onChange(page + 1)}
          disabled={page >= totalPages}
          className="p-1.5 rounded-lg disabled:opacity-40 transition-colors hover:bg-[var(--bg-elevated)]"
          style={{ color: "var(--text-secondary)" }}
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}