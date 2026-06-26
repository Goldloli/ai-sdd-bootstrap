#!/usr/bin/env python3
"""AI SDD Bootstrap — argparse setup and main entry point.

Philosophy:
- 0 -> 1 (MVP): minimal scaffold, let AI explore freely.
- 1 -> 3 (Foundation): bootstrap full docs/ADR/spec/harness framework once architecture stabilizes.
- 3 -> 10 (Iteration): keep adding specs and harnesses as the project grows.
"""

from __future__ import annotations

import argparse

# Re-export core utilities and command functions for backwards compatibility.
from ai_sdd_bootstrap.core import (
    PROJECT_ROOT,
    all_stacks,
    find_specs_without_harness,
    is_dry_run,
    is_strict,
    set_dry_run,
    set_project_root,
    set_strict,
    slugify,
)
from ai_sdd_bootstrap.commands import (
    HARNESS_KINDS,
    add_harness_evaluation,
    add_harness_go,
    add_harness_nodejs_ts,
    add_harness_python,
    add_harness_rust,
    add_harness_scenario,
    add_harness_shell,
    cmd_add_adr,
    cmd_add_harness,
    cmd_add_spec,
    cmd_bootstrap_foundation,
    cmd_init,
    cmd_review_architecture,
    cmd_status,
    cmd_suggest_harness,
    cmd_validate,
)


def main():
    parser = argparse.ArgumentParser(description="AI SDD Bootstrap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_dry_run(parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing files.",
        )

    def add_strict(parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Fail instead of prompting or silently using defaults.",
        )

    init_parser = subparsers.add_parser("init", help="Initialize minimal MVP scaffold")
    init_parser.add_argument("--primary-stack", choices=all_stacks())
    init_parser.add_argument("--additional-stack", action="append", help="Additional stack. Can be repeated or comma-separated.")
    add_dry_run(init_parser)
    add_strict(init_parser)

    foundation_parser = subparsers.add_parser(
        "bootstrap-foundation",
        help="Bootstrap full docs/ADR/spec/harness framework after MVP validation",
    )
    foundation_parser.add_argument("--primary-stack", choices=all_stacks())
    foundation_parser.add_argument("--additional-stack", action="append", help="Additional stack. Can be repeated or comma-separated.")
    add_dry_run(foundation_parser)
    add_strict(foundation_parser)

    status_parser = subparsers.add_parser("status", help="Show project status and recommendations")
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of human text.",
    )

    adr_parser = subparsers.add_parser("add-adr", help="Add an architecture decision record")
    adr_parser.add_argument("--title")
    adr_parser.add_argument("--background")
    adr_parser.add_argument("--decision")
    adr_parser.add_argument("--consequences")
    adr_parser.add_argument("--status", choices=["proposed", "accepted", "deprecated"])
    add_dry_run(adr_parser)
    add_strict(adr_parser)

    spec_parser = subparsers.add_parser("add-spec", help="Add a feature spec")
    spec_parser.add_argument("--title")
    spec_parser.add_argument("--in-scope")
    spec_parser.add_argument("--out-scope")
    spec_parser.add_argument("--boundaries")
    spec_parser.add_argument("--acceptance")
    spec_parser.add_argument("--dependencies")
    add_dry_run(spec_parser)
    add_strict(spec_parser)

    harness_parser = subparsers.add_parser("add-harness", help="Add a harness skeleton")
    harness_parser.add_argument("--stack")
    harness_parser.add_argument("--title")
    harness_parser.add_argument("--module")
    harness_parser.add_argument("--purpose")
    harness_parser.add_argument(
        "--related-spec",
        help="Path of the spec this harness locks (e.g. docs/feature/login-flow.md).",
    )
    harness_parser.add_argument(
        "--kind",
        choices=HARNESS_KINDS,
        help="Harness kind: test (unit invariant, default), evaluation (task set + "
        "scorer, for LLM/agent quality), scenario (full workflow trajectory).",
    )
    add_dry_run(harness_parser)
    add_strict(harness_parser)

    review_parser = subparsers.add_parser("review-architecture", help="Generate architecture review doc")
    add_dry_run(review_parser)
    add_strict(review_parser)

    validate_parser = subparsers.add_parser("validate", help="Check project health and consistency")
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of human text.",
    )
    suggest_parser = subparsers.add_parser("suggest-harness", help="Suggest harness candidates")
    suggest_parser.add_argument(
        "--top",
        help="Non-interactive: auto-generate harnesses for the top N candidates.",
    )
    suggest_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list candidates, do not prompt or generate harness files.",
    )
    add_strict(suggest_parser)

    args = parser.parse_args()
    set_dry_run(bool(getattr(args, "dry_run", False)))
    set_strict(bool(getattr(args, "strict", False)))

    commands = {
        "init": cmd_init,
        "bootstrap-foundation": cmd_bootstrap_foundation,
        "status": cmd_status,
        "add-adr": cmd_add_adr,
        "add-spec": cmd_add_spec,
        "add-harness": cmd_add_harness,
        "review-architecture": cmd_review_architecture,
        "suggest-harness": cmd_suggest_harness,
        "validate": cmd_validate,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
