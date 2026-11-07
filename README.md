# Event Management App

[![CI](https://github.com/Helen869/event-management-app/actions/workflows/ci.yml/badge.svg)](https://github.com/Helen869/event-management-app/actions/workflows/ci.yml)

A web app for managing events and attendee registrations: a FastAPI REST API and a React frontend. Organizers create
and edit events; users register and unregister by email. Capacity, duplicates and started events are enforced by the backend.

## Features

- Create, list, view and update events (title, description, start date/time, max capacity). Event deletion is not implemented ([ADR-7](docs/DECISIONS.md#adr-7-event-deletion-is-not-implemented)).
- Register an email for an event, unregister it, list an event's registrations.
- Business rules: no registration for started events, never exceed capacity (including concurrent requests), one
  registration per email per event (case- and whitespace-insensitive), capacity can't drop below current registrations,
  started events are read-only.
- Dashboard with upcoming and past events, seats left, and Open/Full/Past status.
- Forms with client-side validation that mirrors the API; backend error messages shown inline and as notifications.
- Uniform JSON error body with machine-readable codes; request and business-event logging.

## Tech stack

| Area | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic (+ `email-validator`), Uvicorn |
| Frontend | React 19, TypeScript (strict), Vite, native Fetch API, plain CSS |
| Tests & quality | Pytest, FastAPI TestClient (`httpx2`), pytest-cov, Ruff, `tsc` |
| Storage | In-memory dictionaries guarded by a lock |
| CI | GitHub Actions |

## Architecture

```mermaid
flowchart TB
  FE["React frontend<br/>Pages, forms, notifications"]
  API["FastAPI routes<br/>Validation, status codes, errors"]
  SVC["Service layer<br/>All business rules live here"]
  REPO["In-memory repository<br/>Dictionaries plus one lock"]
  FE -->|"relative /api, Vite proxy in dev"| API
  API --> SVC
  SVC --> REPO
  classDef fe fill:#EEEDFE,stroke:#534AB7,color:#3C3489
  classDef api fill:#E1F5EE,stroke:#0F6E56,color:#085041
  classDef svc fill:#FAECE7,stroke:#993C1D,color:#712B13
  classDef repo fill:#F1EFE8,stroke:#5F5E5A,color:#444441
  class FE fe
  class API api
  class SVC svc
  class REPO repo
```

*Layers: the service raises domain exceptions and one API handler maps them to 404/409/422.*

```mermaid
flowchart TB
  C1{"Event not found?"} -->|yes| R1["404 EVENT_NOT_FOUND"]
  C1 -->|no| C2{"Event already started?"}
  C2 -->|yes| R2["409 EVENT_IN_PAST"]
  C2 -->|no| C3{"Email already registered?"}
  C3 -->|yes| R3["409 ALREADY_REGISTERED"]
  C3 -->|no| C4{"No seats left?"}
  C4 -->|yes| R4["409 EVENT_FULL"]
  C4 -->|no| OK["Add registration<br/>201 Created"]
  classDef bad fill:#FAECE7,stroke:#993C1D,color:#712B13
  classDef good fill:#E1F5EE,stroke:#0F6E56,color:#085041
  class R1,R2,R3,R4 bad
  class OK good
```

*Registration: after request validation (422), these checks run in this order inside one lock, so the capacity check and the insert are atomic.*

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository structure

```text
.github/workflows/ci.yml     CI: backend and frontend jobs
backend/
  app/
    main.py                  App factory, request logging middleware
    api/                     routes.py, schemas.py, errors.py (domain exception → HTTP)
    domain/                  models.py, errors.py (domain exceptions)
    service.py               All business rules
    repository.py            In-memory storage and the lock
  tests/
    unit/                    Business rules and concurrency on the service
    integration/             Status codes and schemas through TestClient
  pyproject.toml             Ruff, pytest and coverage config
  requirements*.txt          Runtime and dev dependencies
frontend/
  src/
    pages/                   EventList, EventForm, EventDetails
    api.ts                   Typed fetch client for /api
    router.ts, hooks.ts      Hash router; useLoad and useSubmit
    components.tsx, notifications.tsx, dates.ts, text.ts
    App.tsx, main.tsx, styles.css
  vite.config.ts             Dev proxy /api → :8000
docs/                        Architecture, API spec, decisions
```

Each module's responsibility: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#layer-responsibilities).

## Quick start

### Prerequisites

- **Python 3.12+** is required. On Windows, where several versions may be installed side by side, `py -3.12 -m venv .venv` selects 3.12 explicitly. Plain `python` may point to an older version.
- **Node.js 22+** (22 LTS is what CI uses; see [`frontend/.nvmrc`](frontend/.nvmrc)).

### 1. Backend (terminal 1)

**PowerShell (Windows)**
```powershell
cd backend
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned   # allows Activate.ps1 in this session only
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
python --version            # should print Python 3.12.x
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

The API runs at http://localhost:8000. Swagger UI: http://localhost:8000/docs.

### 2. Frontend (terminal 2)

**PowerShell (Windows)**
```powershell
cd frontend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned   # npm.ps1 is blocked by default; this session only
npm ci                      # installs the exact versions in package-lock.json
npm run dev
```

**Bash (macOS/Linux)**
```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. The Vite dev server forwards `/api` to the backend on port 8000, so start the backend first.

## Runbook

Backend commands run from `backend/` with the virtual environment activated. Frontend commands run from `frontend/`.
They are the same in PowerShell and Bash.

| Task | Command |
|---|---|
| Run the API (auto-reload) | `uvicorn app.main:app --reload` |
| All backend tests | `pytest` |
| Unit tests only | `pytest tests/unit` |
| Integration tests only | `pytest tests/integration` |
| Tests with coverage | `pytest --cov` |
| Coverage gate (as CI) | `pytest --cov` then `coverage report --fail-under=80` |
| HTML coverage report | `coverage html` → open `htmlcov/index.html` |
| Lint / format | `ruff check .` / `ruff format .` |
| Run the frontend (dev) | `npm run dev` |
| Type check | `npm run typecheck` |
| Production build | `npm run build` (output in `frontend/dist/`) |
| Serve the build locally | `npm run preview` (http://localhost:4173, same `/api` proxy) |
| Reset all data | Stop the backend (Ctrl+C) and start it again. Storage is in memory. |

**Troubleshooting**

| Symptom | Fix |
|---|---|
| `Activate.ps1` or `npm.ps1 cannot be loaded because running scripts is disabled` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in that window, or run tools without activating: `.\.venv\Scripts\python -m pytest` |
| `python --version` shows 3.10 or 3.11 inside the venv | Delete `.venv` and recreate it with `py -3.12 -m venv .venv` (Windows) or `python3.12 -m venv .venv` |
| `ModuleNotFoundError: No module named 'app'` | Run backend commands from `backend/`, not the repo root |
| `[Errno 10048]` / address already in use | Another process uses port 8000: stop it. The frontend proxy expects the API on 8000. |
| UI shows "Cannot reach the server" or "unexpected error (500)" | The backend is not running on port 8000; start it (terminal 1) |
| `npm ci` fails with `EPERM` on Windows | A running `npm run dev` holds files in `node_modules`; stop it and retry |
| Data disappeared | Expected after a backend restart or an auto-reload: storage is in memory |

## Testing

- **Unit tests** (`backend/tests/unit`): business rules on the service layer, with an injected fake clock and a thread-based concurrency test.
- **Integration tests** (`backend/tests/integration`): status codes, response schemas and the error body through `TestClient`.
- Each test gets a fresh repository, clock and app. Coverage is 99% of `backend/app`.
- **Frontend:** checked by strict type checking and the production build in CI. There are no automated frontend tests (optional in scope).

The rule-to-test matrix is in [docs/DECISIONS.md](docs/DECISIONS.md#test-strategy).

## Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pushes to `main` and `feature/**` and on pull requests to `main`.
Two jobs run in parallel: **Backend** (lint, unit tests, integration tests, coverage) and **Frontend** (`npm ci`, type check, build).

**Quality gates (the pipeline fails on):**
- Ruff lint errors
- any unit or integration test failure
- backend coverage below 80% (line + branch)
- frontend type-check or build failure

**Branch protection:** a repository ruleset on `main` requires a pull request and both checks, **Backend (lint, tests, coverage)** and **Frontend (type check, build)**, to pass on a branch that is up to date with `main`. Direct pushes and force pushes are blocked. Required approvals are 0 because there is a single contributor, and the owner configured no bypass. All changes go through `feat/…`, `fix/…` or `docs/…` branches.

**Viewing results:** open the repository's **Actions** tab and select a run of **CI**. Each step's log is shown per job.
JUnit XML and coverage reports (XML + HTML) are attached as the `backend-reports` artifact on the run's summary page.

Coverage exclusions: the repository `Protocol` declaration only.

## Assumptions and limitations

- A user is identified by email (trimmed, lowercased); there is no authentication or authorization.
- Events have only a start time (timezone-aware, stored in UTC). An event counts as past from the moment it starts (`start <= now`), and that moment is also the registration cutoff. A real system would add an end time and a separate registration deadline.
- The UI shows times in the browser's local time zone and sends UTC to the API.
- Data is in memory and process-local: lost on restart, and not shared across workers. Run a single Uvicorn worker.
- Cancelling puts the email in the URL, so it appears in logs.
- Event deletion is not implemented: a scope decision, see [ADR-7](docs/DECISIONS.md#adr-7-event-deletion-is-not-implemented). No pagination. A page's Past/Full status is as of its last load (it refreshes after every action).
- Production would serve the frontend and API under one origin through a reverse proxy; no deployment is included.

## Notes

Built with AI assistance (Claude Code). Design decisions, business rules and verification were reviewed and owned by the author.

## Documentation

- [Architecture](docs/ARCHITECTURE.md): layers, frontend design, data model, concurrency, error policy, networking, production evolution
- [API specification](docs/API_SPEC.md): endpoints, schemas, error codes, rule evaluation order
- [Decisions](docs/DECISIONS.md): ADRs, sequence diagrams, CI pipeline, test strategy

<!-- Test: shared AI review workflow integration -->
