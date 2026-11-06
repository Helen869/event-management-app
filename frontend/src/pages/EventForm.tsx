import { useState, type FormEvent, type ReactNode } from "react";
import { api, toApiError, type ApiError, type EventResponse } from "../api";
import { LoadError, Loading } from "../components";
import { localInputToUtc, toLocalInput } from "../dates";
import { useLoad, useSubmit } from "../hooks";
import { useNotify } from "../notifications";
import { navigate } from "../router";
import { plural } from "../text";

const MAX_CAPACITY = 100_000;

type Values = { title: string; description: string; startsAt: string; maxCapacity: string };
type Errors = Partial<Record<keyof Values | "form", string>>;

const API_FIELDS: Record<string, keyof Values> = {
  title: "title",
  description: "description",
  starts_at: "startsAt",
  max_capacity: "maxCapacity",
};

// Mirrors the backend rules for fast feedback; the server's answer is still authoritative.
function validate(values: Values, registeredCount: number): Errors {
  const errors: Errors = {};
  const title = values.title.trim();
  if (!title) errors.title = "Title is required.";
  else if (title.length > 200) errors.title = "Title must be at most 200 characters.";
  if (values.description.trim().length > 2000) errors.description = "Description must be at most 2000 characters.";
  if (!values.startsAt) errors.startsAt = "Start date and time are required.";
  else if (new Date(values.startsAt) <= new Date()) errors.startsAt = "Start time must be in the future.";
  const capacity = Number(values.maxCapacity);
  if (!values.maxCapacity || !Number.isInteger(capacity) || capacity < 1 || capacity > MAX_CAPACITY) {
    errors.maxCapacity = `Max capacity must be a whole number from 1 to ${MAX_CAPACITY}.`;
  } else if (capacity < registeredCount) {
    // Reached only when 1 <= capacity < registeredCount, so the count is always plural.
    errors.maxCapacity = `Max capacity can't be lower than the ${registeredCount} current registrations.`;
  }
  return errors;
}

function errorsFromApi(error: ApiError): Errors {
  const errors: Errors = {};
  for (const detail of error.details) {
    const field = API_FIELDS[detail.field];
    if (field) errors[field] = detail.message;
  }
  if (error.code === "START_TIME_IN_PAST") errors.startsAt = error.message;
  if (error.code === "CAPACITY_BELOW_REGISTRATIONS") errors.maxCapacity = error.message;
  if (Object.keys(errors).length === 0) errors.form = error.message;
  return errors;
}

export function EditEvent({ id }: { id: string }) {
  const { data: event, error, reload } = useLoad(() => api.getEvent(id));
  if (!event) return error ? <LoadError error={error} onRetry={reload} /> : <Loading what="event" />;
  if (event.is_past) {
    return (
      <div className="panel">
        <p>This event has started and can no longer be edited.</p>
        <a className="button" href={`#/events/${id}`}>Back to event</a>
      </div>
    );
  }
  return <EventForm event={event} />;
}

export function EventForm({ event }: { event?: EventResponse }) {
  const notify = useNotify();
  const { busy, run } = useSubmit();
  const [errors, setErrors] = useState<Errors>({});
  const [values, setValues] = useState<Values>({
    title: event?.title ?? "",
    description: event?.description ?? "",
    startsAt: event ? toLocalInput(new Date(event.starts_at)) : "",
    maxCapacity: event ? String(event.max_capacity) : "",
  });
  const set = (field: keyof Values) => (e: { target: { value: string } }) =>
    setValues((current) => ({ ...current, [field]: e.target.value }));

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const found = validate(values, event?.registered_count ?? 0);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    void run(async () => {
      const input = {
        title: values.title.trim(),
        description: values.description.trim(),
        starts_at: localInputToUtc(values.startsAt),
        max_capacity: Number(values.maxCapacity),
      };
      try {
        const saved = event ? await api.updateEvent(event.id, input) : await api.createEvent(input);
        notify("success", event ? "Event updated." : "Event created.");
        navigate(`/events/${saved.id}`);
      } catch (err) {
        const apiError = toApiError(err);
        setErrors(errorsFromApi(apiError));
        notify("error", apiError.message);
      }
    });
  };

  return (
    <form className="panel form" onSubmit={onSubmit} noValidate>
      <h1>{event ? "Edit event" : "New event"}</h1>
      {errors.form && <p className="form-error" role="alert">{errors.form}</p>}
      <Field label="Title" error={errors.title} id="title">
        <input id="title" value={values.title} onChange={set("title")} maxLength={200} required />
      </Field>
      <Field label="Description (optional)" error={errors.description} id="description">
        <textarea id="description" value={values.description} onChange={set("description")} rows={4} />
      </Field>
      <Field label="Starts at (your local time)" error={errors.startsAt} id="startsAt">
        <input
          id="startsAt"
          type="datetime-local"
          value={values.startsAt}
          min={toLocalInput(new Date())}
          onChange={set("startsAt")}
          required
        />
      </Field>
      <Field label="Max capacity" error={errors.maxCapacity} id="maxCapacity">
        <input
          id="maxCapacity"
          type="number"
          inputMode="numeric"
          min={Math.max(1, event?.registered_count ?? 0)}
          max={MAX_CAPACITY}
          step={1}
          value={values.maxCapacity}
          onChange={set("maxCapacity")}
          required
        />
      </Field>
      {event && event.registered_count > 0 && (
        <p className="muted">
          {event.registered_count} {plural(event.registered_count, "person", "people")} registered; capacity can't
          go below {event.registered_count}.
        </p>
      )}
      <div className="actions">
        <button className="button button-primary" type="submit" disabled={busy}>
          {busy ? "Saving…" : event ? "Save changes" : "Create event"}
        </button>
        <a className="button" href={event ? `#/events/${event.id}` : "#/"}>Cancel</a>
      </div>
    </form>
  );
}

function Field({ label, error, id, children }: { label: string; error?: string; id: string; children: ReactNode }) {
  return (
    <div className={error ? "field field-invalid" : "field"}>
      <label htmlFor={id}>{label}</label>
      {children}
      {error && <p className="field-error">{error}</p>}
    </div>
  );
}
