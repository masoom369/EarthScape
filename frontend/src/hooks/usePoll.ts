import { useEffect, useRef } from 'react';

export function usePoll(callback: () => void | Promise<void>, intervalMs: number, enabled = true) {
  const saved = useRef(callback);
  saved.current = callback;

  useEffect(() => {
    if (!enabled || intervalMs <= 0) return undefined;
    const tick = () => { saved.current(); };
    tick();
    const id = setInterval(tick, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs, enabled]);
}
