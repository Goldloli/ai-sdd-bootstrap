import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import ai_sdd_bootstrap.cli as ai_sdd_bootstrap_module


def load_module():
    return ai_sdd_bootstrap_module


class AiSddBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.module.PROJECT_ROOT = self.root

    def tearDown(self):
        self.tmp.cleanup()

    def _capture(self, func, *args, **kwargs):
        """Run a function while swallowing printed output and stdin."""
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), patch("sys.stdin", io.StringIO("\n")):
            return func(*args, **kwargs)

    def bootstrap_index(self):
        index_path = self.root / "docs" / "INDEX.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("# Project Documentation Index\n", encoding="utf-8")

    def bootstrap_foundation_files(self):
        """Create a minimal foundation structure so add-adr/add-spec don't warn."""
        (self.root / "docs" / "guide").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "adr").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "feature").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "guide" / "ai-behavior.md").write_text("", encoding="utf-8")
        (self.root / "AI_HANDOFF.md").write_text("", encoding="utf-8")
        (self.root / "CLAUDE.md").write_text("", encoding="utf-8")

    def test_init_creates_minimal_mvp_scaffold(self):
        args = SimpleNamespace(primary_stack="python", additional_stack=None)

        self._capture(self.module.cmd_init, args)

        self.assertTrue((self.root / "README.md").exists())
        self.assertTrue((self.root / "AGENTS.md").exists())
        self.assertTrue((self.root / ".gitignore").exists())
        # Foundation docs should NOT exist yet.
        self.assertFalse((self.root / "docs").exists())
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertFalse((self.root / "AI_HANDOFF.md").exists())

    def test_bootstrap_foundation_creates_full_framework(self):
        # Start from MVP scaffold.
        init_args = SimpleNamespace(primary_stack="nodejs-ts", additional_stack=None)
        self._capture(self.module.cmd_init, init_args)

        foundation_args = SimpleNamespace(
            primary_stack="nodejs-ts",
            additional_stack=["python"],
        )
        self._capture(self.module.cmd_bootstrap_foundation, foundation_args)

        self.assertTrue((self.root / "docs" / "INDEX.md").exists())
        self.assertTrue((self.root / "docs" / "guide" / "ai-behavior.md").exists())
        self.assertTrue((self.root / "docs" / "guide" / "project-meta.md").exists())
        self.assertTrue((self.root / "docs" / "adr").exists())
        self.assertTrue((self.root / "docs" / "feature").exists())
        self.assertTrue((self.root / "CLAUDE.md").exists())
        self.assertTrue((self.root / "AI_HANDOFF.md").exists())
        self.assertTrue((self.root / "AGENTS.md").exists())

        meta = (self.root / "docs" / "guide" / "project-meta.md").read_text(encoding="utf-8")
        self.assertIn("**Stage:** foundation", meta)
        self.assertIn("**Primary stack:** nodejs-ts", meta)
        self.assertIn("**Additional stacks:** python", meta)

    def test_bootstrap_foundation_reuses_existing_additional_stacks(self):
        # Initialize with python + rust.
        init_args = SimpleNamespace(
            primary_stack="python",
            additional_stack=["rust"],
        )
        self._capture(self.module.cmd_init, init_args)

        # Change primary stack, leave additional-stack unset.
        foundation_args = SimpleNamespace(
            primary_stack="nodejs-ts",
            additional_stack=None,
        )
        self._capture(self.module.cmd_bootstrap_foundation, foundation_args)

        meta = (self.root / "docs" / "guide" / "project-meta.md").read_text(encoding="utf-8")
        self.assertIn("**Primary stack:** nodejs-ts", meta)
        self.assertIn("**Additional stacks:** rust", meta)

    def test_add_adr_accepts_args_and_updates_index(self):
        self.bootstrap_index()
        self.bootstrap_foundation_files()
        args = SimpleNamespace(
            title="Use SQLite",
            background="The app needs local persistence.",
            decision="Use SQLite for local data.",
            consequences="Desktop storage is simple but not multi-user.",
            status="accepted",
        )

        self._capture(self.module.cmd_add_adr, args)

        adr_path = self.root / "docs" / "adr" / "ADR-001-use-sqlite.md"
        self.assertTrue(adr_path.exists())
        index = (self.root / "docs" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("ADR-001-use-sqlite.md", index)
        self.assertIn("Use SQLite", index)

    def test_add_spec_accepts_args_and_updates_index(self):
        self.bootstrap_index()
        self.bootstrap_foundation_files()
        args = SimpleNamespace(
            title="Login Flow",
            in_scope="User can log in with email",
            out_scope="Social login",
            boundaries="Do not bypass password verification,Do not mutate user roles",
            acceptance="Reject bad password,Create session for valid user",
            dependencies="ADR-001-auth.md",
        )

        self._capture(self.module.cmd_add_spec, args)

        spec_path = self.root / "docs" / "feature" / "login-flow.md"
        self.assertTrue(spec_path.exists())
        spec = spec_path.read_text(encoding="utf-8")
        self.assertIn("- User can log in with email", spec)
        self.assertIn("- Social login", spec)
        index = (self.root / "docs" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("login-flow.md", index)
        self.assertIn("Login Flow", index)

    def test_python_harness_skeleton_does_not_pass_by_default(self):
        self._capture(
            self.module.add_harness_python,
            "Payment rejection",
            "billing",
            "Reject payment when user has no entitlement.",
        )

        harness = (
            self.root
            / "tests"
            / "harness"
            / "billing"
            / "test_payment_rejection.py"
        ).read_text(encoding="utf-8")
        self.assertIn("Replace this draft harness", harness)
        self.assertNotIn("assert True", harness)

    def test_go_harness_uses_go_test_convention_and_fails_by_default(self):
        self._capture(
            self.module.add_harness_go,
            "Login rejection",
            "auth",
            "Reject login with wrong password.",
        )

        go_file = (
            self.root / "tests" / "harness" / "auth" / "login_rejection_test.go"
        )
        self.assertTrue(go_file.exists())
        content = go_file.read_text(encoding="utf-8")
        # Go test files must end with _test.go to be discovered by `go test`.
        self.assertTrue(go_file.name.endswith("_test.go"))
        # Draft harness must fail until the placeholder is replaced.
        self.assertIn("Replace this draft harness", content)
        self.assertIn("t.Fatalf", content)
        # Exported test function must start with Test and be PascalCase.
        self.assertIn("func TestLoginRejection", content)
        # Package name must match the directory (last segment of module path).
        self.assertIn("package auth", content)

    def test_go_harness_uses_module_name_for_nested_package(self):
        """A module like 'backend/auth' should produce package 'auth'."""
        self._capture(
            self.module.add_harness_go,
            "Login rejection",
            "backend/auth",
            "Reject login with wrong password.",
        )
        go_file = self.root / "tests" / "harness" / "backend" / "auth" / "login_rejection_test.go"
        self.assertTrue(go_file.exists())
        content = go_file.read_text(encoding="utf-8")
        self.assertIn("package auth", content)
        self.assertNotIn("package backend_auth", content)

    def test_suggest_harness_top_n_is_non_interactive(self):
        """--top N must auto-generate harnesses without prompting."""
        # Plant a high-signal source file: name contains "auth" so the core-flow
        # heuristic scores it.
        src = self.root / "src" / "auth_service.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("def login():\n    pass\n" * 10, encoding="utf-8")

        args = SimpleNamespace(top="1", dry_run=False)
        out = io.StringIO()
        # Replace stdin EOF is handled inside prompt(); we just need to ensure
        # no interactive prompt blocks us. With --top set, we never reach prompt().
        with redirect_stdout(out):
            self.module.cmd_suggest_harness(args)

        harnesses = list((self.root / "tests" / "harness").rglob("test_*.py"))
        self.assertEqual(len(harnesses), 1)
        self.assertIn("Auto-generating", out.getvalue())

    def test_suggest_harness_dry_run_does_not_create_files(self):
        """--dry-run must list candidates but not write any harness file."""
        src = self.root / "src" / "payment.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("def charge():\n    pass\n", encoding="utf-8")

        args = SimpleNamespace(top=None, dry_run=True)
        out = io.StringIO()
        with redirect_stdout(out):
            self.module.cmd_suggest_harness(args)

        self.assertFalse((self.root / "tests").exists())
        self.assertIn("Top harness candidates", out.getvalue())

    def test_add_harness_writes_related_spec_into_header(self):
        self._capture(
            self.module.add_harness_python,
            "Login rejection",
            "auth",
            "Reject login with wrong password.",
            "docs/feature/login-flow.md",
        )
        harness = (
            self.root / "tests" / "harness" / "auth" / "test_login_rejection.py"
        ).read_text(encoding="utf-8")
        self.assertIn("docs/feature/login-flow.md", harness)

    def test_add_harness_allows_missing_related_spec(self):
        """A non-existent --related-spec should not stop harness generation."""
        self._capture(
            self.module.add_harness_python,
            "Login rejection",
            "auth",
            "Reject login with wrong password.",
            "docs/feature/missing.md",
        )
        harness = (
            self.root / "tests" / "harness" / "auth" / "test_login_rejection.py"
        )
        self.assertTrue(harness.exists())

    def test_spec_with_explicit_related_harness_is_not_flagged_missing(self):
        """A spec referenced via --related-spec must not appear in the missing list."""
        # Spec file.
        feature_dir = self.root / "docs" / "feature"
        feature_dir.mkdir(parents=True, exist_ok=True)
        spec_path = feature_dir / "login-flow.md"
        spec_path.write_text("# Login Flow\n", encoding="utf-8")

        # Harness that explicitly references it. The stem does NOT match the
        # spec slug, so only the precise "Related spec:" line can link them.
        self._capture(
            self.module.add_harness_python,
            "Bad password guard",
            "auth",
            "Reject login with wrong password.",
            "docs/feature/login-flow.md",
        )

        missing = self.module.find_specs_without_harness()
        self.assertNotIn("login-flow.md", missing)

    def test_evaluation_harness_template_is_generated_and_fails(self):
        self._capture(
            self.module.add_harness_evaluation,
            "Memory recall quality",
            "agent",
            "Evaluate memory recall accuracy across golden cases.",
            "docs/feature/memory-recall.md",
        )
        path = (
            self.root / "tests" / "harness" / "agent" / "test_memory_recall_quality.py"
        )
        self.assertTrue(path.exists())
        content = path.read_text(encoding="utf-8")
        # Draft harness must require user wiring before it can pass.
        self.assertIn("NotImplementedError", content)
        # Evaluation-specific scaffolding must be present.
        self.assertIn("EvalCase", content)
        self.assertIn("PASS_THRESHOLD", content)

    def test_scenario_harness_template_is_generated_and_fails(self):
        self._capture(
            self.module.add_harness_scenario,
            "First launch onboarding",
            "agent",
            "Drive the first-launch scenario end-to-end.",
            "docs/feature/first-launch.md",
        )
        path = (
            self.root / "tests" / "harness" / "agent" / "test_first_launch_onboarding.py"
        )
        self.assertTrue(path.exists())
        content = path.read_text(encoding="utf-8")
        self.assertIn("NotImplementedError", content)
        # Scenario-specific scaffolding must be present.
        self.assertIn("STEPS", content)
        self.assertIn("TRAJECTORY_CHECKS", content)

    def test_add_harness_kind_routes_to_scenario(self):
        """--kind scenario must bypass the per-stack dispatch."""
        args = SimpleNamespace(
            stack="python",
            title="Skin event sequence",
            module="skins",
            purpose="Verify skin event sequence stays valid.",
            related_spec="docs/feature/skins.md",
            kind="scenario",
        )
        self._capture(self.module.cmd_add_harness, args)
        path = (
            self.root / "tests" / "harness" / "skins" / "test_skin_event_sequence.py"
        )
        self.assertTrue(path.exists())


class DryRunTests(unittest.TestCase):
    def setUp(self):
        self.module = ai_sdd_bootstrap_module
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.module.PROJECT_ROOT = self.root
        self._original_dry_run = self.module.is_dry_run()

    def tearDown(self):
        self.module.set_dry_run(self._original_dry_run)
        self.tmp.cleanup()

    def _capture(self, func, *args, **kwargs):
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), patch("sys.stdin", io.StringIO("\n")):
            return func(*args, **kwargs)

    def test_init_dry_run_does_not_create_files(self):
        self.module.set_dry_run(True)
        args = SimpleNamespace(primary_stack="python", additional_stack=None)
        self._capture(self.module.cmd_init, args)
        self.assertFalse((self.root / "README.md").exists())
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_add_adr_dry_run_does_not_write(self):
        self.module.set_dry_run(True)
        index_path = self.root / "docs" / "INDEX.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("# Index\n", encoding="utf-8")
        args = SimpleNamespace(
            title="Use SQLite",
            background="b",
            decision="d",
            consequences="c",
            status="accepted",
        )
        self._capture(self.module.cmd_add_adr, args)
        self.assertFalse((self.root / "docs" / "adr").exists())


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.module = ai_sdd_bootstrap_module
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.module.PROJECT_ROOT = self.root

    def tearDown(self):
        self.tmp.cleanup()

    def _capture(self, func, *args, **kwargs):
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), patch("sys.stdin", io.StringIO("\n")):
            return func(*args, **kwargs)

    def test_validate_reports_broken_link(self):
        index_path = self.root / "docs" / "INDEX.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            "# Index\n\n## Architecture Decisions\n\n- [Missing ADR](./missing-adr.md)\n",
            encoding="utf-8",
        )
        args = SimpleNamespace(json=False)
        with self.assertRaises(SystemExit) as ctx:
            self._capture(self.module.cmd_validate, args)
        self.assertEqual(ctx.exception.code, 1)


class SlugTests(unittest.TestCase):
    def setUp(self):
        self.module = ai_sdd_bootstrap_module

    def test_slugify_ascii_title(self):
        self.assertEqual(self.module.slugify("Login Flow"), "login-flow")

    def test_slugify_cjk_title(self):
        # When pypinyin is installed, CJK should be romanized.
        slug = self.module.slugify("登录流程")
        self.assertNotIn("\u767b\u5f55", slug)  # no raw CJK in filename
        self.assertTrue(slug)  # not empty
        self.assertRegex(slug, r"^[\w-]+$")

    def test_slugify_empty_fallback(self):
        slug = self.module.slugify("——")
        self.assertTrue(slug.startswith("untitled-"))


if __name__ == "__main__":
    unittest.main()
