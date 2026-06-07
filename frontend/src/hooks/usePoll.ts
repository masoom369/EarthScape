import { useEffect, useRef } from "react";

/** Generic polling hook. Stable interval; fn ref updated via effect, never during render. */
export function usePoll(fn: () => void, intervalMs: number, enabled = true) {
  const fnRef = useRef(fn);

  useEffect(() => {
    fnRef.current = fn;
  });

  useEffect(() => {
    if (!enabled) return;
    fnRef.current();
    const id = setInterval(() => fnRef.current(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs, enabled]);
}