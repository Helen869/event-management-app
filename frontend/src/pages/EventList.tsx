import { api, type EventResponse } from "../api";
import { EventBadges, LoadError, Loading } from "../components";
import { formatDateTime } from "../dates";
import { useLoad } from "../hooks";
import { plural } from "../text";

export function EventList() {
  const { data: events, error, loading, reload } = useLoad(api.listEvents);

  return (
    <>
      <div className="page-header">
        <h1>Events</h1>
        <a className="button button-primary" href="#/events/new">New event</a>
      </div>
      {loading && <Loading what="events" />}
      {error && <LoadError error={error} onRetry={reload} />}
      {events && events.length === 0 && (
        <div className="panel empty">
          <p>No events yet.</p>
          <a className="button button-primary" href="#/events/new">Create your first event</a>
        </div>
      )}
      {events && events.length > 0 && (
        <>
          <EventSection title="Upcoming" events={events.filter((e) => !e.is_past)} empty="No upcoming events." />
          {/* Most recent first: the API returns ascending start order. */}
          <EventSection title="Past" events={events.filter((e) => e.is_past).reverse()} empty="No past events." />
        </>
      )}
    </>
  );
}

function EventSection({ title, events, empty }: { title: string; events: EventResponse[]; empty: string }) {
  return (
    <section>
      <h2>{title} <span className="muted">({events.length})</span></h2>
      {events.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <ul className="card-grid">
          {events.map((event) => (
            <li key={event.id} className="card">
              <div className="card-title">
                <a href={`#/events/${event.id}`}>{event.title}</a>
                <EventBadges event={event} />
              </div>
              <p className="muted">{formatDateTime(event.starts_at)}</p>
              <p>
                {event.registered_count} / {event.max_capacity} registered ·{" "}
                <strong>{event.remaining_seats}</strong> {plural(event.remaining_seats, "seat")} left
              </p>
              <div className="actions">
                <a className="button" href={`#/events/${event.id}`}>View</a>
                {event.is_past ? (
                  <button className="button" disabled title="Started events can't be edited">Edit</button>
                ) : (
                  <a className="button" href={`#/events/${event.id}/edit`}>Edit</a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
