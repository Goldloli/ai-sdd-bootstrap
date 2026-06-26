# {{PROJECT_NAME}}

This project uses AI-driven engineering practices:

- `docs/feature/` — Feature specs (locked decisions)
- `docs/adr/` — Architecture Decision Records
- `docs/guide/ai-behavior.md` — AI behavior constitution
- `AI_HANDOFF.md` — Project state snapshot for new AI sessions
- `CLAUDE.md` — Claude-specific charter
- `AGENTS.md` — Generic agent entry

## Quick Start for AI

1. Read `AI_HANDOFF.md` for current project state.
2. Read `docs/guide/ai-behavior.md`.
3. Read `docs/INDEX.md`.
4. Load only relevant specs and ADRs for the current task.

## Project Stages

- **MVP** — Validate ideas, keep specs minimal, let AI explore.
- **Foundation** — Review the MVP architecture, modularize, and record key ADRs.
- **Iteration** — Lock boundaries with specs and harnesses as the project stabilizes.

## Harness

Harness tests are generated on demand. See `docs/guide/ai-behavior.md` section 5.3 for when to add them.
