# Event Management App

[![CI](https://github.com/Helen869/event-management-app/actions/workflows/ci.yml/badge.svg)](https://github.com/Helen869/event-management-app/actions/workflows/ci.yml)

A REST API (with a frontend to follow) for managing events and attendee registrations. Organizers create and edit events;
users register and unregister by email. Capacity, duplicates and started events are enforced by the backend.

## Features

- Create, list, view and update events (title, description, start date/time, max capacity). Event deletion is out of scope.
- Register an email for an event, unregister it, list an event's registrations.
- Business rules: no registration for started events, never exceed capacity (including concurrent requests), one
  registration per email per event (case- and whitespace-insensitive), capacity can't drop below current registrations,
  started events are read-only.
- Uniform JSON error body with machine-readable codes; request and business-event logging.

## Tech stack

| Area | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic (+ `email-validator`), Uvicorn |
| Tests & quality | Pytest, FastAPI TestClient (`httpx2`), pytest-cov, Ruff |
| Storage | In-memory dictionaries guarded by a lock |
| CI | GitHub Actions |

## Architecture

`routes (HTTP) → EventService (all business rules) → InMemoryRepository (storage + lock)`. The service raises domain
exceptions; one handler maps them to 404/409/422. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start

Requires Python 3.12.

**PowerShell (Windows)**
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version            # should print Python 3.12.x
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

**Bash (macOS/Linux)**
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate   # Git Bash on Windows: source .venv/Scripts/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The API runs at http://localhost:8000. Swagger UI: http://localhost:8000/docs.

## Runbook

All commands run from `backend/` with the virtual environment activated. They are the same in PowerShell and Bash.

| Task | Command |
|---|---|
| Run the API (auto-reload) | `uvicorn app.main:app --reload` |
| All tests | `pytest` |
| Unit tests only | `pytest tests/unit` |
| Integration tests only | `pytest tests/integration` |
| Tests with coverage | `pytest --cov` |
| Coverage gate (as CI) | `pytest --cov` then `coverage report --fail-under=80` |
| HTML coverage report | `coverage html` → open `htmlcov/index.html` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Reset all data | Stop the server (Ctrl+C) and start it again. Storage is in memory. |

**Troubleshooting**

| Symptom | Fix |
|---|---|
| `Activate.ps1 cannot be loaded because running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or run tools without activating: `.\.venv\Scripts\python -m pytest` |
| `python --version` shows 3.10 or 3.11 inside the venv | Delete `.venv` and recreate it with `py -3.12 -m venv .venv` (Windows) or `python3.12 -m venv .venv` |
| `ModuleNotFoundError: No module named 'app'` | Run commands from `backend/`, not the repo root |
| `[Errno 10048]` / address already in use | Another process uses port 8000: stop it, or run `uvicorn app.main:app --reload --port 8001` |
| Data disappeared | Expected after a restart or an auto-reload: storage is in memory |

## Testing

- **Unit tests** (`backend/tests/unit`): business rules on the service layer, with an injected fake clock and a thread-based concurrency test.
- **Integration tests** (`backend/tests/integration`): status codes, response schemas and the error body through `TestClient`.
- Each test gets a fresh repository, clock and app. Coverage is 99% of `backend/app`.

The rule-to-test matrix is in [docs/DECISIONS.md](docs/DECISIONS.md#test-strategy).

## Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pushes to `main` and `feature/**` and on pull requests to `main`.

**Quality gates (the pipeline fails on):**
- Ruff lint errors
- any unit or integration test failure
- backend coverage below 80% (line + branch)

**Viewing results:** open the repository's **Actions** tab and select a run of **CI**. Each step's log is shown per job.
JUnit XML and coverage reports (XML + HTML) are attached as the `backend-reports` artifact on the run's summary page.

Coverage exclusions: the repository `Protocol` declaration only.

## Assumptions and limitations

- A user is identified by email (trimmed, lowercased); there is no authentication or authorization.
- An event has one timezone-aware start time stored in UTC; it counts as started when `start <= now`.
- Data is in memory and process-local: lost on restart, and not shared across workers. Run a single Uvicorn worker.
- Cancelling puts the email in the URL, so it appears in logs.
- No event deletion and no pagination.

## Documentation

- [Architecture](docs/ARCHITECTURE.md): layers, data model, concurrency, error policy, networking, production evolution
- [API specification](docs/API_SPEC.md): endpoints, schemas, error codes, rule evaluation order
- [Decisions](docs/DECISIONS.md): ADRs, sequence diagrams, CI pipeline, test strategy
