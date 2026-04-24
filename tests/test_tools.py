from __future__ import annotations

import unittest
from pathlib import Path

from agent.tools import ToolRegistry
from tools.github_repo_info import _parse_repo


class ToolTests(unittest.TestCase):
    def test_registry_loads_submission_tools(self) -> None:
        registry = ToolRegistry.with_defaults(Path("tools"))

        self.assertIn("github_repo_info", registry.names())
        self.assertIn("plan_optimizer", registry.names())

    def test_plan_optimizer_beats_greedy_on_demo_case(self) -> None:
        registry = ToolRegistry.with_defaults(Path("tools"))

        result = registry.execute(
            "plan_optimizer",
            {
                "available_hours": 8,
                "tasks": [
                    {"title": "README", "hours": 1, "value": 3},
                    {"title": "GitHub API tool", "hours": 4, "value": 10},
                    {"title": "optimizer tool", "hours": 4, "value": 10},
                    {"title": "REFLECTION", "hours": 1, "value": 3},
                    {"title": "screencast", "hours": 3, "value": 8},
                    {"title": "polish", "hours": 1, "value": 3},
                    {"title": "tests", "hours": 3, "value": 6},
                ],
            },
        )

        self.assertTrue(result["comparison"]["improved_is_better"])
        self.assertEqual(result["comparison"]["value_gain"], 4.0)

    def test_github_repo_url_parser(self) -> None:
        self.assertEqual(
            _parse_repo("https://github.com/openai/openai-python"),
            ("openai", "openai-python"),
        )
        self.assertEqual(_parse_repo("pallets/flask"), ("pallets", "flask"))


if __name__ == "__main__":
    unittest.main()
