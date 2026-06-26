import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "ai_sdd_bootstrap.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("ai_sdd_bootstrap", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AiSddBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.module.PROJECT_ROOT = self.root

    def tearDown(self):
        self.tmp.cleanup()

    def _capture(self, func, *args, **kwargs):
        """Run a function while swallowing printed output."""
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
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


if __name__ == "__main__":
    unittest.main()
