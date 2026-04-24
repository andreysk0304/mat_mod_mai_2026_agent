from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from agent.project_paths import PROJECT_ROOT, PROJECT_TOOLS_DIR, resolve_project_path
from agent.tools import ToolRegistry


class ProjectPathTests(unittest.TestCase):
    def test_project_paths_do_not_depend_on_current_working_directory(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)

                registry = ToolRegistry.with_defaults(PROJECT_TOOLS_DIR)
                readme_path = resolve_project_path("README.md")
            finally:
                os.chdir(original_cwd)

        self.assertIn("github_repo_info", registry.names())
        self.assertEqual(readme_path, PROJECT_ROOT / "README.md")

    def test_resolve_project_path_rejects_parent_escape(self) -> None:
        with self.assertRaisesRegex(ValueError, "project directory"):
            resolve_project_path("../outside.txt")


if __name__ == "__main__":
    unittest.main()
