# AI-Native Database Seeder

Zero-config relational database seeder that automatically infers cross-column state machine logic and foreign key dependencies using LLM schema introspection.

## Features
- **Zero-Shot State Cohesion:** Automatically infers logic (e.g. `status = 'cancelled'` -> `cancellation_reason` populated, `shipped_at` NULL).
- **FK Graph Topological Sorting:** Resolves foreign key insertion order automatically.
- **SQL & ORM Agnostic:** Introspects via SQLAlchemy (PostgreSQL, SQLite, MySQL).

## Quickstart

1. **Install:**
   ```bash
   pip install -e .
   ```

2. **Configure Key:**
   Copy `.env.example` to `.env` and insert your `OPENROUTER_API_KEY`:
   ```bash
   OPENROUTER_API_KEY=your_key_here
   ```

3. **Generate Data:**
   ```bash
   db-seed generate --db-url "sqlite:///test.db" --rows 5
   ```
