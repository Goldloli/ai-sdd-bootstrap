# Project Documentation Index

## Required Reading (load first)
- [AI Behavior Guide](./guide/ai-behavior.md) — How AI assistants must collaborate on this project.

## By Task

### Starting a new feature
1. Check existing `docs/feature/` for related specs.
2. Check `docs/adr/` for relevant architecture decisions.
3. Write `docs/feature/<feature-name>.md` if the feature is ready to be locked.

### Making an architectural decision
1. Write `docs/adr/ADR-NNN-<title>.md`.
2. Update this index.

### Adding a harness
1. Read the relevant `docs/feature/` spec.
2. Add harness tests under the stack-specific harness directory.
3. Update this index if the harness is tied to a documented boundary.

## Directories

- `docs/adr/` — Architecture Decision Records
- `docs/feature/` — Feature specifications
- `docs/guide/` — Guides and project metadata
- `docs/examples/` — Format examples (meta-examples, not real decisions)
