# API Specification

The FastAPI-generated OpenAPI document is the source of truth: run the backend and open
[`/docs`](http://localhost:8000/docs) (Swagger UI) or [`/openapi.json`](http://localhost:8000/openapi.json).
This page summarizes it and adds the business constraints that OpenAPI cannot express.

## Conventions

- Base path: `/api`. JSON bodies, `snake_case` fields.
- Datetimes are ISO 8601. Requests **must** include a UTC offset (`Z` or `+02:00`); responses are always UTC with a `Z` suffix.
- Event IDs are UUIDs. A malformed ID is a request-shape error (422); a well-formed unknown ID is 404.
- Emails are trimmed and lowercased before storage and comparison, so `" Alice@Example.COM "` and `alice@example.com` are the same user.
- Unknown request fields are rejected (422).

## Endpoints

| Method | Path | Success | Errors |
|---|---|---|---|
| GET | `/api/events` | 200 `EventResponse[]` (sorted by `starts_at`) | – |
| GET | `/api/events/{event_id}` | 200 `EventResponse` | 404, 422 |
| POST | `/api/events` | 201 `EventResponse` + `Location` header | 422 |
| PUT | `/api/events/{event_id}` | 200 `EventResponse` | 404, 409, 422 |
| GET | `/api/events/{event_id}/registrations` | 200 `RegistrationResponse[]` (registration order) | 404, 422 |
| POST | `/api/events/{event_id}/registrations` | 201 `RegistrationResponse` | 404, 409, 422 |
| DELETE | `/api/events/{event_id}/registrations/{email}` | 204, empty body | 404, 409, 422 |

Event deletion is out of scope. `PUT` is a full replacement: every required field must be sent.

## Schemas

### `EventInput` (POST and PUT body)

| Field | Type | Rules |
|---|---|---|
| `title` | string | required, trimmed, 1–200 chars |
| `description` | string | optional, default `""`, trimmed, ≤ 2000 chars |
| `starts_at` | datetime | required, timezone-aware, must be in the future |
| `max_capacity` | integer | required, strict integer (no `"5"`, `5.5` or `true`), 1–100000 |

```json
{ "title": "Team Offsite", "description": "Q1 planning", "starts_at": "2026-12-01T09:00:00+01:00", "max_capacity": 30 }
```

### `EventResponse`

```json
{
  "id": "6f1c3a52-2b8e-4c0e-9a51-0f4f7f1f6d2a",
  "title": "Team Offsite",
  "description": "Q1 planning",
  "starts_at": "2026-12-01T08:00:00Z",
  "max_capacity": 30,
  "registered_count": 12,
  "remaining_seats": 18,
  "is_past": false,
  "is_full": false
}
```

`is_past` is `true` once `starts_at <= now` on the server clock. `registered_count` is derived from the stored registrations, never stored separately.

### `RegistrationInput` / `RegistrationResponse`

```json
{ "email": "Alice@Example.com" }
```
```json
{ "email": "alice@example.com", "registered_at": "2026-11-05T14:02:11.123456Z" }
```

### Cancelling: email in the path

The email is the last path segment and must be percent-encoded by the client
(`encodeURIComponent`). For example, `first.last+tag@example.com` becomes
`/api/events/{id}/registrations/first.last%2Btag%40example.com`. The route uses a `path` converter, so an
encoded `/` (legal in an email local part) still works. The email is normalized before lookup, and a
format check is not applied: an address that was never registered simply returns 404.

> Privacy note: the email appears in request URLs, so it appears in access logs and proxy logs.

## Error body

Every 4xx/5xx response uses the same shape:

```json
{ "code": "EVENT_FULL", "message": "This event is full.", "details": [] }
```

`details` lists field problems for request validation errors:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Some fields are missing or invalid.",
  "details": [{ "field": "max_capacity", "message": "Input should be greater than or equal to 1" }]
}
```

| Status | `code` | When |
|---|---|---|
| 422 | `VALIDATION_ERROR` | Missing/invalid field, naive datetime, malformed UUID, unknown field |
| 422 | `START_TIME_IN_PAST` | Create or update with `starts_at <= now` |
| 404 | `EVENT_NOT_FOUND` | Unknown event ID |
| 404 | `REGISTRATION_NOT_FOUND` | Cancelling an email that is not registered |
| 409 | `EVENT_IN_PAST` | Registering, cancelling, or updating once the event has started |
| 409 | `EVENT_FULL` | Registering when `registered_count == max_capacity` |
| 409 | `ALREADY_REGISTERED` | Registering an email already registered for the event |
| 409 | `CAPACITY_BELOW_REGISTRATIONS` | Update sets `max_capacity` below `registered_count` |
| 404/405 | `HTTP_404`, `HTTP_405` | Unknown route or method |
| 500 | `INTERNAL_ERROR` | Unexpected failure (no internal detail is exposed) |

## Rule evaluation order

When several rules fail at once, the first failing check decides the response. Request validation (422) always runs first.

| Operation | Order |
|---|---|
| Register | event exists (404) → event not started (409 `EVENT_IN_PAST`) → not already registered (409 `ALREADY_REGISTERED`) → seats left (409 `EVENT_FULL`) |
| Cancel | event exists (404) → event not started (409 `EVENT_IN_PAST`) → registration exists (404 `REGISTRATION_NOT_FOUND`) |
| Update | event exists (404) → event not started (409 `EVENT_IN_PAST`) → new start in future (422 `START_TIME_IN_PAST`) → `max_capacity >= registered_count` (409) |

"Already registered" wins over "full" because it is the more accurate answer for that user. Each ordering is fixed by a unit test (see the test matrix in [DECISIONS.md](DECISIONS.md#test-strategy)).

## Business constraints

- Registration is closed once `starts_at <= now`. An event starting exactly now counts as started.
- Registrations can never exceed `max_capacity`, including under concurrent requests (within one process).
- One registration per (event, normalized email). The same email may register for different events.
- Cancelling frees the seat immediately; the same email may register again.
- `max_capacity` may be reduced to exactly the current registration count (the event becomes full), but not below it.
- Started events are read-only: they can be listed and viewed, including attendees.
