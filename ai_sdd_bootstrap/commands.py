#!/usr/bin/env python3
"""Command handlers and harness generators for AI SDD Bootstrap."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from ai_sdd_bootstrap import core
from ai_sdd_bootstrap.core import (
    all_stacks,
    arg_list,
    arg_value,
    ensure_foundation_dirs,
    find_specs_without_harness,
    is_dry_run,
    is_foundation_bootstrapped,
    is_minimally_initialized,
    is_strict,
    load_template,
    next_adr_number,
    prompt,
    prompt_choice,
    prompt_choice_or_arg,
    prompt_multi_or_arg,
    prompt_or_arg,
    read_stack_info,
    read_stage,
    report_created,
    scan_source_files,
    analyze_file,
    git_file_change_counts,
    find_harness_files,
    score_harness_candidate,
    set_dry_run,
    set_strict,
    slugify,
    snake_slug,
    pascal_slug,
    split_items,
    update_index_entry,
    warn_if_pre_foundation,
    write_file,
    _build_status_recommendations,
    _count_draft_harnesses,
    _count_harnesses,
    _parse_index_links,
    print_recommendations,
)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init(args):
    """Create the minimal MVP scaffold. No heavy docs or constraints."""
    if is_minimally_initialized():
        answer = prompt_choice(
            "Project already initialized. Overwrite?",
            ["skip", "update", "overwrite"],
            default="skip",
        )
        if answer == "skip":
            print("Skipping.")
            return
        overwrite = answer == "overwrite"
    else:
        overwrite = False

    stacks = all_stacks()
    primary_stack = prompt_choice_or_arg(args, "primary_stack", "Primary project stack", stacks, default="nodejs-ts")
    additional_stacks = prompt_multi_or_arg(
        args,
        "additional_stack",
        "Additional project stacks",
        [s for s in stacks if s != primary_stack],
    )
    project_name = core.PROJECT_ROOT.name or "project"
    additional_stacks_text = ", ".join(additional_stacks) if additional_stacks else "none"

    files_to_write = {
        core.PROJECT_ROOT / "README.md": (
            load_template("README.mvp.md")
            .replace("{{PROJECT_NAME}}", project_name)
            .replace("{{PRIMARY_STACK}}", primary_stack)
            .replace("{{ADDITIONAL_STACKS}}", additional_stacks_text)
        ),
        core.PROJECT_ROOT / "AGENTS.md": load_template("AGENTS.mvp.md"),
        core.PROJECT_ROOT / ".gitignore": load_template(".gitignore"),
    }

    for path, content in files_to_write.items():
        if path.exists() and not overwrite:
            print(f"Skipping existing file: {path}")
            continue
        write_file(path, content)
        report_created(path)

    stacks_display = primary_stack
    if additional_stacks:
        stacks_display += f" + {', '.join(additional_stacks)}"

    print("\nInitialized MVP scaffold.")
    print(f"Stacks: {stacks_display}, Stage: mvp")
    print("Next: build the MVP freely. When architecture stabilizes, run 'bootstrap-foundation'.")


def _collect_stack_info(args) -> tuple[str, list[str]]:
    """Collect primary and additional stacks, reusing existing info if possible."""
    existing_primary, existing_additional = read_stack_info()
    stacks = all_stacks()

    if existing_primary and existing_primary in stacks:
        default_primary = existing_primary
    else:
        default_primary = "nodejs-ts"

    primary_stack = prompt_choice_or_arg(args, "primary_stack", "Primary project stack", stacks, default=default_primary)

    existing_other = [s for s in existing_additional if s in stacks and s != primary_stack]
    if existing_other:
        print(f"Existing additional stacks: {', '.join(existing_other)}")

    # If no --additional-stack is provided, default to existing stacks from project-meta.md.
    additional_stacks = prompt_multi_or_arg(
        args,
        "additional_stack",
        "Additional project stacks",
        [s for s in stacks if s != primary_stack],
        default=existing_other,
    )

    return primary_stack, additional_stacks


def cmd_bootstrap_foundation(args):
    """Build the full docs/ADR/spec/harness framework after MVP validation."""
    if not is_minimally_initialized():
        print("Project not initialized. Run 'init' first to create the MVP scaffold.")
        return

    if is_foundation_bootstrapped():
        answer = prompt_choice(
            "Foundation framework already exists. Overwrite?",
            ["skip", "update", "overwrite"],
            default="skip",
        )
        if answer == "skip":
            print("Skipping.")
            return
        overwrite = answer == "overwrite"
    else:
        overwrite = False

    primary_stack, additional_stacks = _collect_stack_info(args)
    project_name = core.PROJECT_ROOT.name or "project"
    harness_dir = "tests/harness"
    additional_stacks_text = ", ".join(additional_stacks) if additional_stacks else "none"
    today = datetime.now().strftime("%Y-%m-%d")

    files_to_write = {
        core.PROJECT_ROOT / "docs" / "INDEX.md": load_template("INDEX.md"),
        core.PROJECT_ROOT / "docs" / "guide" / "ai-behavior.md": load_template("ai-behavior.md"),
        core.PROJECT_ROOT / "docs" / "guide" / "project-meta.md": (
            load_template("project-meta.md")
            .replace("{{PRIMARY_STACK}}", primary_stack)
            .replace("{{ADDITIONAL_STACKS}}", additional_stacks_text)
            .replace("{{STAGE}}", "foundation")
            .replace("{{HARNESS_DIR}}", harness_dir)
        ),
        core.PROJECT_ROOT / "docs" / "adr" / ".gitkeep": "",
        core.PROJECT_ROOT / "docs" / "feature" / ".gitkeep": "",
        core.PROJECT_ROOT / "docs" / "examples" / "ADR.example.md": load_template("ADR.example.md"),
        core.PROJECT_ROOT / "docs" / "examples" / "feature-spec.example.md": load_template("feature-spec.example.md"),
        core.PROJECT_ROOT / "CLAUDE.md": load_template("CLAUDE.md"),
        core.PROJECT_ROOT / "AGENTS.md": load_template("AGENTS.md"),
        core.PROJECT_ROOT / "AI_HANDOFF.md": (
            load_template("AI_HANDOFF.md")
            .replace("{{PROJECT_NAME}}", project_name)
            .replace("{{PRIMARY_STACK}}", primary_stack)
            .replace("{{ADDITIONAL_STACKS}}", additional_stacks_text)
            .replace("{{STAGE}}", "foundation")
            .replace("{{DATE}}", today)
        ),
        core.PROJECT_ROOT / "README.md": (
            load_template("README.md").replace("{{PROJECT_NAME}}", project_name)
        ),
    }

    # Always replace MVP versions of AGENTS.md and README.md with foundation versions.
    always_update = {core.PROJECT_ROOT / "AGENTS.md", core.PROJECT_ROOT / "README.md"}

    for path, content in files_to_write.items():
        if path.exists() and not overwrite and path not in always_update:
            print(f"Skipping existing file: {path}")
            continue
        if path.exists() and path in always_update:
            print(f"Updated: {path}")
        else:
            report_created(path)
        write_file(path, content)

    stacks_display = primary_stack
    if additional_stacks:
        stacks_display += f" + {', '.join(additional_stacks)}"

    print("\nBootstrapped foundation SDD framework.")
    print(f"Stacks: {stacks_display}, Stage: foundation")
    print("\nRecommended next steps:")
    print("  1. Review MVP architecture:")
    print("       ai-sdd review-architecture")
    print("  2. Record 2-3 framework-level decisions (DB, framework, auth):")
    print("       ai-sdd add-adr --title \"...\"")
    print("  3. Identify one core flow to lock:")
    print("       ai-sdd suggest-harness --top 1")
    print("  4. Update AI_HANDOFF.md with current focus and open questions.")


def cmd_status(args):
    branch, dirty_files = core.git_info()
    stage = read_stage()
    foundation = is_foundation_bootstrapped()
    initialized = is_minimally_initialized()

    adr_dir = core.PROJECT_ROOT / "docs" / "adr"
    spec_dir = core.PROJECT_ROOT / "docs" / "feature"

    adr_count = len([p for p in adr_dir.glob("ADR-*.md")]) if adr_dir.exists() else 0
    spec_count = len([p for p in spec_dir.glob("*.md")]) if spec_dir.exists() else 0
    harness_count = _count_harnesses()
    draft_harness_count = _count_draft_harnesses()
    missing_harness = find_specs_without_harness() if foundation else []

    recommendations = _build_status_recommendations(
        initialized, foundation, stage, adr_count, harness_count, dirty_files
    )

    if args.json:
        print(
            json.dumps(
                {
                    "initialized": initialized,
                    "foundation_bootstrapped": foundation,
                    "stage": stage,
                    "counts": {
                        "adr": adr_count,
                        "spec": spec_count,
                        "harness": harness_count,
                        "draft_harness": draft_harness_count,
                    },
                    "specs_without_harness": missing_harness,
                    "git": {"branch": branch, "dirty_files": dirty_files},
                    "recommendations": recommendations,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    print("=" * 40)
    print("Project Status")
    print("=" * 40)
    print(f"Initialized: {'yes' if initialized else 'no'}")
    print(f"Foundation bootstrapped: {'yes' if foundation else 'no'}")
    print(f"Stage: {stage}")
    print(f"ADR count: {adr_count}")
    print(f"Feature spec count: {spec_count}")
    print(f"Harness count: {harness_count}")
    print(f"Draft harness count: {draft_harness_count}")
    print(f"Git branch: {branch or 'N/A'}")
    print(f"Uncommitted files: {len(dirty_files)}")
    for f in dirty_files[:10]:
        print(f"  - {f}")
    if len(dirty_files) > 10:
        print(f"  ... and {len(dirty_files) - 10} more")

    print("\nRecommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")


def cmd_add_adr(args):
    title = prompt_or_arg(args, "title", "ADR title")
    if not title:
        print("Title is required.")
        return
    background = prompt_or_arg(args, "background", "Background")
    decision = prompt_or_arg(args, "decision", "Decision")
    consequences = prompt_or_arg(args, "consequences", "Consequences")
    status = prompt_choice_or_arg(args, "status", "Status", ["proposed", "accepted", "deprecated"], default="accepted")

    ensure_foundation_dirs()
    warn_if_pre_foundation("Adding an ADR")

    number = next_adr_number()
    date = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"ADR-{number:03d}-{slug}.md"

    content = (
        load_template("ADR.md")
        .replace("{{TITLE}}", title)
        .replace("{{NUMBER}}", f"ADR-{number:03d}")
        .replace("{{STATUS}}", status)
        .replace("{{DATE}}", date)
    )

    content = content.replace(
        "[What problem or context led to this decision?]",
        background or "[To be completed]",
    )
    content = content.replace(
        "[What did we decide? Be specific.]",
        decision or "[To be completed]",
    )
    content = content.replace(
        "[What tradeoffs, risks, or follow-up work does this create?]",
        consequences or "[To be completed]",
    )

    path = core.PROJECT_ROOT / "docs" / "adr" / filename
    write_file(path, content)
    update_index_entry("Architecture Decisions", path, f"{number:03d} - {title}")
    report_created(path)


def cmd_add_spec(args):
    title = prompt_or_arg(args, "title", "Feature spec title")
    if not title:
        print("Title is required.")
        return
    in_scope = prompt_or_arg(args, "in_scope", "In scope (comma-separated)")
    out_scope = prompt_or_arg(args, "out_scope", "Out of scope (comma-separated)")
    boundaries = prompt_or_arg(args, "boundaries", "Key boundaries (comma-separated)")
    acceptance = prompt_or_arg(args, "acceptance", "Acceptance criteria (comma-separated)")
    dependencies = prompt_or_arg(args, "dependencies", "Dependencies (comma-separated)")

    ensure_foundation_dirs()
    warn_if_pre_foundation("Adding a spec")

    slug = slugify(title)
    filename = f"{slug}.md"

    content = load_template("feature-spec.md").replace("{{TITLE}}", title)

    if in_scope:
        scope_items = "\n".join(f"- {item}" for item in split_items(in_scope))
        content = content.replace("[What this feature does.]", scope_items)
    else:
        content = content.replace("[What this feature does.]", "- [To be completed]")

    if out_scope:
        out_items = "\n".join(f"- {item}" for item in split_items(out_scope))
        content = content.replace("[What this feature explicitly does NOT do.]", out_items)
    else:
        content = content.replace(
            "[What this feature explicitly does NOT do.]", "- [To be completed]"
        )

    if boundaries:
        boundary_items = "\n".join(f"- {b}" for b in split_items(boundaries))
        content = content.replace(
            "- [Rule 1: what AI must not break]\n- [Rule 2: what AI must always do]",
            boundary_items,
        )

    if acceptance:
        criteria_items = "\n".join(f"- [ ] {c}" for c in split_items(acceptance))
        content = content.replace(
            "- [ ] Criterion 1\n- [ ] Criterion 2",
            criteria_items,
        )

    content = content.replace(
        "- [Related ADRs]\n- [Related modules]",
        dependencies or "- [None yet]",
    )

    path = core.PROJECT_ROOT / "docs" / "feature" / filename
    write_file(path, content)
    update_index_entry("Feature Specs", path, title)
    report_created(path)

    # A spec is a soft constraint. Nudge the user toward a hard constraint
    # whenever the boundary matters enough to enforce at test time.
    rel_path = path.relative_to(core.PROJECT_ROOT).as_posix()
    print(
        "Tip: to turn this spec into a hard constraint, run:\n"
        f"  ai-sdd add-harness --title \"{title}\" --related-spec {rel_path}"
    )


def add_harness_nodejs_ts(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = slugify(title)
    filename = f"{slug}.spec.ts"
    harness_dir = core.PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-ts.ts")
        .replace("{{TITLE}}", title)
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    if purpose:
        content = content.replace(
            "[Describe the business boundary or invariant this harness locks.]",
            purpose,
        )
    write_file(harness_dir / filename, content)
    report_created(harness_dir / filename)
    print("Reminder: install vitest and update package.json test scripts if needed.")


def add_harness_python(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = snake_slug(title)
    filename = f"test_{slug}.py"
    harness_dir = core.PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-py.py")
        .replace("{{TITLE}}", title)
        .replace("{{SLUG}}", slug)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    report_created(harness_dir / filename)
    print("Reminder: install pytest and update pyproject.toml or requirements if needed.")


def add_harness_rust(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = snake_slug(title)
    filename = f"{slug}.rs"
    harness_dir = core.PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-rs.rs")
        .replace("{{TITLE}}", title)
        .replace("{{SLUG}}", slug)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    report_created(harness_dir / filename)
    print("Reminder: cargo test will pick up files under tests/.")


def add_harness_shell(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = snake_slug(title)
    filename = f"{slug}.sh"
    harness_dir = core.PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-shell.sh")
        .replace("{{TITLE}}", title)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    if not is_dry_run():
        os.chmod(harness_dir / filename, 0o755)
    report_created(harness_dir / filename)
    print("Reminder: run with `./path/to/harness.sh` or integrate into CI.")


def add_harness_go(title: str, module: str, purpose: str, related_spec: str = ""):
    snake = snake_slug(title)
    # Go convention: test files end with _test.go.
    filename = f"{snake}_test.go"
    harness_dir = core.PROJECT_ROOT / "tests" / "harness" / module
    # Go package names are based on the directory that contains the file.
    # Use the last segment of the module path (e.g. "backend/auth" -> "auth").
    package_name = Path(module).name.replace("-", "_")
    content = (
        load_template("harness-go.go")
        .replace("{{TITLE}}", title)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{PACKAGE}}", package_name)
        .replace("{{PASCAL_SLUG}}", pascal_slug(title))
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    report_created(harness_dir / filename)
    print("Reminder: `go test ./tests/harness/...` will pick up *_test.go automatically.")


HARNESS_KINDS = ["test", "evaluation", "scenario"]


def _fill_py_template(template_name: str, title: str, module: str, purpose: str, related_spec: str, prefix: str = "test_") -> None:
    """Shared filler for python-flavoured harness templates."""
    slug = snake_slug(title)
    filename = f"{prefix}{slug}.py" if prefix else f"{slug}.py"
    harness_dir = core.PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template(template_name)
        .replace("{{TITLE}}", title)
        .replace("{{SLUG}}", slug)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    report_created(harness_dir / filename)
    print("Reminder: install pytest and update pyproject.toml or requirements if needed.")


def add_harness_evaluation(title: str, module: str, purpose: str, related_spec: str = ""):
    """Evaluation harness: fixed task set + scorer + pass threshold."""
    # Only python template exists for now; other stacks should pass --stack shell.
    _fill_py_template("harness-eval-py.py", title, module, purpose, related_spec)
    print("Note: evaluation harness currently ships a python template only.")


def add_harness_scenario(title: str, module: str, purpose: str, related_spec: str = ""):
    """Scenario harness: full workflow with expected trajectory + forbidden effects."""
    _fill_py_template("harness-scenario-py.py", title, module, purpose, related_spec)
    print("Note: scenario harness currently ships a python template only.")


def cmd_add_harness(args):
    meta_path = core.PROJECT_ROOT / "docs" / "guide" / "project-meta.md"
    available_stacks = []
    if meta_path.exists():
        meta = meta_path.read_text(encoding="utf-8")
        primary_match = re.search(r"\*\*Primary stack:\*\*\s*(.+)", meta)
        additional_match = re.search(r"\*\*Additional stacks:\*\*\s*(.+)", meta)
        if primary_match:
            available_stacks.append(primary_match.group(1).strip())
        if additional_match:
            additional = additional_match.group(1).strip()
            if additional != "none":
                available_stacks.extend([s.strip() for s in additional.split(",")])

    if not available_stacks:
        available_stacks = ["nodejs-ts"]

    if "shell" not in available_stacks:
        available_stacks.append("shell")

    stack = prompt_choice_or_arg(
        args,
        "stack",
        "Stack for this harness",
        available_stacks,
        default=available_stacks[0],
    )

    title = prompt_or_arg(args, "title", "Harness title (e.g., 'login flow rejection')")
    if not title:
        print("Title is required.")
        return
    module = prompt_or_arg(args, "module", "Module/subdirectory (e.g., 'auth' or 'backend/auth')", default="core")
    purpose = prompt_or_arg(args, "purpose", "What boundary does this harness lock?")
    related_spec = prompt_or_arg(
        args,
        "related_spec",
        "Related spec path (e.g., 'docs/feature/login-flow.md')",
    )
    if related_spec:
        spec_path = core.PROJECT_ROOT / related_spec
        if not spec_path.exists():
            msg = f"Related spec not found: {related_spec}"
            if is_strict():
                print(f"Error: {msg}")
                sys.exit(1)
            print(f"Warning: {msg}")

    kind = prompt_choice_or_arg(
        args,
        "kind",
        "Harness kind",
        HARNESS_KINDS,
        default="test",
    )

    warn_if_pre_foundation("Adding a harness")

    # evaluation / scenario currently ship python-only templates; route them
    # before the per-stack dispatch so the choice of --kind wins over --stack.
    if kind == "evaluation":
        if stack != "python":
            msg = (
                f"evaluation harnesses currently use a Python template; "
                f"--stack {stack} will be ignored."
            )
            if core.is_strict():
                print(f"Error: {msg}")
                sys.exit(1)
            print(f"Warning: {msg}")
        add_harness_evaluation(title, module, purpose, related_spec)
        return
    if kind == "scenario":
        if stack != "python":
            msg = (
                f"scenario harnesses currently use a Python template; "
                f"--stack {stack} will be ignored."
            )
            if core.is_strict():
                print(f"Error: {msg}")
                sys.exit(1)
            print(f"Warning: {msg}")
        add_harness_scenario(title, module, purpose, related_spec)
        return

    if stack == "nodejs-ts":
        add_harness_nodejs_ts(title, module, purpose, related_spec)
    elif stack == "python":
        add_harness_python(title, module, purpose, related_spec)
    elif stack == "rust":
        add_harness_rust(title, module, purpose, related_spec)
    elif stack == "go":
        add_harness_go(title, module, purpose, related_spec)
    elif stack == "shell":
        add_harness_shell(title, module, purpose, related_spec)
    elif stack == "language-agnostic":
        print("No code harness for language-agnostic stack. Use 'shell' for a generic check.")


def _dispatch_harness_by_ext(ext: str, title: str, module: str, purpose: str, related_spec: str = "") -> None:
    """Pick the right harness generator based on source-file extension."""
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        add_harness_nodejs_ts(title, module, purpose, related_spec)
    elif ext == ".py":
        add_harness_python(title, module, purpose, related_spec)
    elif ext == ".rs":
        add_harness_rust(title, module, purpose, related_spec)
    elif ext == ".go":
        add_harness_go(title, module, purpose, related_spec)
    else:
        add_harness_shell(title, module, purpose, related_spec)


def cmd_suggest_harness(args):
    print("Analyzing project for harness candidates...")
    files = scan_source_files(core.PROJECT_ROOT)
    source_files = [f for f in files if f.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".py", ".rs", ".go"}]

    if not source_files:
        print("No source files found.")
        return

    change_counts = git_file_change_counts()
    harness_stems = find_harness_files()

    candidates = []
    for f in source_files:
        info = analyze_file(f)
        if not info:
            continue
        score, reasons = score_harness_candidate(info, change_counts, harness_stems)
        if score > 0:
            candidates.append((score, info, reasons))

    candidates.sort(key=lambda x: x[0], reverse=True)

    if not candidates:
        print("No strong harness candidates found.")
        return

    top_n = arg_value(args, "top")
    dry_run = bool(getattr(args, "dry_run", False))

    # --top N: non-interactive. Auto-generate harnesses for the top N candidates.
    if top_n:
        try:
            n = max(1, int(top_n))
        except ValueError:
            print(f"Invalid --top value: {top_n}")
            return
        selected = candidates[:n]
        print(f"\nAuto-generating harnesses for top {len(selected)} candidate(s):\n")
        for _, info, reasons in selected:
            print(f"- {info['relative']}  ({', '.join(reasons)})")
            title = f"{info['path'].stem} behavior"
            module = str(info["relative"].parent) if str(info["relative"].parent) != "." else "core"
            purpose = f"Lock behavior of {info['relative']}"
            ext = info["path"].suffix.lower()
            _dispatch_harness_by_ext(ext, title, module, purpose)
        return

    # Default: list top 10 and optionally let the user pick one interactively.
    print("\nTop harness candidates:\n")
    for i, (score, info, reasons) in enumerate(candidates[:10], 1):
        print(f"{i}. {info['relative']}")
        print(f"   Score: {score}")
        print(f"   Reasons: {', '.join(reasons)}")
        print()

    if dry_run:
        return

    choice = prompt("Enter number to generate harness, or press Enter to skip")
    if not choice:
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(candidates[:10]):
            print("Invalid choice.")
            return
    except ValueError:
        print("Invalid choice.")
        return

    _, info, _ = candidates[idx]
    title = prompt("Harness title", default=f"{info['path'].stem} behavior")
    module = prompt("Module/subdirectory", default=str(info["relative"].parent))
    purpose = prompt("What boundary does this harness lock?", default=f"Lock behavior of {info['relative']}")

    ext = info["path"].suffix.lower()
    _dispatch_harness_by_ext(ext, title, module, purpose)


def cmd_validate(args):
    index_path = core.PROJECT_ROOT / "docs" / "INDEX.md"
    broken_links = []
    for text, link in _parse_index_links(index_path):
        # Resolve relative to docs/ directory.
        target = (core.PROJECT_ROOT / "docs" / link).resolve()
        try:
            target.relative_to(core.PROJECT_ROOT)
        except ValueError:
            broken_links.append((text, link, "outside project root"))
            continue
        if not target.exists():
            broken_links.append((text, link, "file not found"))

    draft_count = _count_draft_harnesses()
    missing_harness = find_specs_without_harness()

    primary, additional = read_stack_info()
    stage = read_stage()

    issues = []
    if broken_links:
        issues.append(f"{len(broken_links)} broken INDEX link(s)")
    if draft_count:
        issues.append(f"{draft_count} harness(es) still in draft state")
    if missing_harness:
        issues.append(f"{len(missing_harness)} spec(s) without harness")
    if not is_minimally_initialized():
        issues.append("project not initialized")

    if args.json:
        print(
            json.dumps(
                {
                    "valid": not issues,
                    "stage": stage,
                    "stack": {"primary": primary, "additional": additional},
                    "broken_links": [
                        {"text": t, "link": l, "reason": r}
                        for t, l, r in broken_links
                    ],
                    "draft_harness_count": draft_count,
                    "specs_without_harness": missing_harness,
                    "issues": issues,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    print("=" * 40)
    print("Project Validation")
    print("=" * 40)
    print(f"Stage: {stage}")
    print(f"Primary stack: {primary or 'N/A'}")
    print(f"Additional stacks: {', '.join(additional) if additional else 'none'}")
    print(f"Broken INDEX links: {len(broken_links)}")
    for text, link, reason in broken_links:
        print(f"  - [{text}]({link}): {reason}")
    print(f"Draft harnesses: {draft_count}")
    print(f"Specs without harness: {len(missing_harness)}")
    for spec in missing_harness:
        print(f"  - {spec}")

    if issues:
        print(f"\nFound {len(issues)} issue(s).")
        sys.exit(1)
    else:
        print("\nAll checks passed.")


def cmd_review_architecture(args):
    print("Scanning project architecture...")
    files = scan_source_files(core.PROJECT_ROOT)
    source_files = [f for f in files if f.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".py", ".rs", ".go"}]

    if not source_files:
        print("No source files found to review.")
        return

    analysis = [analyze_file(f) for f in source_files]
    analysis = [a for a in analysis if a]
    analysis.sort(key=lambda x: x["size"], reverse=True)

    importers = {}
    for a in analysis:
        for imp in a["imports"]:
            importers.setdefault(imp, []).append(str(a["relative"]))

    lines = [
        "# Architecture Review",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Overview",
        "",
        f"- Total source files: {len(analysis)}",
    ]
    if analysis:
        lines.append(f"- Largest file: `{analysis[0]['relative']}` ({analysis[0]['lines']} lines)")

    lines.extend([
        "",
        "## Review Questions",
        "",
        "Answer these questions with the AI before making refactoring decisions:",
        "",
        "1. Which modules have unclear responsibilities?",
        "2. Which files are imported by many unrelated modules?",
        "3. Where are there temporary solutions or hacks?",
        "4. Which features should be split into independent modules?",
        "5. Does the dependency direction make sense (high-level → low-level)?",
        "",
        "## Potential Hotspots",
        "",
    ])

    for a in analysis[:10]:
        todos = f", {a['todos']} TODO/FIXME" if a["todos"] else ""
        lines.append(f"- `{a['relative']}` — {a['lines']} lines, {a['func_count']} functions{todos}")

    lines.extend([
        "",
        "## Widely Imported Modules",
        "",
    ])

    for imp, files_list in sorted(importers.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        if len(files_list) >= 3:
            lines.append(f"- `{imp}` — imported by {len(files_list)} files")

    lines.extend([
        "",
        "## Refactoring Candidates",
        "",
        "List modules or files that should be refactored for better coupling/cohesion:",
        "",
        "- [ ] ",
        "",
        "## Decisions to Record",
        "",
        "For each significant architectural choice, create an ADR with `add-adr`.",
    ])

    output_path = core.PROJECT_ROOT / "docs" / "guide" / "architecture-review.md"
    write_file(output_path, "\n".join(lines))
    print(f"Created: {output_path}")
    print("Next: review this file with AI and create ADRs for confirmed decisions.")


__all__ = [
    "cmd_init",
    "cmd_bootstrap_foundation",
    "cmd_status",
    "cmd_add_adr",
    "cmd_add_spec",
    "cmd_add_harness",
    "cmd_review_architecture",
    "cmd_suggest_harness",
    "cmd_validate",
    "add_harness_nodejs_ts",
    "add_harness_python",
    "add_harness_rust",
    "add_harness_go",
    "add_harness_shell",
    "add_harness_evaluation",
    "add_harness_scenario",
    "HARNESS_KINDS",
]
