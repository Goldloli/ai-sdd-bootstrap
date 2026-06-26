#!/usr/bin/env python3
"""AI SDD Bootstrap — staged scaffold for AI-engineering projects.

Philosophy:
- 0 -> 1 (MVP): minimal scaffold, let AI explore freely.
- 1 -> 3 (Foundation): bootstrap full docs/ADR/spec/harness framework once architecture stabilizes.
- 3 -> 10 (Iteration): keep adding specs and harnesses as the project grows.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
PROJECT_ROOT = Path.cwd()


def load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def prompt(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{suffix}: ").strip()
    except EOFError:
        print(f" (non-interactive, using default: {default!r})")
        return default
    return answer if answer else default


def prompt_choice(question: str, choices: list[str], default: str = "") -> str:
    while True:
        options = "/".join(choices)
        suffix = f" [{default}]" if default else ""
        try:
            answer = input(f"{question} ({options}){suffix}: ").strip()
        except EOFError:
            print(f" (non-interactive, using default: {default!r})")
            return default if default in choices else choices[0]
        if not answer and default:
            return default
        if answer in choices:
            return answer
        print(f"Please choose one of: {', '.join(choices)}")


def prompt_multi(question: str, choices: list[str], default: list[str] | None = None) -> list[str]:
    print(f"{question} (comma-separated, e.g., {', '.join(choices)})")
    try:
        answer = input("Enter choices or leave empty for none: ").strip()
    except EOFError:
        default = default or []
        print(f" (non-interactive, using default: {default!r})")
        return default
    if not answer:
        return default or []
    selected = [s.strip() for s in answer.split(",")]
    valid = [s for s in selected if s in choices]
    invalid = [s for s in selected if s not in choices]
    if invalid:
        print(f"Ignoring invalid choices: {', '.join(invalid)}")
    return valid


def all_stacks() -> list[str]:
    return ["nodejs-ts", "python", "rust", "go", "language-agnostic", "shell"]


def arg_value(args, name: str, default: str = "") -> str:
    value = getattr(args, name, None)
    return value if value is not None else default


def arg_list(args, name: str) -> list[str]:
    value = getattr(args, name, None)
    if not value:
        return []
    if isinstance(value, list):
        raw = []
        for item in value:
            raw.extend(str(item).split(","))
    else:
        raw = str(value).split(",")
    return [item.strip() for item in raw if item.strip()]


def prompt_or_arg(args, name: str, question: str, default: str = "") -> str:
    value = arg_value(args, name)
    if value:
        return value
    return prompt(question, default=default)


def prompt_choice_or_arg(args, name: str, question: str, choices: list[str], default: str = "") -> str:
    value = arg_value(args, name)
    if value:
        if value not in choices:
            print(f"Invalid {name}: {value}. Expected one of: {', '.join(choices)}")
            return default if default in choices else choices[0]
        return value
    return prompt_choice(question, choices, default=default)


def prompt_multi_or_arg(args, name: str, question: str, choices: list[str], default: list[str] | None = None) -> list[str]:
    values = arg_list(args, name)
    if values:
        invalid = [value for value in values if value not in choices]
        if invalid:
            print(f"Ignoring invalid {name}: {', '.join(invalid)}")
        return [value for value in values if value in choices]
    return prompt_multi(question, choices, default=default)


def split_items(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def update_index_entry(section: str, rel_path: Path, title: str) -> None:
    index_path = PROJECT_ROOT / "docs" / "INDEX.md"
    if not index_path.exists():
        return

    try:
        link_path = rel_path.relative_to(PROJECT_ROOT / "docs")
    except ValueError:
        link_path = rel_path.relative_to(PROJECT_ROOT)

    link = f"./{link_path.as_posix()}"
    entry = f"- [{title}]({link})"
    content = index_path.read_text(encoding="utf-8")
    if link in content:
        return

    heading = f"## {section}"
    if heading not in content:
        if content and not content.endswith("\n"):
            content += "\n"
        content += f"\n{heading}\n\n{entry}\n"
    else:
        lines = content.splitlines()
        heading_idx = lines.index(heading)
        insert_idx = len(lines)
        for idx in range(heading_idx + 1, len(lines)):
            if lines[idx].startswith("## "):
                insert_idx = idx
                break
        while insert_idx > heading_idx + 1 and lines[insert_idx - 1] == "":
            insert_idx -= 1
        lines.insert(insert_idx, entry)
        content = "\n".join(lines) + "\n"

    index_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Project state detection
# ---------------------------------------------------------------------------


def is_minimally_initialized() -> bool:
    """True if `init` has been run (MVP scaffold exists)."""
    return (PROJECT_ROOT / "AGENTS.md").exists()


def is_foundation_bootstrapped() -> bool:
    """True if the full SDD framework has been bootstrapped."""
    return (
        (PROJECT_ROOT / "docs" / "guide" / "ai-behavior.md").exists()
        and (PROJECT_ROOT / "docs" / "adr").exists()
        and (PROJECT_ROOT / "docs" / "feature").exists()
        and (PROJECT_ROOT / "AI_HANDOFF.md").exists()
        and (PROJECT_ROOT / "CLAUDE.md").exists()
    )


def read_stage() -> str:
    meta_path = PROJECT_ROOT / "docs" / "guide" / "project-meta.md"
    if meta_path.exists():
        meta = meta_path.read_text(encoding="utf-8")
        stage_match = re.search(r"\*\*Stage:\*\*\s*(mvp|foundation|iteration)", meta)
        return stage_match.group(1).strip() if stage_match else "mvp"
    return "mvp"


def read_stack_info() -> tuple[str, list[str]]:
    """Try to read stack info from project-meta.md or the MVP README.md."""
    primary = ""
    additional = []

    meta_path = PROJECT_ROOT / "docs" / "guide" / "project-meta.md"
    if meta_path.exists():
        meta = meta_path.read_text(encoding="utf-8")
        pm = re.search(r"\*\*Primary stack:\*\*\s*(.+)", meta)
        am = re.search(r"\*\*Additional stacks:\*\*\s*(.+)", meta)
        if pm:
            primary = pm.group(1).strip()
        if am:
            raw = am.group(1).strip()
            if raw and raw != "none":
                additional = [s.strip() for s in raw.split(",")]
        return primary, additional

    # Fallback: parse the MVP README.md created by `init`.
    readme_path = PROJECT_ROOT / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        pm = re.search(r"\*\*Primary:\*\*\s*(.+)", readme)
        am = re.search(r"\*\*Additional:\*\*\s*(.+)", readme)
        if pm:
            primary = pm.group(1).strip()
        if am:
            raw = am.group(1).strip()
            if raw and raw != "none":
                additional = [s.strip() for s in raw.split(",")]
    return primary, additional


def git_info():
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        branch = None

    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        dirty_files = [line.split()[-1] for line in status.splitlines() if line]
    except Exception:
        dirty_files = []

    return branch, dirty_files


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
    project_name = PROJECT_ROOT.name or "project"
    additional_stacks_text = ", ".join(additional_stacks) if additional_stacks else "none"

    files_to_write = {
        PROJECT_ROOT / "README.md": (
            load_template("README.mvp.md")
            .replace("{{PROJECT_NAME}}", project_name)
            .replace("{{PRIMARY_STACK}}", primary_stack)
            .replace("{{ADDITIONAL_STACKS}}", additional_stacks_text)
        ),
        PROJECT_ROOT / "AGENTS.md": load_template("AGENTS.mvp.md"),
        PROJECT_ROOT / ".gitignore": load_template(".gitignore"),
    }

    for path, content in files_to_write.items():
        if path.exists() and not overwrite:
            print(f"Skipping existing file: {path}")
            continue
        write_file(path, content)
        print(f"Created: {path}")

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
    project_name = PROJECT_ROOT.name or "project"
    harness_dir = "tests/harness"
    additional_stacks_text = ", ".join(additional_stacks) if additional_stacks else "none"
    today = datetime.now().strftime("%Y-%m-%d")

    files_to_write = {
        PROJECT_ROOT / "docs" / "INDEX.md": load_template("INDEX.md"),
        PROJECT_ROOT / "docs" / "guide" / "ai-behavior.md": load_template("ai-behavior.md"),
        PROJECT_ROOT / "docs" / "guide" / "project-meta.md": (
            load_template("project-meta.md")
            .replace("{{PRIMARY_STACK}}", primary_stack)
            .replace("{{ADDITIONAL_STACKS}}", additional_stacks_text)
            .replace("{{STAGE}}", "foundation")
            .replace("{{HARNESS_DIR}}", harness_dir)
        ),
        PROJECT_ROOT / "docs" / "adr" / ".gitkeep": "",
        PROJECT_ROOT / "docs" / "feature" / ".gitkeep": "",
        PROJECT_ROOT / "docs" / "examples" / "ADR.example.md": load_template("ADR.example.md"),
        PROJECT_ROOT / "docs" / "examples" / "feature-spec.example.md": load_template("feature-spec.example.md"),
        PROJECT_ROOT / "CLAUDE.md": load_template("CLAUDE.md"),
        PROJECT_ROOT / "AGENTS.md": load_template("AGENTS.md"),
        PROJECT_ROOT / "AI_HANDOFF.md": (
            load_template("AI_HANDOFF.md")
            .replace("{{PROJECT_NAME}}", project_name)
            .replace("{{PRIMARY_STACK}}", primary_stack)
            .replace("{{ADDITIONAL_STACKS}}", additional_stacks_text)
            .replace("{{STAGE}}", "foundation")
            .replace("{{DATE}}", today)
        ),
        PROJECT_ROOT / "README.md": (
            load_template("README.md").replace("{{PROJECT_NAME}}", project_name)
        ),
    }

    # Always replace MVP versions of AGENTS.md and README.md with foundation versions.
    always_update = {PROJECT_ROOT / "AGENTS.md", PROJECT_ROOT / "README.md"}

    for path, content in files_to_write.items():
        if path.exists() and not overwrite and path not in always_update:
            print(f"Skipping existing file: {path}")
            continue
        if path.exists() and path in always_update:
            print(f"Updated: {path}")
        else:
            print(f"Created: {path}")
        write_file(path, content)

    stacks_display = primary_stack
    if additional_stacks:
        stacks_display += f" + {', '.join(additional_stacks)}"

    print("\nBootstrapped foundation SDD framework.")
    print(f"Stacks: {stacks_display}, Stage: foundation")
    print("Next: run 'review-architecture' with AI, then start adding ADRs and harnesses.")


def cmd_status(args):
    branch, dirty_files = git_info()
    stage = read_stage()
    foundation = is_foundation_bootstrapped()

    adr_dir = PROJECT_ROOT / "docs" / "adr"
    spec_dir = PROJECT_ROOT / "docs" / "feature"
    harness_dir = PROJECT_ROOT / "tests" / "harness"

    adr_count = len([p for p in adr_dir.glob("ADR-*.md")]) if adr_dir.exists() else 0
    spec_count = len([p for p in spec_dir.glob("*.md")]) if spec_dir.exists() else 0
    harness_count = 0
    if harness_dir.exists():
        harness_count += len(list(harness_dir.rglob("*.spec.ts")))
        harness_count += len(list(harness_dir.rglob("test_*.py")))
        harness_count += len(list(harness_dir.rglob("*.rs")))
        harness_count += len(list(harness_dir.rglob("*_test.go")))
        harness_count += len(list(harness_dir.rglob("*.sh")))

    print("=" * 40)
    print("Project Status")
    print("=" * 40)
    print(f"Initialized: {'yes' if is_minimally_initialized() else 'no'}")
    print(f"Foundation bootstrapped: {'yes' if foundation else 'no'}")
    print(f"Stage: {stage}")
    print(f"ADR count: {adr_count}")
    print(f"Feature spec count: {spec_count}")
    print(f"Harness count: {harness_count}")
    print(f"Git branch: {branch or 'N/A'}")
    print(f"Uncommitted files: {len(dirty_files)}")
    for f in dirty_files[:10]:
        print(f"  - {f}")
    if len(dirty_files) > 10:
        print(f"  ... and {len(dirty_files) - 10} more")

    print("\nRecommendations:")
    recommendations = []

    if not is_minimally_initialized():
        recommendations.append("Run 'init' to set up the minimal MVP scaffold.")
        print_recommendations(recommendations)
        return

    if not foundation:
        # MVP stage guidance
        recommendations.append("MVP stage: focus on validating ideas. Avoid specs, ADRs, and heavy architecture decisions.")
        recommendations.append("Let AI explore freely. Code quality expectations are low.")
        if dirty_files:
            recommendations.append("Keep iterating. When the MVP feels solid and architecture stabilizes, run 'bootstrap-foundation'.")
        else:
            recommendations.append("No active changes. Good time to experiment or validate the next assumption.")
    else:
        # Foundation / iteration stage guidance
        if stage == "foundation":
            recommendations.append("Foundation stage: modularize MVP architecture and lock key decisions into ADRs.")
            recommendations.append("Run 'review-architecture' to audit the current structure.")
            if adr_count == 0:
                recommendations.append("No ADRs yet. Start recording framework, data model, and module boundary decisions.")
        else:
            # iteration
            if adr_count == 0:
                recommendations.append("Iteration stage: review architecture and add key ADRs first.")
            if harness_count == 0:
                recommendations.append("No harnesses yet. Identify one core flow or frequently-broken feature to lock down.")
            missing_harness = find_specs_without_harness()
            if missing_harness:
                specs_list = ", ".join(missing_harness[:3])
                suffix = f" and {len(missing_harness) - 3} more" if len(missing_harness) > 3 else ""
                recommendations.append(f"Specs without harness: {specs_list}{suffix}. Consider adding harnesses to enforce boundaries.")

        if dirty_files:
            core_patterns = ["auth", "login", "payment", "permission", "security"]
            core_changed = any(
                any(p in f.lower() for p in core_patterns)
                for f in dirty_files
            )
            if core_changed:
                recommendations.append("Core flow changed. Consider 'add-harness' after locking the spec.")
            else:
                recommendations.append("Uncommitted changes detected. Consider 'add-spec' if this feature is stabilizing.")
        else:
            recommendations.append("No active changes. Good time to review docs/adr/ and docs/feature/ for gaps.")

    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")


def print_recommendations(recommendations: list[str]):
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")


def next_adr_number() -> int:
    numbers = []
    adr_dir = PROJECT_ROOT / "docs" / "adr"
    if adr_dir.exists():
        for p in adr_dir.glob("ADR-*.md"):
            m = re.match(r"ADR-(\d+)", p.name)
            if m:
                numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1


def slugify(title: str) -> str:
    return re.sub(r"[^\w]+", "-", title).strip("-").lower()


def ensure_foundation_dirs():
    """Create docs dirs if they don't exist (so add-adr/add-spec still work pre-foundation)."""
    (PROJECT_ROOT / "docs" / "adr").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "docs" / "feature").mkdir(parents=True, exist_ok=True)


