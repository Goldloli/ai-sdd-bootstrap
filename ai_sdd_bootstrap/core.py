#!/usr/bin/env python3
"""Shared utilities, project state, prompts, dry-run/strict globals."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
PROJECT_ROOT = Path.cwd()
_DRY_RUN = False
_STRICT = False


def set_project_root(path) -> None:
    global PROJECT_ROOT
    PROJECT_ROOT = Path(path)


def set_dry_run(value: bool) -> None:
    global _DRY_RUN
    _DRY_RUN = value


def is_dry_run() -> bool:
    return _DRY_RUN


def set_strict(value: bool) -> None:
    global _STRICT
    _STRICT = value


def is_strict() -> bool:
    return _STRICT


def load_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    if _DRY_RUN:
        print(f"[dry-run] Would create: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def report_created(path: Path) -> None:
    if _DRY_RUN:
        return
    print(f"Created: {path}")


def _strict_error(question: str) -> None:
    print(f"Error: missing required input for '{question}' (strict mode refuses interactive prompts).")
    sys.exit(1)


def prompt(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{suffix}: ").strip()
    except EOFError:
        if _STRICT and not default:
            _strict_error(question)
        print(f" (non-interactive, using default: {default!r})")
        return default
    if _STRICT and not answer and not default:
        _strict_error(question)
    return answer if answer else default


def prompt_choice(question: str, choices: list[str], default: str = "") -> str:
    while True:
        options = "/".join(choices)
        suffix = f" [{default}]" if default else ""
        try:
            answer = input(f"{question} ({options}){suffix}: ").strip()
        except EOFError:
            if _STRICT and not default:
                _strict_error(question)
            print(f" (non-interactive, using default: {default!r})")
            return default if default in choices else choices[0]
        if not answer and default:
            return default
        if answer in choices:
            return answer
        if _STRICT:
            print(f"Error: invalid choice '{answer}' in strict mode.")
            sys.exit(1)
        print(f"Please choose one of: {', '.join(choices)}")


def prompt_multi(question: str, choices: list[str], default: list[str] | None = None) -> list[str]:
    print(f"{question} (comma-separated, e.g., {', '.join(choices)})")
    try:
        answer = input("Enter choices or leave empty for none: ").strip()
    except EOFError:
        default = default or []
        if _STRICT:
            _strict_error(question)
        print(f" (non-interactive, using default: {default!r})")
        return default
    if not answer:
        if _STRICT:
            _strict_error(question)
        return default or []
    selected = [s.strip() for s in answer.split(",")]
    valid = [s for s in selected if s in choices]
    invalid = [s for s in selected if s not in choices]
    if invalid:
        if _STRICT:
            print(f"Error: invalid choices in strict mode: {', '.join(invalid)}")
            sys.exit(1)
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

    if is_dry_run():
        print(f"[dry-run] Would update index: {entry}")
        return
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
# Slug / naming helpers
# ---------------------------------------------------------------------------


def _romanize_cjk(title: str) -> str:
    """Romanize CJK characters when pypinyin is installed.

    Falls back to a hash-based slug if pypinyin is missing, so titles that
    would otherwise produce unreadable or empty slugs still produce a safe,
    deterministic filename.
    """
    has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in title)
    if not has_cjk:
        return title
    try:
        from pypinyin import lazy_pinyin
        return "-".join(lazy_pinyin(title))
    except ImportError:
        import hashlib
        print(
            "Warning: CJK title detected but pypinyin is not installed. "
            "Install with: pip install 'ai-sdd-bootstrap[cjk]'. "
            "Using a hash-based slug for now."
        )
        return f"cjk-{hashlib.md5(title.encode('utf-8')).hexdigest()[:8]}"


def slugify(title: str) -> str:
    romanized = _romanize_cjk(title)
    slug = re.sub(r"[^\w]+", "-", romanized).strip("-").lower()
    if not slug:
        import hashlib
        slug = f"untitled-{hashlib.md5(title.encode('utf-8')).hexdigest()[:8]}"
    return slug


def snake_slug(title: str) -> str:
    return slugify(title).replace("-", "_")


def pascal_slug(title: str) -> str:
    """Convert a title to PascalCase for Go exported identifiers."""
    parts = re.split(r"[^\w]+", title)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


# ---------------------------------------------------------------------------
# Foundation directory helpers
# ---------------------------------------------------------------------------


def ensure_foundation_dirs():
    """Create docs dirs if they don't exist (so add-adr/add-spec still work pre-foundation)."""
    if is_dry_run():
        return
    (PROJECT_ROOT / "docs" / "adr").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "docs" / "feature").mkdir(parents=True, exist_ok=True)


