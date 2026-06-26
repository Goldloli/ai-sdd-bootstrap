---
name: ai-sdd-bootstrap
description: Staged AI-engineering scaffold. Minimal MVP setup first, then full Spec/Harness/ADR framework on demand.
---

# AI SDD Bootstrap

This skill bootstraps a project for sustainable AI-driven development using Spec-Driven Development (SDD) principles.

**Core philosophy**: do not over-engineer at the MVP stage. Start with a minimal scaffold, let AI explore freely, and only build the full docs/ADR/spec/harness framework once the architecture stabilizes.

## When to use

Use this skill when:
- Starting a new project that will be developed with AI assistance
- A project has finished its MVP/exploration phase and needs a real engineering foundation
- A project has reached the iteration phase and needs documented boundaries
- You need to add an ADR, Feature Spec, or Harness to an existing project

## Commands

This skill wraps `~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py`.

Run one of:
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py init`
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py bootstrap-foundation`
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py status`
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-adr`
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-spec`
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-harness`
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py review-architecture`
- `python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py suggest-harness`

## Natural Language Invocation

When this skill is invoked with a prompt, map the intent to a command:

- "init", "initialize", "set up this project", "bootstrap", "新建项目" → `init`
- "bootstrap foundation", "build the full framework", "建立更详细的adr和harness框架", "进入建地基阶段", "完善工程化框架", "搭好工程化底座" → `bootstrap-foundation`
- "status", "check status", "what should I do next" → `status`
- "add an ADR", "new architecture decision" → `add-adr`
- "add a spec", "write a feature spec" → `add-spec`
- "add a harness", "write a test" → `add-harness`
- "review architecture", "audit the codebase", "check coupling" → `review-architecture`
- "suggest harness", "where should I add tests", "what needs tests" → `suggest-harness`

## Staged workflow

### 1. MVP / exploration phase → `init`

Create only the minimal scaffold:
- `README.md` (MVP version)
- `AGENTS.md` (MVP version: encourage exploration, forbid premature specs)
- `.gitignore`

No `docs/`, no `CLAUDE.md`, no `AI_HANDOFF.md`, no harness directory. This avoids early constraints and lets AI explore freely.

### 2. Foundation phase → `bootstrap-foundation`

After the MVP is validated and architecture stabilizes, run this to build the full SDD framework:
- `docs/INDEX.md`
- `docs/guide/ai-behavior.md`
- `docs/guide/project-meta.md` (stage = foundation)
- `docs/adr/`
- `docs/feature/`
- `docs/examples/`
- `AI_HANDOFF.md`
- `CLAUDE.md`
- `AGENTS.md` (foundation version)
- Updated `README.md`

This is the right time to say:
> "为这个项目建立更详细的 ADR 和 Harness 框架。"

### 3. Iteration phase

Use `add-adr`, `add-spec`, `add-harness`, `review-architecture`, and `suggest-harness` as the project grows.

## Design doc

See the full design at `/Users/gejiawei/Desktop/ai_picuure/ai编程工程化skills/docs/superpowers/specs/2026-06-26-ai-sdd-bootstrap-design.md`.

## Usage Examples

### Initialize a new project (MVP)

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py init
```

Choose your primary stack and optional additional stacks. The command creates the minimal MVP scaffold.
For non-interactive use, pass `--primary-stack` and optional `--additional-stack`.

Supported stacks:
- `nodejs-ts`
- `python`
- `rust`
- `language-agnostic`
- `shell`

You can mix stacks, e.g. primary `nodejs-ts` + additional `python` for full-stack projects.

### Bootstrap the full framework after MVP

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py bootstrap-foundation
```

This builds the docs/ADR/spec/harness structure and switches the project stage to `foundation`.

### Check project status

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py status
```

### Add an ADR

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-adr
```

Non-interactive example:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-adr \
  --title "Use SQLite" \
  --background "The app needs local persistence" \
  --decision "Use SQLite for local data" \
  --consequences "Simple local storage, not multi-user" \
  --status accepted
```

### Add a feature spec

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-spec
```

Non-interactive example:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-spec \
  --title "Login Flow" \
  --in-scope "Email login" \
  --out-scope "Social login" \
  --boundaries "Do not bypass password verification,Do not mutate user roles" \
  --acceptance "Reject bad password,Create session for valid user"
```

### Add a harness skeleton

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-harness
```

Generated harnesses are draft constraints and intentionally fail until you replace the placeholder with real assertions.

Supported harness generators:
- `nodejs-ts` → Vitest `.spec.ts`
- `python` → pytest `test_*.py`
- `rust` → cargo test `*.rs`
- `shell` → bash `.sh` (also available as a fallback for any project)
- `language-agnostic` → docs only, use `shell` if you need a generic harness