def warn_if_pre_foundation(action: str):
    if not is_foundation_bootstrapped():
        print(f"Note: foundation framework not yet bootstrapped. {action} now creates an isolated doc.")
        print("Run 'bootstrap-foundation' when you are ready to build the full SDD scaffold.\n")


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

    path = PROJECT_ROOT / "docs" / "adr" / filename
    write_file(path, content)
    update_index_entry("Architecture Decisions", path, f"{number:03d} - {title}")
    print(f"Created: {path}")


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

    content = content.replace(
        "[What this feature does.]",
        in_scope or "[To be completed]",
    )
    content = content.replace(
        "[What this feature explicitly does NOT do.]",
        out_scope or "[To be completed]",
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

    path = PROJECT_ROOT / "docs" / "feature" / filename
    write_file(path, content)
    update_index_entry("Feature Specs", path, title)
    print(f"Created: {path}")

    # A spec is a soft constraint. Nudge the user toward a hard constraint
    # whenever the boundary matters enough to enforce at test time.
    rel_path = path.relative_to(PROJECT_ROOT).as_posix()
    print(
        "Tip: to turn this spec into a hard constraint, run:\n"
        f"  ai-sdd add-harness --title \"{title}\" --related-spec {rel_path}"
    )


def snake_slug(title: str) -> str:
    return slugify(title).replace("-", "_")


def add_harness_nodejs_ts(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = slugify(title)
    filename = f"{slug}.spec.ts"
    harness_dir = PROJECT_ROOT / "tests" / "harness" / module
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
    print(f"Created: {harness_dir / filename}")
    print("Reminder: install vitest and update package.json test scripts if needed.")


def add_harness_python(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = snake_slug(title)
    filename = f"test_{slug}.py"
    harness_dir = PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-py.py")
        .replace("{{TITLE}}", title)
        .replace("{{SLUG}}", slug)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    print(f"Created: {harness_dir / filename}")
    print("Reminder: install pytest and update pyproject.toml or requirements if needed.")


def add_harness_rust(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = snake_slug(title)
    filename = f"{slug}.rs"
    harness_dir = PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-rs.rs")
        .replace("{{TITLE}}", title)
        .replace("{{SLUG}}", slug)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    print(f"Created: {harness_dir / filename}")
    print("Reminder: cargo test will pick up files under tests/.")


def add_harness_shell(title: str, module: str, purpose: str, related_spec: str = ""):
    slug = snake_slug(title)
    filename = f"{slug}.sh"
    harness_dir = PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-shell.sh")
        .replace("{{TITLE}}", title)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    os.chmod(harness_dir / filename, 0o755)
    print(f"Created: {harness_dir / filename}")
    print("Reminder: run with `./path/to/harness.sh` or integrate into CI.")


def pascal_slug(title: str) -> str:
    """Convert a title to PascalCase for Go exported identifiers."""
    parts = re.split(r"[^\w]+", title)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def add_harness_go(title: str, module: str, purpose: str, related_spec: str = ""):
    snake = snake_slug(title)
    # Go convention: test files end with _test.go.
    filename = f"{snake}_test.go"
    harness_dir = PROJECT_ROOT / "tests" / "harness" / module
    content = (
        load_template("harness-go.go")
        .replace("{{TITLE}}", title)
        .replace("{{PURPOSE}}", purpose or "[To be completed]")
        .replace("{{SLUG}}", snake)
        .replace("{{PASCAL_SLUG}}", pascal_slug(title))
        .replace("{{RELATED_SPEC}}", related_spec or "[none]")
    )
    write_file(harness_dir / filename, content)
    print(f"Created: {harness_dir / filename}")
    print("Reminder: `go test ./tests/harness/...` will pick up *_test.go automatically.")


def cmd_add_harness(args):
    meta_path = PROJECT_ROOT / "docs" / "guide" / "project-meta.md"
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

    warn_if_pre_foundation("Adding a harness")

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


# Architecture review and harness suggestion helpers

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "target",
    "dist", "build", ".next", ".cache", "coverage", ".pytest_cache",
    "tests", "test",
}
IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mp3", ".pdf", ".zip", ".tar", ".gz",
    ".bin", ".exe", ".dll", ".so", ".dylib",
}
MAX_FILE_SIZE = 500_000  # 500 KB


def should_ignore_path(path: Path) -> bool:
    parts = set(path.parts)
    if parts & IGNORED_DIRS:
        return True
    if path.suffix.lower() in IGNORED_EXTENSIONS:
        return True
    if path.is_file() and path.stat().st_size > MAX_FILE_SIZE:
        return True
    return False


def scan_source_files(root: Path) -> list[Path]:
    files = []
    try:
        for p in root.rglob("*"):
            if p.is_file() and not should_ignore_path(p):
                files.append(p)
    except PermissionError:
        pass
    return files


def analyze_file(path: Path) -> dict:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}

    lines = content.splitlines()
    size = len(content)
    ext = path.suffix.lower()

    func_count = 0
    class_count = 0
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        func_count = len(re.findall(r"\bfunction\s+\w+\s*\(", content))
        func_count += len(re.findall(r"\bconst\s+\w+\s*=\s*\([^)]*\)\s*=>", content))
        class_count = len(re.findall(r"\bclass\s+\w+", content))
    elif ext == ".py":
        func_count = len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
        class_count = len(re.findall(r"^\s*class\s+\w+", content, re.MULTILINE))
    elif ext == ".rs":
        func_count = len(re.findall(r"^\s*fn\s+\w+", content, re.MULTILINE))
        class_count = len(re.findall(r"^\s*(struct|enum|trait)\s+\w+", content, re.MULTILINE))

    todos = len(re.findall(r"(TODO|FIXME|HACK|XXX|BUG):", content, re.IGNORECASE))

    imports = []
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        imports = re.findall(r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]', content)
    elif ext == ".py":
        imports = re.findall(r"^\s*(?:import|from)\s+(\w+)", content, re.MULTILINE)
    elif ext == ".rs":
        imports = re.findall(r"^\s*use\s+([\w:]+)", content, re.MULTILINE)

    return {
        "path": path,
        "relative": path.relative_to(PROJECT_ROOT),
        "size": size,
        "lines": len(lines),
        "func_count": func_count,
        "class_count": class_count,
        "todos": todos,
        "imports": imports,
    }


def git_file_change_counts(since_commits: int = 20) -> dict[str, int]:
    try:
        log = subprocess.check_output(
            ["git", "log", f"-n{since_commits}", "--name-only", "--pretty=format:"],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except Exception:
        return {}

    counts = {}
    for line in log.splitlines():
        line = line.strip()
        if line and not line.startswith("/"):
            counts[line] = counts.get(line, 0) + 1
    return counts


def find_harness_files() -> set[str]:
    harness_dir = PROJECT_ROOT / "tests" / "harness"
    if not harness_dir.exists():
        return set()
    stems = set()
    for p in harness_dir.rglob("*"):
        if p.is_file() and p.suffix in {".ts", ".py", ".rs", ".go", ".sh"}:
            # Strip language-specific suffixes: test_foo.py -> foo, foo_test.go -> foo,
            # foo.spec.ts -> foo.spec. Keep snake/kebab form for matching.
            stem = p.stem
            stem = re.sub(r"^test_", "", stem)
            stem = re.sub(r"_test$", "", stem)
            stems.add(stem)
    return stems


def find_harness_related_specs() -> set[str]:
    """Collect every 'Related spec:' path declared inside harness files.

    Matches lines like:
        Related spec: docs/feature/login-flow.md
        // Related spec: docs/feature/login-flow.md
        # Related spec: docs/feature/login-flow.md
    Only paths that actually point at docs/feature/*.md are counted, so
    placeholder "[none]" or "[Link to ...]" strings are ignored.
    """
    harness_dir = PROJECT_ROOT / "tests" / "harness"
    if not harness_dir.exists():
        return set()

    related: set[str] = set()
    pattern = re.compile(r"[Rr]elated spec:\s*(\S+\.md)")
    for p in harness_dir.rglob("*"):
        if not p.is_file() or p.suffix not in {".ts", ".py", ".rs", ".go", ".sh"}:
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in pattern.finditer(content):
            ref = match.group(1).strip()
            # Only count real spec paths, not placeholders like "[none]".
            if "docs/feature/" in ref or ref.startswith("feature/"):
                related.add(ref)
    return related


def find_specs_without_harness() -> list[str]:
    spec_dir = PROJECT_ROOT / "docs" / "feature"
    if not spec_dir.exists():
        return []

    related_specs = find_harness_related_specs()
    harness_stems = find_harness_files()
    missing = []
    for spec_file in spec_dir.glob("*.md"):
        spec_rel = spec_file.relative_to(PROJECT_ROOT).as_posix()
        # Primary signal: explicit "Related spec:" reference in any harness.
        if spec_rel in related_specs:
            continue
        # Fallback: stem fuzzy match (legacy behaviour) for harnesses that
        # predate --related-spec.
        spec_stem = spec_file.stem.lower().replace("-", "_")
        has_harness = any(
            spec_stem in h.replace("-", "_") or h.replace("-", "_") in spec_stem
            for h in harness_stems
        )
        if not has_harness:
            missing.append(spec_file.name)
    return missing


def score_harness_candidate(file_info: dict, change_counts: dict, harness_stems: set[str]) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    rel = str(file_info["relative"])
    stem = file_info["path"].stem

    core_patterns = ["auth", "login", "payment", "permission", "security"]
    if any(p in rel.lower() for p in core_patterns):
        score += 3
        reasons.append("core flow")

    changes = change_counts.get(rel, 0)
    if changes >= 5:
        score += 3
        reasons.append(f"changed {changes} times recently")
    elif changes >= 3:
        score += 2
        reasons.append(f"changed {changes} times recently")

    if file_info["lines"] > 300:
        score += 2
        reasons.append("large file")
    if file_info["func_count"] > 8:
        score += 1
        reasons.append("many functions")

    if file_info["todos"] > 0:
        score += 1
        reasons.append("has TODO/FIXME/HACK")

    if stem in harness_stems:
        score -= 5
        reasons.append("already has harness")

    return score, reasons


def cmd_review_architecture(args):
    print("Scanning project architecture...")
    files = scan_source_files(PROJECT_ROOT)
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

    output_path = PROJECT_ROOT / "docs" / "guide" / "architecture-review.md"
    write_file(output_path, "\n".join(lines))
    print(f"Created: {output_path}")
    print("Next: review this file with AI and create ADRs for confirmed decisions.")


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
    files = scan_source_files(PROJECT_ROOT)
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


def main():
    parser = argparse.ArgumentParser(description="AI SDD Bootstrap")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize minimal MVP scaffold")
    init_parser.add_argument("--primary-stack", choices=all_stacks())
    init_parser.add_argument("--additional-stack", action="append", help="Additional stack. Can be repeated or comma-separated.")

    foundation_parser = subparsers.add_parser(
        "bootstrap-foundation",
        help="Bootstrap full docs/ADR/spec/harness framework after MVP validation",
    )
    foundation_parser.add_argument("--primary-stack", choices=all_stacks())
    foundation_parser.add_argument("--additional-stack", action="append", help="Additional stack. Can be repeated or comma-separated.")

    subparsers.add_parser("status", help="Show project status and recommendations")

    adr_parser = subparsers.add_parser("add-adr", help="Add an architecture decision record")
    adr_parser.add_argument("--title")
    adr_parser.add_argument("--background")
    adr_parser.add_argument("--decision")
    adr_parser.add_argument("--consequences")
    adr_parser.add_argument("--status", choices=["proposed", "accepted", "deprecated"])

    spec_parser = subparsers.add_parser("add-spec", help="Add a feature spec")
    spec_parser.add_argument("--title")
    spec_parser.add_argument("--in-scope")
    spec_parser.add_argument("--out-scope")
    spec_parser.add_argument("--boundaries")
    spec_parser.add_argument("--acceptance")
    spec_parser.add_argument("--dependencies")

    harness_parser = subparsers.add_parser("add-harness", help="Add a harness skeleton")
    harness_parser.add_argument("--stack")
    harness_parser.add_argument("--title")
    harness_parser.add_argument("--module")
    harness_parser.add_argument("--purpose")
    harness_parser.add_argument(
        "--related-spec",
        help="Path of the spec this harness locks (e.g. docs/feature/login-flow.md).",
    )

    subparsers.add_parser("review-architecture", help="Generate architecture review doc")
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

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "bootstrap-foundation": cmd_bootstrap_foundation,
        "status": cmd_status,
        "add-adr": cmd_add_adr,
        "add-spec": cmd_add_spec,
        "add-harness": cmd_add_harness,
        "review-architecture": cmd_review_architecture,
        "suggest-harness": cmd_suggest_harness,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