def warn_if_pre_foundation(action: str):
    if not is_foundation_bootstrapped():
        print(f"Note: foundation framework not yet bootstrapped. {action} now creates an isolated doc.")
        print("Run 'bootstrap-foundation' when you are ready to build the full SDD scaffold.\n")


def next_adr_number() -> int:
    numbers = []
    adr_dir = PROJECT_ROOT / "docs" / "adr"
    if adr_dir.exists():
        for p in adr_dir.glob("ADR-*.md"):
            m = re.match(r"ADR-(\d+)", p.name)
            if m:
                numbers.append(int(m.group(1)))
    return max(numbers, default=0) + 1


# ---------------------------------------------------------------------------
# Harness counting and status recommendations
# ---------------------------------------------------------------------------


def _count_harnesses() -> int:
    harness_dir = PROJECT_ROOT / "tests" / "harness"
    if not harness_dir.exists():
        return 0
    return sum(
        len(list(harness_dir.rglob(pattern)))
        for pattern in ["*.spec.ts", "test_*.py", "*.rs", "*_test.go", "*.sh"]
    )


def _count_draft_harnesses() -> int:
    harness_dir = PROJECT_ROOT / "tests" / "harness"
    if not harness_dir.exists():
        return 0
    draft_marker = "Replace this draft harness"
    count = 0
    for p in harness_dir.rglob("*"):
        if p.is_file() and p.suffix in {".ts", ".py", ".rs", ".go", ".sh"}:
            try:
                if draft_marker in p.read_text(encoding="utf-8"):
                    count += 1
            except Exception:
                pass
    return count


def _build_status_recommendations(
    initialized: bool,
    foundation: bool,
    stage: str,
    adr_count: int,
    harness_count: int,
    dirty_files: list[str],
) -> list[str]:
    recommendations = []
    if not initialized:
        recommendations.append("Run 'init' to set up the minimal MVP scaffold.")
        return recommendations

    if not foundation:
        recommendations.append("MVP stage: focus on validating ideas. Avoid specs, ADRs, and heavy architecture decisions.")
        recommendations.append("Let AI explore freely. Code quality expectations are low.")
        if dirty_files:
            recommendations.append("Keep iterating. When the MVP feels solid and architecture stabilizes, run 'bootstrap-foundation'.")
        else:
            recommendations.append("No active changes. Good time to experiment or validate the next assumption.")
        return recommendations

    if stage == "foundation":
        recommendations.append("Foundation stage: modularize MVP architecture and lock key decisions into ADRs.")
        recommendations.append("Run 'review-architecture' to audit the current structure.")
        if adr_count == 0:
            recommendations.append("No ADRs yet. Start recording framework, data model, and module boundary decisions.")
    else:
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

    return recommendations


def print_recommendations(recommendations: list[str]):
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")


# ---------------------------------------------------------------------------
# File scanning / index helpers
# ---------------------------------------------------------------------------

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


def _parse_index_links(index_path: Path) -> list[tuple[str, str]]:
    """Return (link_text, relative_link) tuples from docs/INDEX.md."""
    if not index_path.exists():
        return []
    content = index_path.read_text(encoding="utf-8")
    links = []
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
        link = match.group(2)
        if link.startswith("http://") or link.startswith("https://"):
            continue
        links.append((match.group(1), link))
    return links


__all__ = [
    "SCRIPT_DIR",
    "TEMPLATES_DIR",
    "PROJECT_ROOT",
    "set_project_root",
    "set_dry_run",
    "is_dry_run",
    "set_strict",
    "is_strict",
    "load_template",
    "write_file",
    "report_created",
    "prompt",
    "prompt_choice",
    "prompt_multi",
    "all_stacks",
    "arg_value",
    "arg_list",
    "prompt_or_arg",
    "prompt_choice_or_arg",
    "prompt_multi_or_arg",
    "split_items",
    "update_index_entry",
    "is_minimally_initialized",
    "is_foundation_bootstrapped",
    "read_stage",
    "read_stack_info",
    "git_info",
    "slugify",
    "snake_slug",
    "pascal_slug",
    "ensure_foundation_dirs",
    "warn_if_pre_foundation",
    "next_adr_number",
    "_count_harnesses",
    "_count_draft_harnesses",
    "_build_status_recommendations",
    "print_recommendations",
    "should_ignore_path",
    "scan_source_files",
    "analyze_file",
    "git_file_change_counts",
    "find_harness_files",
    "find_harness_related_specs",
    "find_specs_without_harness",
    "score_harness_candidate",
    "_parse_index_links",
]
