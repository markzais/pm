# Kanban Database Schema (Normalized)

This document proposes a normalized SQLite schema for the Kanban data model. It favors clarity and simple migrations over storing the entire board as JSON.

Tables
- `users`
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `username` TEXT UNIQUE NOT NULL
  - `password_hash` TEXT NOT NULL
  - `created_at` TEXT

- `boards`
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `user_id` INTEGER REFERENCES users(id) ON DELETE CASCADE
  - `title` TEXT NOT NULL
  - `created_at` TEXT

- `columns`
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `board_id` INTEGER REFERENCES boards(id) ON DELETE CASCADE
  - `title` TEXT NOT NULL
  - `position` INTEGER NOT NULL -- small int for ordering
  - `created_at` TEXT

- `cards`
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `column_id` INTEGER REFERENCES columns(id) ON DELETE CASCADE
  - `title` TEXT NOT NULL
  - `description` TEXT
  - `position` INTEGER NOT NULL
  - `metadata` JSON NULL -- optional freeform metadata
  - `updated_at` TEXT
  - `created_at` TEXT

- `card_history`
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `card_id` INTEGER REFERENCES cards(id) ON DELETE CASCADE
  - `action` TEXT NOT NULL -- e.g., created, updated, moved, deleted
  - `payload` JSON NULL -- snapshot or diff
  - `created_at` TEXT

Indexes & constraints
- Index `cards(column_id, position)` for ordering queries.
- Unique constraint on `(board_id, position)` for `columns` to keep column ordering consistent.

Migration / creation
- On startup, create DB file if missing and apply a simple migration that creates these tables.

Seed data
- Create default `user` with username `user` and a seeded password hash.
- Create one board and a set of columns (e.g., Todo, Doing, Done) with sample cards to match the frontend demo.

Testing & Success Criteria
- Unit tests for CRUD operations on `cards` and `columns`.
- Integration test that performs: move card between columns, update card content, and read back consistent state.

Notes
- Using normalized tables makes it straightforward to extend the model later (tags, assignments, multiple boards per user).
