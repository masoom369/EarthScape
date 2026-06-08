import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Viewport-centered modal rendered via React portal into document.body.
 * Root cause fix: previously rendered inside the page component tree,
 * so centering was relative to the nearest positioned ancestor (the page
 * container), not the viewport. Portal bypasses that entirely.
 * Overlay uses var(--bg-overlay) from theme.css — respects light/dark mode.
 * backdrop-filter blur adds depth without destroying visual hierarchy.
 */
export default function Modal({ open, onClose, title, children, className }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);

    // Prevent body scroll while modal is open
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  function handleOverlayClick(e: React.MouseEvent<HTMLDivElement>) {
    // Close only when clicking the overlay itself, not the modal panel
    if (e.target === overlayRef.current) onClose();
  }

  return createPortal(
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      style={{
        // Theme-aware overlay: var(--bg-overlay) defined in theme.css for both modes
        background: "var(--bg-overlay)",
        backdropFilter: "blur(4px)",
        WebkitBackdropFilter: "blur(4px)",
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={cn(
          "relative w-full max-w-lg rounded-2xl p-6 animate-fade-up",
          className
        )}
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-default)",
          boxShadow: "var(--shadow-xl)",
          // Clamp height so modal never overflows viewport on small screens
          maxHeight: "calc(100dvh - 2rem)",
          overflowY: "auto",
        }}
      >
        <div className="flex items-center justify-between mb-5">
          <h2
            id="modal-title"
            className="text-lg font-bold"
            style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg transition-colors hover:bg-[var(--bg-surface)]"
            style={{ color: "var(--text-tertiary)" }}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body
  );
}