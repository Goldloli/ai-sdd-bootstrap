# AI SDD Bootstrap

AI SDD Bootstrap is a staged scaffold for AI-assisted software projects. It helps you start lightweight during MVP exploration, then add Spec, ADR, and Harness structure only after the project is worth sustaining.

The core idea is simple:

- **MVP stage:** move fast, validate the idea, avoid premature specs.
- **Foundation stage:** after the MVP works, document the architecture and project rules.
- **Iteration stage:** lock stable decisions with specs and executable harnesses.

## When To Use It

Use this skill when:

- You are starting a new project with AI assistance.
- Your MVP already works and you want to prevent future AI changes from breaking old behavior.
- You need a repeatable structure for ADRs, feature specs, and harness tests.
- You want agents such as Codex, Kimi, Cursor, Claude Code, or Copilot to read the same project rules.

Do not use the full framework at the very beginning of a throwaway prototype. Start with `init` only.

## Install Location

This skill lives at:

```bash
~/.agents/skills/ai-sdd-bootstrap
```

The main command is:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py
```

For convenience, you can create an alias:

```bash
alias ai-sdd='python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py'
```

Then use `ai-sdd status`, `ai-sdd init`, and so on.

## Supported Stacks

- `nodejs-ts`
- `python`
- `rust`
- `language-agnostic`
- `shell`

You can choose one primary stack and optional additional stacks.

## The Recommended Workflow

### 1. Start A New MVP

Run this inside your project root:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py init
```

Non-interactive example:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py init \
  --primary-stack nodejs-ts
```

This creates only:

```text
AGENTS.md
README.md
.gitignore
```

It intentionally does **not** create `docs/`, `CLAUDE.md`, `AI_HANDOFF.md`, or harness files. The MVP is still a draft; do not bury it under process too early.

### 2. Build Freely Until The MVP Is Validated

During MVP:

- Let AI explore implementation options.
- Keep code small and easy to change.
- Avoid writing many specs.
- Record only decisions that are truly locked.

Good signals that you are ready for the next stage:

- You have used the MVP as a real user.
- The product direction is no longer changing every hour.
- You can name the main modules and boundaries.
- You have started worrying that AI may break old behavior while adding new features.

### 3. Bootstrap The Foundation

Once the MVP is validated, run:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py bootstrap-foundation
```

Non-interactive example:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py bootstrap-foundation \
  --primary-stack nodejs-ts \
  --additional-stack python
```

This creates the full SDD structure:

```text
docs/
  INDEX.md
  adr/
  feature/
  guide/
    ai-behavior.md
    project-meta.md
  examples/
AGENTS.md
AI_HANDOFF.md
CLAUDE.md
README.md
```

From this point on, agents should read `AGENTS.md`, `CLAUDE.md`, `AI_HANDOFF.md`, and `docs/guide/ai-behavior.md` before making substantial changes.

### 4. Check Project Status

Run this any time:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py status
```

It reports:

- Whether the project is initialized.
- Whether the foundation framework exists.
- Current stage.
- ADR count.
- Feature spec count.
- Harness count.
- Git branch and uncommitted files.
- Recommended next actions.

## Common Commands

### Add An ADR

Use an ADR for architectural decisions that should not be re-decided every time a new AI session starts.

Interactive:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-adr
```

Non-interactive:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-adr \
  --title "Use SQLite For Local Storage" \
  --background "The desktop app needs reliable local persistence." \
  --decision "Use SQLite as the local persistence layer." \
  --consequences "Simple local-first storage, but not a multi-user database." \
  --status accepted
```

This creates a file under `docs/adr/` and updates `docs/INDEX.md`.

### Add A Feature Spec

Use a feature spec when a behavior or boundary has stabilized.

Interactive:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-spec
```

Non-interactive:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-spec \
  --title "Login Flow" \
  --in-scope "Email and password login" \
  --out-scope "Social login, password reset" \
  --boundaries "Do not bypass password verification,Do not mutate user roles during login" \
  --acceptance "Reject wrong password,Create session for valid credentials" \
  --dependencies "ADR-001-use-sqlite-for-local-storage.md"
```

This creates a file under `docs/feature/` and updates `docs/INDEX.md`.

### Add A Harness

Use a harness when a behavior is important enough to enforce with executable checks.

Interactive:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-harness
```

Non-interactive:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py add-harness \
  --stack nodejs-ts \
  --title "Login Rejects Wrong Password" \
  --module auth \
  --purpose "Lock the invariant that invalid credentials never create a session."
```

Important: generated harnesses are **draft constraints**. They intentionally fail until you replace the placeholder with real setup, real inputs, and real assertions. Do not count a generated harness as coverage until it tests real behavior.

