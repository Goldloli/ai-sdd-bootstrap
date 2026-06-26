# AGENTS.md

**Status:** MVP stage. Keep instructions minimal and avoid premature constraints.

## Current Goal

This project is in MVP/exploration phase. Focus on validating ideas and getting something working end-to-end.

## Rules for MVP

1. **Explore freely.** Do not over-engineer or add speculative abstractions.
2. **Prefer working code over perfect code.** Code quality requirements are near-zero at this stage.
3. **Avoid writing specs or ADRs unless a decision is truly locked.** Most guesses will change.
4. **Keep the project small and hackable.** The MVP is a draft, not a foundation.
5. **When the MVP is validated and architecture stabilizes, run `bootstrap-foundation` to build the full SDD scaffold.**

## Transition to Foundation

When the user indicates the MVP is validated and wants to build the full engineering framework (e.g., "建立更详细的 ADR 和 Harness 框架", "进入建低级阶段", "完善工程化框架"), invoke the `ai-sdd-bootstrap` skill with `bootstrap-foundation`.

## Handoff

When passing this project to another AI, summarize:
- What was built so far
- What is being validated
- What the next experiment is
