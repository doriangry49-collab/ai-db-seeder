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

## Related Work

This project focuses specifically on **zero-config cross-column state machine inference** (e.g. `status = 'cancelled'` → `cancellation_reason` filled, `shipped_at` null) — a gap left after Snaplet's shutdown in 2024.

Other tools worth knowing about:
- **[Snaplet Seed](https://github.com/supabase-community/seed)** — Snaplet's open-source fork, maintained by the Supabase community. Has an LLM mode for field-level text generation, but cross-column business logic still requires manual TypeScript `refinements`.
- **[seedloom](https://github.com/therealonenak/seedloom)** — broader provider support (Claude, OpenAI, Gemini, local models), pgvector-aware, ships as an MCP server. Strong on FK integrity and type/constraint handling, but doesn't currently target cross-column state inference.

If your use case is closer to what these tools already do well, they're great options. This project exists for the specific gap between them.

