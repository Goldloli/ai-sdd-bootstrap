# AI SDD Bootstrap — An AI Agent Skill for Staged Engineering

> **This is an AI agent skill / CLI tool.** It provides a staged scaffold for AI-assisted software projects: stay light during MVP exploration, then add Specs, ADRs, and Harnesses only after the architecture stabilizes.
>
> 🇨🇳 [中文版 README](README_zh.md)

AI SDD Bootstrap helps you practice **Spec-Driven Development (SDD)** with AI agents such as Codex, Claude Code, Kimi Code, Cursor, and Copilot. It generates the right amount of structure at the right time, so you don't over-engineer your MVP or lose control during long-term iteration.

## Core Philosophy

- **MVP phase:** Move fast, validate ideas, avoid premature specs.
- **Foundation phase:** After the MVP works, document architecture and project rules.
- **Iteration phase:** Lock stable decisions into specs and executable harnesses.

## When to Use

Use this skill when:

- You are starting a new project with AI assistance.
- The MVP is validated and you want to prevent future AI changes from breaking existing behavior.
- You need a reusable structure for ADRs, feature specs, and harness tests.
- You want Codex, Kimi, Cursor, Claude Code, and Copilot to read the same project rules.

Do **not** bootstrap the full framework for throwaway prototypes. Run `init` only.

## Installation

### Via pip (recommended)

```bash
pip install git+https://github.com/Goldloli/ai-sdd-bootstrap.git
```

After installation you get the `ai-sdd` command:

```bash
ai-sdd --help
```

### Local development install

```bash
git clone https://github.com/Goldloli/ai-sdd-bootstrap.git
cd ai-sdd-bootstrap
pip install -e .
```

### As an AI agent skill

Place this repository in your agent's skill directory, for example:

```bash
~/.agents/skills/ai-sdd-bootstrap
```

Then invoke the wrapper script:

```bash
python3 ~/.agents/skills/ai-sdd-bootstrap/scripts/ai_sdd_bootstrap.py --help
```

The rest of this document uses `ai-sdd`. If you are using the local script, replace `ai-sdd` with the path above.

## Supported Stacks

Choose one primary stack and optionally additional stacks:

- `nodejs-ts`
- `python`
- `rust`
- `go`
- `language-agnostic`
- `shell`

## Recommended Workflow

### 1. Start a New MVP

Run inside your project root:

```bash
ai-sdd init
```

Non-interactive example:

```bash
ai-sdd init --primary-stack nodejs-ts
```

This creates only:

```text
AGENTS.md
README.md
.gitignore
```

It intentionally does **not** create `docs/`, `CLAUDE.md`, `AI_HANDOFF.md`, or harness files. An MVP is still a draft; don't bury it in process.

### 2. Build Freely Until the MVP Is Validated

During the MVP phase:

- Let the AI explore implementation options.
- Keep the codebase small and easy to change.
- Avoid writing many specs.
- Record only decisions that are truly locked.

Signals that you are ready for the next phase:

- You have used the MVP as a real user.
- The product direction is no longer changing every hour.
- You can describe the main modules and boundaries.
- You start worrying that new AI changes will break old behavior.

### 3. Bootstrap the Foundation Framework

After the MVP is validated, run:

```bash
ai-sdd bootstrap-foundation
```

Non-interactive example:

```bash
ai-sdd bootstrap-foundation \
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

From this point on, agents should read `AGENTS.md`, `CLAUDE.md`, `AI_HANDOFF.md`, and `docs/guide/ai-behavior.md` before making substantive changes.

### 4. Check Project Status

At any time run:

```bash
ai-sdd status
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

### Add an ADR

Write an ADR when an architectural decision should not be re-debated in every new AI session.

Interactive:

```bash
ai-sdd add-adr
```

Non-interactive:

```bash
ai-sdd add-adr \
  --title "Use SQLite For Local Storage" \
  --background "The desktop app needs reliable local persistence." \
  --decision "Use SQLite as the local persistence layer." \
  --consequences "Simple local-first storage, but not a multi-user database." \
  --status accepted
```

This creates a file under `docs/adr/` and updates `docs/INDEX.md`.

### Add a Feature Spec

Write a feature spec when a behavior or boundary has stabilized.

Interactive:

```bash
ai-sdd add-spec
```

Non-interactive:

```bash
ai-sdd add-spec \
  --title "Login Flow" \
  --in-scope "Email and password login" \
  --out-scope "Social login, password reset" \
  --boundaries "Do not bypass password verification,Do not mutate user roles during login" \
  --acceptance "Reject wrong password,Create session for valid credentials" \
  --dependencies "ADR-001-use-sqlite-for-local-storage.md"
```

