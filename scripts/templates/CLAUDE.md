# CLAUDE.md

**Status:** Project charter for Claude Code and Claude Desktop.

## Required Reading

Before any task, read `docs/guide/ai-behavior.md` fully. It defines how we collaborate.

## Project Context

- This project follows Spec-Driven Development (SDD).
- Specs live in `docs/feature/`.
- Architecture decisions live in `docs/adr/`.
- Executable constraints live in harness tests.
- For doc navigation, see `docs/INDEX.md`.

## How to Work

1. Read `docs/guide/ai-behavior.md`.
2. If a task touches a documented area, read the relevant `docs/feature/` and `docs/adr/` files.
3. State assumptions and ask before guessing.
4. Make surgical changes only.
5. Verify with existing harnesses or by running the project tests.

## Hard Rules

- Do not rewrite unrelated code.
- Do not add speculative abstractions.
- Do not delete pre-existing code unless explicitly asked.
- If a spec exists, follow it. If it conflicts with reality, ask.
