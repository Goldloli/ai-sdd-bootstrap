# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-06-26

### Added
- Staged workflow: `init` for MVP, `bootstrap-foundation` for full framework.
- Support for `go` stack harness generation.
- Harness kinds: `test` (default), `evaluation`, `scenario`.
- `--related-spec` flag to link harnesses with specs.
- Non-interactive `suggest-harness` with `--top` and `--dry-run`.
- Automatic update of `docs/INDEX.md` when adding ADRs or specs.
- CLI flags for all interactive commands.
- 14 unit tests.
- Pip-installable package structure.
- GitHub Actions CI workflow.

## [0.1.0] - 2026-06-26

### Added
- Initial skill scaffold with `init`, `status`, `add-adr`, `add-spec`, `add-harness`.
- Support for `nodejs-ts`, `python`, `rust`, `shell` stacks.
- `review-architecture` and `suggest-harness` helpers.
