## Project Plan — Detailed Checklist, Tests, and Success Criteria

This document expands the high-level plan into actionable phases with concrete substeps, tests, and acceptance criteria. Each numbered Phase is intended to be completed and reviewed in a single batched commit.

## Completed Phases

Phase 1 — Plan ✅
- `docs/PLAN.md`, `docs/kanban_schema.md`, and `docs/ai_schema.md` created and approved.
- High-level requirements and technical decisions recorded in `AGENTS.md`.

Phase 2 — Scaffolding ✅
- `Dockerfile` (multi-stage: Node frontend build → Python runtime) and `docker-compose.yml` created.
- FastAPI backend with health endpoint (`GET /health`) and static file serving.
- Start/stop scripts in `scripts/` for macOS/Linux/Windows.

Phase 3 — Frontend static build and serve ✅
- Next.js configured with static export (`output: "export"` in `next.config.ts`).
- Frontend builds to `frontend/out/` and served by FastAPI from `/`.
- Demo Kanban appears at `/`.

Phase 4 — Fake user sign-in ✅
- AuthGate component on frontend requires credentials (`user`/`password`).
- Backend `/api/login` validates credentials and returns Bearer token.
- Token stored in localStorage as `pm-demo-token`.
- `/api/logout` clears token on backend (removes from `VALID_TOKENS` dict).
- `/api/me` endpoint returns current user.

Phase 5 — Database modeling ✅
- SQLite schema with normalized tables: `users`, `boards`, `columns`, `cards`, `card_history`.
- DB file created at `backend/kanban.db` on first run.
- Seed data: default user (`user`/`password`), board (`Kanban Studio`), 5 columns, 8 sample cards.
- Foreign keys and cascading deletes configured.

Phase 6 — Backend API for Kanban ✅
- RESTful endpoints implemented and tested with `pytest`:
  - `GET /api/board` - read board state for authenticated user
  - `POST /api/cards` - create card
  - `PATCH /api/cards/{id}` - update card (title, description)
  - `DELETE /api/cards/{id}` - delete card
  - `POST /api/cards/{id}/move` - move card with position
  - `PATCH /api/columns/{id}` - rename column
- Auth via Bearer token with `get_current_user_id` dependency.
- All 4 backend API tests passing.

Phase 7 — Frontend + Backend integration ✅
- API client (`frontend/src/lib/api.ts`) with functions: `fetchBoard()`, `createCardApi()`, `deleteCardApi()`, `moveCardApi()`, `renameColumnApi()`.
- KanbanBoard component wired to backend: fetches board on mount, persists mutations.
- Optimistic UI updates: state changes immediately, API calls in background.
- All 6 frontend tests passing (3 in `kanban.test.ts`, 3 in `KanbanBoard.test.tsx`).
- Frontend build succeeds and outputs to `frontend/out/`.

## Current Design Decisions (Logged for Phases 8-10)

### Frontend Architecture
- **Framework**: Next.js 16.1.6 with React 19.2.3
- **Build**: Static export to `frontend/out/` (no dynamic server)
- **State Management**: React hooks (useState) with optimistic updates, no external state library
- **Testing**: Vitest 3.2.4 with @testing-library/react and jsdom
- **Drag-and-drop**: @dnd-kit (non-sortable version for simplicity)
- **Styling**: Tailwind CSS with custom color scheme

### Backend Architecture
- **Framework**: FastAPI with Pydantic models
- **Server**: Uvicorn ASGI server
- **Package Manager**: `pip` via requirements.txt (note: AGENTS.md specified `uv`, but `pip` was used for simplicity)
- **Database**: SQLite at `backend/kanban.db` with normalized schema
- **Auth**: Bearer tokens stored in memory (dict) during runtime; not session/cookie based

### API Design
- **Endpoints**: RESTful with JSON payloads
- **Auth**: All board/card/column endpoints require `Authorization: Bearer {token}` header
- **Response Format**: Consistent JSON responses with appropriate HTTP status codes
- **Error Handling**: HTTPException with descriptive messages

### Deployment
- **Container**: Single Docker image with multi-stage build
  - Stage 1: Node 20 Alpine, builds Next.js frontend to `frontend/out/`
  - Stage 2: Python 3.11-slim, runs FastAPI server, copies frontend build, serves on port 8000
- **Database**: Local SQLite, persisted on filesystem
- **Secrets**: `.env` file (not yet integrated, but ready for OpenRouter API key in Phase 8)

---

## Upcoming Phases

Phase 8 — AI connectivity
- Substeps:
	- Add OpenRouter client integration to backend (`OPENROUTER_API_KEY` from `.env`).
	- Create `/api/ai/prompt` endpoint that forwards user message + board context to model.
	- Use `openai/gpt-oss-120b` model via OpenRouter.
	- Add error handling for missing key, network timeouts, and invalid responses.
- Tests / Success criteria:
	- Backend can call OpenRouter with a trivial prompt (e.g., "2+2") and receives a response.
	- Response is parsed and returned to frontend as JSON.
	- Error scenarios (missing key, network failure) return sensible error messages.
	- Endpoint requires authentication (Bearer token).

Phase 9 — AI structured outputs and Kanban updates
- Substeps:
	- Extend `/api/ai/prompt` to parse structured JSON responses from AI (per `docs/ai_schema.md`).
	- Validate AI-suggested actions (create, update, move, delete) before applying.
	- Apply valid actions transactionally to the database.
	- Return both AI response text and list of applied changes to frontend.
- Tests / Success criteria:
	- Unit tests: parse sample structured outputs and verify DB updates.
	- Integration tests: send prompt, receive structured output, confirm DB reflects changes.
	- Malformed AI responses are rejected safely; no partial updates if validation fails.
	- Endpoint returns applied actions in response payload.

Phase 10 — UI: AI chat sidebar and automatic updates
- Substeps:
	- Add chat sidebar component on the right side of the Kanban board.
	- Input field sends message to `/api/ai/prompt` endpoint.
	- Display AI response text in chat window.
	- If AI returns actions, apply them to local board state and refresh UI automatically.
	- Add end-to-end tests for chat flow with example scripted AI updates.
- Tests / Success criteria:
	- Chat UI is functional: send message, receive AI response, display in sidebar.
	- When AI suggests card changes, UI updates reflect applied changes without manual refresh.
	- E2E tests verify a complete flow: user message → AI response → card creation/move.
	- Chat history persists for the session.

## Notes / Constraints
- Follow the technical defaults in `AGENTS.md` unless a clearly better alternative exists.
- Secrets stored in `.env` at project root. Do not commit secrets.
- Work will be delivered in large batched commits per phase, per user preference.
- Keep the MVP simple: no extra features, no over-engineering.
- All code must have tests; identify root causes when issues arise, don't guess.

## References
- `AGENTS.md` — high-level business requirements and technical decisions
- `docs/kanban_schema.md` — normalized SQLite schema
- `docs/ai_schema.md` — structured AI output format