## Project Plan — Detailed Checklist, Tests, and Success Criteria

This document expands the high-level plan into actionable phases with concrete substeps, tests, and acceptance criteria. Each numbered Phase is intended to be completed and reviewed in a single batched commit.

Phase 1 — Plan (this document)
- Substeps:
	- Finalize substeps for all subsequent phases.
	- Create `frontend/AGENTS.md` describing the existing frontend code and how it maps to plan phases.
	- Produce `docs/kanban_schema.md` and `docs/ai_schema.md` with proposed schemas.
- Tests / Success criteria:
	- `docs/PLAN.md`, `docs/kanban_schema.md`, and `docs/ai_schema.md` are present and approved by the user.
	- User confirms scope and approves proceeding to scaffolding.

Phase 2 — Scaffolding (Docker + backend skeleton)
- Substeps:
	- Add `Dockerfile` and `docker-compose.yml` to run backend and serve static frontend.
	- Create a minimal FastAPI app in `backend/` with a health endpoint (`GET /health`) and a sample static endpoint (`GET /`) that returns a small HTML page.
	- Add start/stop helper scripts in `scripts/` for macOS/Linux/Windows.
- Tests / Success criteria:
	- Container builds locally without errors.
	- `GET /health` returns 200 OK in containerized environment.
	- Start/stop scripts run without manual steps.

Phase 3 — Frontend static build and serve
- Substeps:
	- Add a production build step to `frontend/package.json` that outputs static assets.
	- Configure FastAPI to serve the static build from `/`.
	- Verify the demo Kanban appears at `/` when container is running.
- Tests / Success criteria:
	- Production build completes locally.
	- Visiting `/` shows the existing demo Kanban UI.

Phase 4 — Fake user sign-in
- Substeps:
	- Add a simple authentication guard on the frontend that requires credentials `user` / `password`.
	- Backend exposes an auth endpoint (`POST /api/login`) that validates the dummy credentials and returns a session token (cookie or simple bearer token).
	- Add logout flow.
- Tests / Success criteria:
	- Unauthorized requests to the Kanban UI redirect to login.
	- Login succeeds with `user`/`password` and fails otherwise.

Phase 5 — Database modeling (normalized tables)
- Substeps:
	- Implement a normalized SQLite schema and migration logic (create DB if missing).
	- Tables: `users`, `boards`, `columns`, `cards`, `card_history` (see `docs/kanban_schema.md`).
	- Add simple seed data for the default user and board on first run.
- Tests / Success criteria:
	- DB file is created automatically on first server start.
	- Simple CRUD operations work against the DB via backend unit tests.

Phase 6 — Backend API for Kanban
- Substeps:
	- Implement RESTful endpoints to read/update board, columns, and cards for an authenticated user (CRUD).
	- Add server-side validation and simple concurrency controls (ETag or updated_at checks).
	- Unit tests with `pytest` covering endpoints and DB interactions.
- Tests / Success criteria:
	- Backend unit tests pass locally.
	- End-to-end manual test: create, update, move, and delete cards via API.

Phase 7 — Frontend + Backend integration
- Substeps:
	- Replace local demo store with API calls to the backend.
	- Ensure drag-and-drop updates persist to backend and UI updates reflect server state.
	- Add frontend tests (unit + integration with `vitest` / `playwright` as needed).
- Tests / Success criteria:
	- Frontend integration tests exercise key flows (move card, edit card, create card).
	- App persists changes and reloads with the persisted state.

Phase 8 — AI connectivity
- Substeps:
	- Add backend integration with OpenRouter using `OPENROUTER_API_KEY` from `.env`.
	- Add a test endpoint that forwards a trivial prompt (e.g., "2+2") to the model and returns the result.
- Tests / Success criteria:
	- Backend can call OpenRouter and receives a valid response for a simple prompt.
	- Failure modes (missing key, network) return sensible errors.

Phase 9 — AI structured outputs and Kanban updates
- Substeps:
	- Define and implement the AI structured-output schema (see `docs/ai_schema.md`).
	- Backend endpoint: send the current Kanban JSON + user prompt to the model and parse structured outputs.
	- If AI suggests Kanban updates, apply them transactionally to the DB and return both the AI text and applied changes.
- Tests / Success criteria:
	- Endpoint returns structured output matching schema.
	- When AI suggests card changes, DB is updated accordingly and state remains consistent.

Phase 10 — UI: AI chat sidebar and automatic updates
- Substeps:
	- Implement a sidebar chat UI that sends messages to the backend AI endpoint and displays AI responses.
	- If AI returns Kanban updates, apply them and refresh the UI in real time.
	- Add end-to-end tests for the chat flow and an example scripted AI update.
- Tests / Success criteria:
	- Chat UI exchanges messages and displays AI responses.
	- When AI returns updates, the UI reflects the changes without manual refresh.

Notes / Constraints
- Follow the technical defaults in `AGENTS.md` unless a clearly better alternative exists. Propose alternatives when they materially improve reliability or cost.
- Secrets stored in `.env` at project root. Do not commit secrets.
- Work will be delivered in large batched commits per phase, per user preference.

Next steps (after approval)
- Implement Phase 2 (scaffolding) as the first development batch.

References
- See `AGENTS.md` at project root for high-level decisions.