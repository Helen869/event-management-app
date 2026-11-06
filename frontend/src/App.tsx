import { EventDetails } from "./pages/EventDetails";
import { EditEvent, EventForm } from "./pages/EventForm";
import { EventList } from "./pages/EventList";
import { useRoute, type Route } from "./router";

export function App() {
  const route = useRoute();
  return (
    <>
      <header className="app-header">
        <a href="#/" className="brand">Event Manager</a>
      </header>
      <main className="container">{page(route)}</main>
    </>
  );
}

// `key` remounts a page when its ID changes, so no page ever shows another event's stale data.
function page(route: Route) {
  switch (route.page) {
    case "list":
      return <EventList />;
    case "new":
      return <EventForm key="new" />;
    case "edit":
      return <EditEvent key={`edit-${route.id}`} id={route.id} />;
    case "details":
      return <EventDetails key={route.id} id={route.id} />;
    case "notFound":
      return (
        <div className="panel">
          <p>Page not found.</p>
          <a className="button" href="#/">Back to events</a>
        </div>
      );
  }
}