This creates a file under `docs/feature/` and updates `docs/INDEX.md`.

### Add a Harness

Add a harness when a behavior is important enough to enforce with an executable check.

Interactive:

```bash
ai-sdd add-harness
```

Non-interactive:

```bash
ai-sdd add-harness \
  --stack nodejs-ts \
  --title "Login Rejects Wrong Password" \
  --module auth \
  --purpose "Lock the invariant that invalid credentials never create a session." \
  --related-spec docs/feature/login-flow.md \
  --kind test
```

Important: generated harnesses are **draft constraints**. They intentionally fail until you replace the placeholder with real setup, inputs, and assertions. Do not count them as coverage before that.

Output paths:

```text
nodejs-ts -> tests/harness/<module>/<name>.spec.ts
python    -> tests/harness/<module>/test_<name>.py
rust      -> tests/harness/<module>/<name>.rs
go        -> tests/harness/<module>/<name>_test.go
shell     -> tests/harness/<module>/<name>.sh
```

Harness kinds (`--kind`):

- `test` (default) — single-invariant unit harness, one stack per file.
- `evaluation` — fixed task set + scorer + pass threshold, for LLM / agent quality (Python template only).
- `scenario` — full workflow with expected trajectory and forbidden side effects (Python template only).

`--related-spec` writes a `Related spec:` line into the harness header. `status` uses these explicit links (with stem matching as a fallback) to report which specs still lack a hard constraint.

### Review Architecture

After the MVP works, generate an architecture review document:

```bash
ai-sdd review-architecture
```

It scans source files and writes:

```text
docs/guide/architecture-review.md
```

Use the output as discussion material with your AI. Do not blindly refactor everything it lists.

### Suggest Harness Candidates

Find good places to add harnesses:

```bash
ai-sdd suggest-harness
```

Heuristics used:

- Core flow names: `auth`, `login`, `payment`, `permission`, `security`.
- Files modified frequently in recent git history.
- Large files.
- Files with many functions.
- Files marked with TODO/FIXME/HACK.

Treat the output as suggestions, not commands.

Non-interactive usage:

```bash
# Auto-generate a harness for the top candidate (good for AI agent calls)
ai-sdd suggest-harness --top 1

# List candidates without writing files
ai-sdd suggest-harness --dry-run
```

## File Purposes

| File or Directory | Purpose |
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

| Stage | Optimize For | Avoid |
|---|---|---|
| MVP | End-to-end works | Heavy docs, comprehensive specs, fake architectural certainty |
| Foundation | Module boundaries, ADRs, project rules | Putting harnesses on everything |
| Iteration | Stable specs, precise harnesses, safe changes | Docs drifting away from code |

## Good Usage Examples

Good MVP usage:

```bash
ai-sdd init --primary-stack nodejs-ts
```

Then build freely until the idea is validated.

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

### Mistake: Running `bootstrap-foundation` too early

If the product direction is still changing rapidly, stay in the MVP phase. Premature specs become constraints around guesses.

### Mistake: Treating generated harnesses as real coverage

Generated harness files intentionally fail. Replace placeholders with real tests before counting them as coverage.

### Mistake: Writing a spec for every idea

Specs are for validated or intentionally locked decisions. If an idea is still a guess, don't write it into a spec.

### Mistake: Stuffing all docs into every AI session

This framework is designed for on-demand loading. Read the index first, then load only relevant ADRs and specs.

### Mistake: Letting `AI_HANDOFF.md` rot

Update it before important planning sessions or handoffs. It should reflect current focus, recent decisions, open questions, and next steps.

## Typical AI Prompts

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

After completing a meaningful feature:

1. Decide whether any decision has now stabilized.
2. If yes, add or update a feature spec.
3. Decide whether breaking this behavior would be costly or hard to notice.
4. If yes, add a real harness.
5. Update `AI_HANDOFF.md` if project direction, current focus, or open questions changed.
6. Run `status` to see what is still missing.

## Cheat Sheet

```bash
# MVP only
ai-sdd init --primary-stack nodejs-ts

# After MVP validation
ai-sdd bootstrap-foundation --primary-stack nodejs-ts

# Check current state
ai-sdd status

# Record an architectural decision
ai-sdd add-adr

# Record a stable feature boundary
ai-sdd add-spec

# Generate a draft harness that needs real assertions
ai-sdd add-harness

# Generate architecture review notes
ai-sdd review-architecture

# Find good harness candidates
ai-sdd suggest-harness --top 1
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
