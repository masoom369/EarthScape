import { useEffect, useRef } from "react";

/** Generic polling hook. interval read from env — never hardcoded at call site. */
export function usePoll(fn: () => void, intervalMs: number, enabled = true) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    if (!enabled) return;
    fn();
    const id = setInterval(() => fnRef.current(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs, enabled]); // eslint-disable-line react-hooks/exhaustive-deps
}