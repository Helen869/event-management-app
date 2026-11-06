import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, toApiError } from "./api";

// Pages are remounted (via `key`) when their ID changes, so `load` only reruns on reload().
export function useLoad<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<ApiError>();
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    load().then(
      (result) => {
        if (!active) return;
        setData(result);
        setError(undefined);
      },
      (err: unknown) => active && setError(toApiError(err)),
    );
    return () => {
      active = false;
    };
  }, [version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { data, error, loading: data === undefined && error === undefined, reload };
}

// The ref blocks a second submit before React re-renders the disabled button.
export function useSubmit() {
  const inFlight = useRef(false);
  const [busy, setBusy] = useState(false);

  const run = useCallback(async (action: () => Promise<void>) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    try {
      await action();
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }, []);

  return { busy, run };
}
