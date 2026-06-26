# AI Behavior Guide

**Status:** Required reading before every AI-assisted task.

This document defines how AI assistants collaborate on this project. Read it fully before planning, implementing, or refactoring.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

## 5. Spec-Driven Development (SDD)

This project uses SDD to prevent AI from silently breaking existing behavior as the project grows.

### 5.1 Spec = Decisions That Won't Change

A spec records decisions you have already made and do not want to re-debate. It is not a design document written upfront.

> **MVP is a draft written in code. Spec is editing that draft with a red pen.**
> Only code that has actually run and been validated deserves to be locked into a spec.

> **Spec is a time machine.** Its only job is to communicate with your future self and the next AI that joins the project.

Write a spec only when:
- A decision has been tested and validated through actual usage
- The same question has come up more than once
- A boundary is important enough that AI should not guess

**When to write a spec:** After a feature passes acceptance, not before. The real end of a feature is recording the reusable judgments it produced.

### 5.2 Spec Is a Soft Constraint

Specs are written in natural language. AI may still miss or misapply them when context is long. Treat specs as strong guidance, not guarantees.

### 5.3 Harness = Hard Constraint

Harnesses are executable tests that verify business logic. If a harness fails, the change is objectively wrong.

Use harnesses for:
- Existing features that AI frequently breaks
- Core flows (auth, payment, permissions, data persistence)
- Areas where the same bug has appeared multiple times
- Logic where failures are hard to trace

Start harnesses as simple scripts. A harness does not need to be a full test suite on day one.

### 5.4 ADR = Architecture Decision Record

Every significant architectural choice (framework, data store, API style, module boundary) gets an ADR in `docs/adr/`.

### 5.5 Why SDD Matters

Locking decisions into specs and harnesses makes the project:

- **Auditable** — specs are versioned alongside code; you can trace which spec produced which behavior
- **Handoff-able** — new contributors read specs instead of reconstructing chat history
- **Reusable** — specs and harnesses transfer to future projects

### 5.6 Project Stages

This project recognizes three stages:

1. **MVP (0 → 1)** — Validate ideas with working code. Write almost no specs. Let AI explore.
2. **Foundation (1 → 3)** — Review MVP architecture, modularize, decouple, add key ADRs. Add only a few harnesses for the most critical boundaries.
3. **Iteration (3 → 10)** — Add feature specs and harnesses as the project stabilizes. Keep recording decisions.

## 6. Document Writing Standards

When creating or updating project documents, follow these exact formats.

### 6.1 ADR Format

File: `docs/adr/ADR-NNN-<short-title>.md`

Required sections:
1. **Background** — What problem are we solving?
2. **Decision** — What did we choose?
3. **Consequences** — What tradeoffs does this create?
4. **Status** — `proposed` | `accepted` | `deprecated`

### 6.2 Feature Spec Format

File: `docs/feature/<feature-name>.md`

Required sections:
1. **Scope** — What this feature does and explicitly does NOT do
2. **Boundaries** — Rules AI must not break
3. **Acceptance Criteria** — How to verify completion
4. **Dependencies** — Related ADRs or modules

### 6.3 Harness Format

File: `tests/harness/<module>/<name>.spec.ts` (or stack-specific path)

Required parts:
1. **Purpose** — What behavior is being locked
2. **Inputs / Preconditions**
3. **Assertions** — Expected outputs

## 7. How to Read Project Docs

1. Read this file first.
2. For a new task, read `docs/INDEX.md` next.
3. Load only the ADRs and specs relevant to the current task.
4. Do not load all documents at once.
