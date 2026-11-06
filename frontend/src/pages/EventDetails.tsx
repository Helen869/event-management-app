import { useState, type FormEvent } from "react";
import { api, toApiError } from "../api";
import { errorProps, EventBadges, FieldErrorText, LoadError, Loading } from "../components";
import { formatDateTime } from "../dates";
import { useLoad, useSubmit } from "../hooks";
import { useNotify } from "../notifications";

export function EventDetails({ id }: { id: string }) {
  const { data, error, reload } = useLoad(() => Promise.all([api.getEvent(id), api.listRegistrations(id)]));
  const notify = useNotify();
  const { busy, run } = useSubmit();
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string>();

  if (!data) return error ? <LoadError error={error} onRetry={reload} /> : <Loading what="event" />;
  const [event, registrations] = data;

  // Every mutation ends with a reload so seats and status always reflect the server.
  const register = (e: FormEvent) => {
    e.preventDefault();
    void run(async () => {
      try {
        const registration = await api.register(id, email);
        notify("success", `${registration.email} is registered.`);
        setEmail("");
        setEmailError(undefined);
      } catch (err) {
        const apiError = toApiError(err);
        setEmailError(apiError.details[0]?.message ?? apiError.message);
        notify("error", apiError.message);
      } finally {
        reload();
      }
    });
  };

  const unregister = (attendee: string) => {
    if (!window.confirm(`Remove ${attendee} from "${event.title}"?`)) return;
    void run(async () => {
      try {
        await api.unregister(id, attendee);
        notify("success", `${attendee} was unregistered.`);
      } catch (err) {
        notify("error", toApiError(err).message);
      } finally {
        reload();
      }
    });
  };

  return (
    <>
      <a href="#/" className="back-link">← All events</a>
      <div className="panel">
        <div className="page-header">
          <h1>{event.title} <EventBadges event={event} /></h1>
          {event.is_past ? (
            <button className="button" disabled title="Started events can't be edited">Edit</button>
          ) : (
            <a className="button" href={`#/events/${id}/edit`}>Edit</a>
          )}
        </div>
        <p className="muted">{formatDateTime(event.starts_at)}</p>
        {event.description && <p className="description">{event.description}</p>}
        <dl className="stats">
          <div><dt>Registered</dt><dd>{event.registered_count} / {event.max_capacity}</dd></div>
          <div><dt>Seats left</dt><dd>{event.remaining_seats}</dd></div>
        </dl>
        {event.is_past && (
          <p className="notice">This event has started. Registration is closed and attendees can no longer be changed.</p>
        )}
        {!event.is_past && event.is_full && (
          <p className="notice">This event is full. A seat opens up if someone unregisters.</p>
        )}
      </div>

      {!event.is_past && (
        <form className="panel" onSubmit={register}>
          <h2>Register</h2>
          <div className={emailError ? "field field-invalid" : "field"}>
            <label htmlFor="email">Email</label>
            <div className="inline">
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                disabled={event.is_full}
                required
                {...errorProps("email", emailError)}
              />
              <button className="button button-primary" type="submit" disabled={busy || event.is_full}>
                {busy ? "Working…" : "Register"}
              </button>
            </div>
            <FieldErrorText inputId="email" error={emailError} />
          </div>
        </form>
      )}

      <section className="panel">
        <h2>Attendees <span className="muted">({registrations.length})</span></h2>
        {registrations.length === 0 ? (
          <p className="muted">No one has registered yet.</p>
        ) : (
          <ul className="attendees">
            {registrations.map((r) => (
              <li key={r.email}>
                <div>
                  <strong>{r.email}</strong>
                  <span className="muted"> · registered {formatDateTime(r.registered_at)}</span>
                </div>
                <button
                  className="button button-danger"
                  onClick={() => unregister(r.email)}
                  disabled={busy || event.is_past}
                  title={event.is_past ? "Started events can't be changed" : undefined}
                >
                  Unregister
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
