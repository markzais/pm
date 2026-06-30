# Frontend AGENTS

This file describes the existing frontend code and how it maps to the project's plan.

Overview of key files (already present in `frontend/src`):
- `components/KanbanBoard.tsx`: main board component; orchestrates columns and cards and holds drag-and-drop logic.
- `components/KanbanColumn.tsx`: column wrapper handling card lists and column-level actions.
- `components/KanbanCard.tsx`: card display and edit UI.
- `components/NewCardForm.tsx`: form to create a new card locally.
- `lib/kanban.ts`: utility functions for board transforms and sample data.

Tests
- `components/KanbanBoard.test.tsx` and `lib/kanban.test.ts` contain unit tests for board behavior.

How this maps to the plan
- Phase 3 (static build) — the existing frontend can be statically built and served.
- Phase 7 (integration) — components will be adapted to call backend APIs instead of local state.
- Phase 10 (AI chat) — the UI should add a sidebar component that posts messages to the backend and applies returned updates to the same store that current components use.

Notes for implementers
- Keep component props minimal and prefer lifting state to a top-level provider when connecting to remote API.
- Preserve existing tests; convert mocks to API-integration tests during Phase 7.
