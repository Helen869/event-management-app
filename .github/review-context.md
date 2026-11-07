# AI review context — Event Management App

This is a lightweight full-stack Event Management application demonstrating REST API design, business-rule enforcement, concurrency handling, automated testing, and reusable AI-assisted code review. The application uses FastAPI/Pydantic, React/TypeScript, and an in-memory repository.

The AI PR reviewer is advisory, **not** a substitute for Ruff, Pytest, API integration tests, type checking or human approval.

## Important business invariants

- Registration closes when `starts_at <= now`; requests must be timezone-aware and server stores UTC.
- Each normalized email (trimmed, lowercased) can register once per event.
- Capacity must not be exceeded, including concurrent registrations in one process.
- Registration and capacity updates must be serialized under the repository lock.
- Event capacity may not be reduced below the existing registered count.
- Started events are read-only.
- Service layer owns business rules; API layer maps domain errors to HTTP responses.
- Each test gets isolated in-memory state; unit and API integration tests run in GitHub Actions.

## Deliberate MVP scope decisions

- **Event deletion is deferred, not accidentally omitted.** Standard CRUD would include deletion, so this is a documented partial-coverage tradeoff (ADR-7 in `docs/DECISIONS.md`). Before enabling deletion, clarify whether a user is cancelling or purging an event, who is allowed to do it, how attendees are notified, and whether historical records must be retained. This does not authorize ignoring bugs in existing event functions.
- No persistent database, authentication, notification service, cloud infrastructure, or frontend E2E tests.
- One Uvicorn process/worker; the lock does not protect across multiple processes.
- An email is used as a simple identity; unregister path currently includes the email, with a documented privacy limitation.

## Review focus

Find concrete regressions and security problems **visible in the changed diff**, especially:
- Broken capacity checks, duplicate prevention, time boundaries or lock scope.
- Changes that let the UI bypass backend enforcement or mishandle HTTP errors.
- Invalid API schema changes, error responses or missing state isolation.
- Unexpected external calls or secrets in code.

Do not make speculative infrastructure claims, demand out-of-scope features, or repeat accepted tradeoffs as fresh bugs. Keep findings actionable and confidence-calibrated.