Generated paths:

```text
nodejs-ts -> tests/harness/<module>/<name>.spec.ts
python    -> tests/harness/<module>/test_<name>.py
rust      -> tests/harness/<module>/<name>.rs
shell     -> tests/harness/<module>/<name>.sh
```

### Review Architecture

After the MVP works, ask the tool to generate an architecture review document:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py review-architecture
```

This scans source files and writes:

```text
docs/guide/architecture-review.md
```

Use the result as a discussion document with AI. Do not blindly refactor everything it lists.

### Suggest Harness Candidates

To find likely places for harnesses:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py suggest-harness
```

The tool uses heuristics such as:

- Core-flow names like `auth`, `login`, `payment`, `permission`, `security`.
- Files changed repeatedly in recent git history.
- Large files.
- Files with many functions.
- Files with TODO/FIXME/HACK markers.

Treat the output as suggestions, not orders.

## What Each File Is For

| File or directory | Purpose |
|---|---|
| `AGENTS.md` | Entry instructions for AI agents. |
| `CLAUDE.md` | Claude-specific project charter. |
| `AI_HANDOFF.md` | Current project state for new AI sessions. |
| `docs/INDEX.md` | Navigation map for specs and ADRs. |
| `docs/guide/ai-behavior.md` | Required AI collaboration rules. |
| `docs/guide/project-meta.md` | Stack, stage, and harness metadata. |
| `docs/adr/` | Architecture Decision Records. |
| `docs/feature/` | Feature specs and stable behavior boundaries. |
| `tests/harness/` | Executable checks for important invariants. |

## Stage Guide

| Stage | What to optimize for | What to avoid |
|---|---|---|
| MVP | Working end-to-end behavior | Heavy docs, broad specs, fake architecture certainty |
| Foundation | Module boundaries, ADRs, project rules | Harnessing everything |
| Iteration | Stable specs, targeted harnesses, safe changes | Letting docs drift from code |

## Good Use Patterns

Good MVP usage:

```bash
ai-sdd init --primary-stack nodejs-ts
```

Then build the project freely until the idea is validated.

Good foundation usage:

```bash
ai-sdd bootstrap-foundation --primary-stack nodejs-ts
ai-sdd review-architecture
ai-sdd add-adr
```

Good iteration usage:

```bash
ai-sdd add-spec
ai-sdd add-harness
ai-sdd status
```

## Common Mistakes

### Mistake: Running `bootstrap-foundation` Too Early

If the product direction is still changing rapidly, stay in MVP. Premature specs become constraints around guesses.

### Mistake: Treating A Generated Harness As Real Coverage

Generated harness files intentionally fail. Replace the placeholder with a real test before counting it.

### Mistake: Writing Specs For Every Thought

A spec is for decisions that are already validated or intentionally locked. If the idea is still a guess, keep it out of specs.

### Mistake: Loading Every Doc Into Every AI Session

The framework is built for selective loading. Read the index, then load only the relevant ADRs and specs.

### Mistake: Letting `AI_HANDOFF.md` Go Stale

Update it before major planning sessions or handoffs. It should reflect current focus, recent decisions, open questions, and next steps.

## Typical Human Prompt Examples

Ask an AI agent:

```text
Use the ai-sdd-bootstrap skill to initialize this project for MVP exploration.
```

```text
The MVP is validated. Use ai-sdd-bootstrap to bootstrap the foundation framework.
```

```text
Use ai-sdd-bootstrap to add an ADR for choosing SQLite as local storage.
```

```text
Use ai-sdd-bootstrap to suggest where this project needs harness tests.
```

```text
Use ai-sdd-bootstrap to add a harness for the login rejection behavior.
```

## Maintenance Checklist

After each meaningful feature:

1. Ask whether any decision is now stable.
2. If yes, add or update a feature spec.
3. Ask whether breaking this behavior would be expensive or hard to notice.
4. If yes, add a real harness.
5. Update `AI_HANDOFF.md` if the project direction, current focus, or open questions changed.
6. Run `status` to see what the project is missing.

## Quick Reference

```bash
# MVP only
ai-sdd init --primary-stack nodejs-ts

# After MVP validation
ai-sdd bootstrap-foundation --primary-stack nodejs-ts

# Inspect current state
ai-sdd status

# Record an architectural decision
ai-sdd add-adr

# Record a stable feature boundary
ai-sdd add-spec

# Generate a draft harness that must be filled in
ai-sdd add-harness

# Produce architecture review notes
ai-sdd review-architecture

# Find likely harness targets
ai-sdd suggest-harness
```
