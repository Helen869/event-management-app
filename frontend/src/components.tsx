import type { ApiError, EventResponse } from "./api";

export function EventBadges({ event }: { event: EventResponse }) {
  if (event.is_past) return <span className="badge badge-past">Past</span>;
  if (event.is_full) return <span className="badge badge-full">Full</span>;
  return <span className="badge badge-open">Open</span>;
}

// Ties an input to its error message so screen readers announce it.
export function errorProps(inputId: string, error?: string) {
  return error ? { "aria-invalid": true, "aria-describedby": `${inputId}-error` } : {};
}

export function FieldErrorText({ inputId, error }: { inputId: string; error?: string }) {
  return error ? <p className="field-error" id={`${inputId}-error`}>{error}</p> : null;
}

export function Loading({ what }: { what: string }) {
  return <p className="muted" role="status">Loading {what}…</p>;
}

export function LoadError({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  // A malformed ID in the URL is a 422 from the API, but to the user it is simply a missing event.
  const notFound = error.status === 404 || error.status === 422;
  return (
    <div className="panel error-panel" role="alert">
      <p>{notFound ? "Event not found." : error.message}</p>
      {notFound ? (
        <a className="button" href="#/">Back to events</a>
      ) : (
        <button className="button" onClick={onRetry}>Try again</button>
      )}
    </div>
  );
}
