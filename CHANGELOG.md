# Changelog

All notable changes to this project will be documented in this file.

## [0.3.1] - 2026-06-26

### Fixed
- Add missing `import re` in `commands.py` that broke `add-harness` after `bootstrap-foundation`.
- Include dotfiles in package data so `templates/.gitignore` is present in non-editable installs.
- Update CONTRIBUTING.md to point to `core.py` for `all_stacks()`.
- `--strict` now errors on `evaluation` / `scenario` harness with non-Python stack.

## [0.3.0] - 2026-06-26

### Added
- CJK title support: romanize Chinese titles via optional `pypinyin` dependency.
- `--dry-run` flag for `init`, `bootstrap-foundation`, `add-adr`, `add-spec`, `add-harness`, `review-architecture`.
- `--strict` flag: fail instead of prompting or silently using defaults.
- `status --json`: machine-readable project status output.
- `validate` command with `--json` output: checks INDEX links, draft harnesses, and specs without harnesses.
- Validation of `--related-spec` path existence when adding a harness.
- pytest + coverage baseline; CI now runs pytest.

### Changed
- Split monolithic `cli.py` into `core.py`, `commands.py`, and `cli.py`.
- `add-spec` now splits `in_scope` and `out_scope` into bullet lists.

### Fixed
- Python 3.9 compatibility (`from __future__ import annotations`).
- Go harness package name now matches the target directory instead of the title slug.
- AGENTS.mvp.md Chinese typo (`建低级` -> `foundation`).
- Removed ambiguous `bootstrap` from `init` natural-language mapping in SKILL.md.

## [0.2.0] - 2026-06-26

### Added
- Staged workflow: `init` for MVP, `bootstrap-foundation` for full framework.
- Support for `go` stack harness generation.
- Harness kinds: `test` (default), `evaluation`, `scenario`.
- `--related-spec` flag to link harnesses with specs.
- Non-interactive `suggest-harness` with `--top` and `--dry-run`.
- Automatic update of `docs/INDEX.md` when adding ADRs or specs.
- CLI flags for all interactive commands.
- Pip-installable package structure.
- GitHub Actions CI workflow.

## [0.1.0] - 2026-06-26

### Added
- Initial skill scaffold with `init`, `status`, `add-adr`, `add-spec`, `add-harness`.
- Support for `nodejs-ts`, `python`, `rust`, `shell` stacks.
- `review-architecture` and `suggest-harness` helpers.
